#!/usr/bin/env python3
"""
Image Folder Comparator
Compares image files in two folders by filename & metadata,
then generates a polished HTML report.

Usage:
    python image_folder_compare.py <folder_a> <folder_b> [--output report.html]

Requirements:
    pip install Pillow
"""

import os
import sys
import argparse
import hashlib
from pathlib import Path
from datetime import datetime

# Try to import Pillow for metadata extraction
try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    print("⚠️  Pillow not found. Install it for image metadata: pip install Pillow")
    print("   Continuing with filename & file-size comparison only.\n")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif", ".svg", ".ico"}


def file_hash(path: Path, chunk=65536) -> str:
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            while chunk_data := f.read(chunk):
                h.update(chunk_data)
        return h.hexdigest()
    except Exception:
        return "error"


def human_size(num_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def get_image_meta(path: Path) -> dict:
    meta = {
        "size_bytes": path.stat().st_size,
        "size_human": human_size(path.stat().st_size),
        "modified": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        "width": "—",
        "height": "—",
        "mode": "—",
        "format": path.suffix.upper().lstrip("."),
    }
    if HAS_PILLOW and path.suffix.lower() in IMAGE_EXTENSIONS - {".svg"}:
        try:
            with Image.open(path) as img:
                meta["width"] = img.width
                meta["height"] = img.height
                meta["mode"] = img.mode
                meta["format"] = img.format or meta["format"]
        except Exception:
            pass
    return meta


def get_images(folder: str) -> dict:
    """Returns {relative_path_str: absolute_Path}"""
    p = Path(folder)
    return {
        str(f.relative_to(p)): f
        for f in p.rglob("*")
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    }


def compare(folder_a: str, folder_b: str):
    a_files = get_images(folder_a)
    b_files = get_images(folder_b)

    keys_a = set(a_files)
    keys_b = set(b_files)

    only_a = sorted(keys_a - keys_b)
    only_b = sorted(keys_b - keys_a)
    common = sorted(keys_a & keys_b)

    identical, different = [], []
    for rel in common:
        ha = file_hash(a_files[rel])
        hb = file_hash(b_files[rel])
        meta_a = get_image_meta(a_files[rel])
        meta_b = get_image_meta(b_files[rel])
        entry = {"name": rel, "meta_a": meta_a, "meta_b": meta_b, "hash_a": ha, "hash_b": hb}
        if ha == hb:
            identical.append(entry)
        else:
            different.append(entry)

    only_a_data = [{"name": r, "meta": get_image_meta(a_files[r])} for r in only_a]
    only_b_data = [{"name": r, "meta": get_image_meta(b_files[r])} for r in only_b]

    return {
        "folder_a": folder_a,
        "folder_b": folder_b,
        "only_a": only_a_data,
        "only_b": only_b_data,
        "identical": identical,
        "different": different,
    }


def diff_badges(ma, mb):
    """Return HTML badges for fields that differ between meta_a and meta_b."""
    badges = []
    checks = [("size_bytes", "Size"), ("width", "Width"), ("height", "Height"), ("mode", "Color Mode"), ("format", "Format")]
    for key, label in checks:
        if ma.get(key) != mb.get(key):
            badges.append(f'<span class="badge">{label}</span>')
    return "".join(badges) if badges else '<span class="badge same">content differs</span>'


def render_html(data: dict) -> str:
    fa = data["folder_a"]
    fb = data["folder_b"]
    total = len(data["only_a"]) + len(data["only_b"]) + len(data["identical"]) + len(data["different"])
    now = datetime.now().strftime("%B %d, %Y at %H:%M")

    def meta_row(label, va, vb, highlight=False):
        cls = ' class="changed"' if highlight and va != vb else ""
        return f"<tr{cls}><td class='label'>{label}</td><td>{va}</td><td>{vb}</td></tr>"

    def only_table(items, folder_label):
        if not items:
            return "<p class='empty'>None</p>"
        rows = ""
        for item in items:
            m = item["meta"]
            rows += f"""
            <div class="file-card solo">
              <div class="file-name">📄 {item['name']}</div>
              <table class="meta-table solo-meta">
                <tr><td class='label'>Size</td><td>{m['size_human']}</td></tr>
                <tr><td class='label'>Modified</td><td>{m['modified']}</td></tr>
                <tr><td class='label'>Format</td><td>{m['format']}</td></tr>
                {"<tr><td class='label'>Dimensions</td><td>" + str(m['width']) + " × " + str(m['height']) + "</td></tr>" if m['width'] != '—' else ""}
              </table>
            </div>"""
        return rows

    def diff_table(items):
        if not items:
            return "<p class='empty'>None</p>"
        rows = ""
        for item in items:
            ma, mb = item["meta_a"], item["meta_b"]
            rows += f"""
            <div class="file-card diff">
              <div class="file-header">
                <span class="file-name">🖼 {item['name']}</span>
                <div class="diff-badges">{diff_badges(ma, mb)}</div>
              </div>
              <table class="meta-table">
                <thead><tr><th>Property</th><th>Folder A</th><th>Folder B</th></tr></thead>
                <tbody>
                  {meta_row("Size", ma['size_human'], mb['size_human'], True)}
                  {meta_row("Modified", ma['modified'], mb['modified'], True)}
                  {meta_row("Format", ma['format'], mb['format'], True)}
                  {meta_row("Dimensions", f"{ma['width']} × {ma['height']}", f"{mb['width']} × {mb['height']}", True) if ma['width'] != '—' else ""}
                  {meta_row("Color Mode", ma['mode'], mb['mode'], True) if ma['mode'] != '—' else ""}
                </tbody>
              </table>
            </div>"""
        return rows

    identical_list = ""
    if data["identical"]:
        identical_list = "<ul class='identical-list'>" + "".join(
            f"<li>✓ {i['name']} <span class='dim'>({i['meta_a']['size_human']})</span></li>"
            for i in data["identical"]
        ) + "</ul>"
    else:
        identical_list = "<p class='empty'>None</p>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Image Folder Comparison Report</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;1,9..144,300&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0e0f11;
    --surface: #16181c;
    --surface2: #1e2128;
    --border: #2a2d35;
    --accent-a: #f0c04a;
    --accent-b: #5b9cf6;
    --danger: #ff6b6b;
    --success: #4ecb8d;
    --text: #e2e4ea;
    --dim: #6b7080;
    --changed: rgba(255,107,107,0.08);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'DM Mono', monospace;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 0;
  }}

  /* Header */
  header {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 2.5rem 3rem 2rem;
    position: relative;
    overflow: hidden;
  }}
  header::before {{
    content: '';
    position: absolute;
    top: -60px; left: -60px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(240,192,74,0.08) 0%, transparent 70%);
    pointer-events: none;
  }}
  .report-label {{
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--dim);
    margin-bottom: 0.5rem;
  }}
  h1 {{
    font-family: 'Fraunces', serif;
    font-size: 2rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 1.2rem;
  }}
  .folders {{
    display: flex;
    gap: 1rem;
    align-items: center;
    font-size: 0.8rem;
    flex-wrap: wrap;
  }}
  .folder-pill {{
    background: var(--surface2);
    border: 1px solid var(--border);
    padding: 0.4rem 0.9rem;
    border-radius: 4px;
    max-width: 320px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  .folder-pill.a {{ border-left: 3px solid var(--accent-a); }}
  .folder-pill.b {{ border-left: 3px solid var(--accent-b); }}
  .vs {{ color: var(--dim); font-style: italic; }}
  .generated {{ font-size: 0.72rem; color: var(--dim); margin-top: 1rem; }}

  /* Stats bar */
  .stats-bar {{
    display: flex;
    gap: 0;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
  }}
  .stat {{
    flex: 1;
    padding: 1.2rem 1.5rem;
    border-right: 1px solid var(--border);
    text-align: center;
    transition: background 0.2s;
  }}
  .stat:last-child {{ border-right: none; }}
  .stat:hover {{ background: var(--surface2); }}
  .stat-num {{
    font-family: 'Fraunces', serif;
    font-size: 2rem;
    font-weight: 300;
    line-height: 1;
    margin-bottom: 0.3rem;
  }}
  .stat-label {{ font-size: 0.68rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--dim); }}
  .stat.only-a .stat-num {{ color: var(--accent-a); }}
  .stat.only-b .stat-num {{ color: var(--accent-b); }}
  .stat.modified .stat-num {{ color: var(--danger); }}
  .stat.identical .stat-num {{ color: var(--success); }}
  .stat.total .stat-num {{ color: var(--text); }}

  /* Main content */
  main {{ padding: 2rem 3rem 4rem; max-width: 1100px; margin: 0 auto; }}

  /* Sections */
  section {{ margin-bottom: 3rem; }}
  .section-title {{
    font-family: 'Fraunces', serif;
    font-size: 1.1rem;
    font-weight: 300;
    font-style: italic;
    margin-bottom: 1.2rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 0.7rem;
  }}
  .section-title .count {{
    font-family: 'DM Mono', monospace;
    font-style: normal;
    font-size: 0.75rem;
    background: var(--surface2);
    border: 1px solid var(--border);
    padding: 0.15rem 0.5rem;
    border-radius: 20px;
    color: var(--dim);
  }}

  /* File cards */
  .file-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
  }}
  .file-card:hover {{ border-color: #3a3d48; }}
  .file-card.diff {{ border-left: 3px solid var(--danger); }}
  .file-card.solo.only-a {{ border-left: 3px solid var(--accent-a); }}
  .file-card.solo.only-b {{ border-left: 3px solid var(--accent-b); }}

  .file-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.8rem;
    gap: 1rem;
    flex-wrap: wrap;
  }}
  .file-name {{ font-size: 0.85rem; word-break: break-all; }}
  .diff-badges {{ display: flex; gap: 0.4rem; flex-wrap: wrap; }}
  .badge {{
    font-size: 0.65rem;
    padding: 0.2rem 0.55rem;
    background: rgba(255,107,107,0.15);
    border: 1px solid rgba(255,107,107,0.3);
    color: #ff9999;
    border-radius: 3px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .badge.same {{
    background: rgba(78,203,141,0.1);
    border-color: rgba(78,203,141,0.25);
    color: #7ddcaa;
  }}

  /* Meta tables */
  .meta-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.78rem;
  }}
  .meta-table th {{
    text-align: left;
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--dim);
    padding: 0.4rem 0.6rem;
    border-bottom: 1px solid var(--border);
  }}
  .meta-table td {{
    padding: 0.35rem 0.6rem;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    vertical-align: top;
  }}
  .meta-table td.label {{
    color: var(--dim);
    font-size: 0.72rem;
    width: 120px;
  }}
  .meta-table tr.changed td {{ background: var(--changed); }}
  .meta-table tr.changed td:first-child {{ background: transparent; }}
  .solo-meta td {{ padding: 0.3rem 0.4rem; }}

  /* Identical list */
  .identical-list {{
    list-style: none;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 0.4rem;
  }}
  .identical-list li {{
    font-size: 0.78rem;
    padding: 0.5rem 0.8rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    border-left: 3px solid var(--success);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .identical-list li .dim {{ color: var(--dim); margin-left: 0.4rem; }}

  .empty {{ color: var(--dim); font-size: 0.82rem; font-style: italic; }}
  .dim {{ color: var(--dim); }}

  /* Folder label badges */
  .folder-a-label {{ color: var(--accent-a); }}
  .folder-b-label {{ color: var(--accent-b); }}

  @media (max-width: 700px) {{
    header, main {{ padding: 1.5rem; }}
    .stats-bar {{ flex-wrap: wrap; }}
    .stat {{ min-width: 50%; border-bottom: 1px solid var(--border); }}
  }}
</style>
</head>
<body>

<header>
  <div class="report-label">Image Comparison Report</div>
  <h1>Folder Diff</h1>
  <div class="folders">
    <span class="folder-pill a"><span class="folder-a-label">A</span> &nbsp;{fa}</span>
    <span class="vs">vs</span>
    <span class="folder-pill b"><span class="folder-b-label">B</span> &nbsp;{fb}</span>
  </div>
  <div class="generated">Generated {now} &nbsp;·&nbsp; {total} image(s) scanned</div>
</header>

<div class="stats-bar">
  <div class="stat only-a">
    <div class="stat-num">{len(data['only_a'])}</div>
    <div class="stat-label">Only in A</div>
  </div>
  <div class="stat only-b">
    <div class="stat-num">{len(data['only_b'])}</div>
    <div class="stat-label">Only in B</div>
  </div>
  <div class="stat modified">
    <div class="stat-num">{len(data['different'])}</div>
    <div class="stat-label">Modified</div>
  </div>
  <div class="stat identical">
    <div class="stat-num">{len(data['identical'])}</div>
    <div class="stat-label">Identical</div>
  </div>
  <div class="stat total">
    <div class="stat-num">{total}</div>
    <div class="stat-label">Total</div>
  </div>
</div>

<main>

  <section>
    <div class="section-title">
      ⚠️ Modified Files
      <span class="count">{len(data['different'])}</span>
    </div>
    {diff_table(data['different'])}
  </section>

  <section>
    <div class="section-title">
      <span class="folder-a-label">A</span>&nbsp; Only in Folder A
      <span class="count">{len(data['only_a'])}</span>
    </div>
    {"".join(f'<div class="file-card solo only-a"><div class="file-name">📄 {i["name"]}</div><table class="meta-table solo-meta"><tr><td class="label">Size</td><td>{i["meta"]["size_human"]}</td></tr><tr><td class="label">Modified</td><td>{i["meta"]["modified"]}</td></tr><tr><td class="label">Format</td><td>{i["meta"]["format"]}</td></tr>{"<tr><td class=label>Dimensions</td><td>" + str(i["meta"]["width"]) + " × " + str(i["meta"]["height"]) + "</td></tr>" if i["meta"]["width"] != "—" else ""}</table></div>' for i in data['only_a']) or "<p class='empty'>None</p>"}
  </section>

  <section>
    <div class="section-title">
      <span class="folder-b-label">B</span>&nbsp; Only in Folder B
      <span class="count">{len(data['only_b'])}</span>
    </div>
    {"".join(f'<div class="file-card solo only-b"><div class="file-name">📄 {i["name"]}</div><table class="meta-table solo-meta"><tr><td class="label">Size</td><td>{i["meta"]["size_human"]}</td></tr><tr><td class="label">Modified</td><td>{i["meta"]["modified"]}</td></tr><tr><td class="label">Format</td><td>{i["meta"]["format"]}</td></tr>{"<tr><td class=label>Dimensions</td><td>" + str(i["meta"]["width"]) + " × " + str(i["meta"]["height"]) + "</td></tr>" if i["meta"]["width"] != "—" else ""}</table></div>' for i in data['only_b']) or "<p class='empty'>None</p>"}
  </section>

  <section>
    <div class="section-title">
      ✓ Identical Files
      <span class="count">{len(data['identical'])}</span>
    </div>
    {identical_list}
  </section>

</main>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Compare image folders and generate an HTML report.")
    parser.add_argument("folder_a", help="Path to Folder A")
    parser.add_argument("folder_b", help="Path to Folder B")
    parser.add_argument("--output", "-o", default="image_comparison_report.html", help="Output HTML file (default: image_comparison_report.html)")
    args = parser.parse_args()

    print(f"🔍 Scanning folders...")
    data = compare(args.folder_a, args.folder_b)

    total = len(data["only_a"]) + len(data["only_b"]) + len(data["identical"]) + len(data["different"])
    print(f"   {total} image(s) found")
    print(f"   Only in A : {len(data['only_a'])}")
    print(f"   Only in B : {len(data['only_b'])}")
    print(f"   Identical : {len(data['identical'])}")
    print(f"   Modified  : {len(data['different'])}")

    html = render_html(data)
    out = Path(args.output)
    out.write_text(html, encoding="utf-8")
    print(f"\n✅ Report saved to: {out.resolve()}")


if __name__ == "__main__":
    main()