#!/usr/bin/env python3
"""
Site Link Crawler
Crawls all links on a website and reports their HTTP status codes.
Uses a headless Chromium browser (Playwright) to handle JS-rendered pages.
Outputs results to a .csv file and optionally prints a summary.

Usage:
    python site_crawler.py https://example.com
    python site_crawler.py https://example.com --output results.csv --max-pages 100
"""

import argparse
import csv
import random
import time
from collections import Counter, deque
from datetime import datetime
from urllib.parse import urljoin, urlparse

try:
    from bs4 import BeautifulSoup
    from playwright.sync_api import sync_playwright
except ImportError:
    print("⚠️  Missing dependencies. Install with:\n"
          "    pip install beautifulsoup4 playwright\n"
          "    playwright install chromium\n")
    raise SystemExit(1)

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_TIMEOUT = 30          # seconds per page load
DEFAULT_DELAY   = 1.0         # seconds between requests (be polite)
DEFAULT_MAX     = 200         # maximum pages to crawl
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

SPECIFIC_LABELS = {
    400: "❌ 400 Bad Request",
    401: "🔒 401 Unauthorized",
    403: "🚫 403 Forbidden (bot-blocked?)",
    404: "❌ 404 Not Found",
    405: "❌ 405 Method Not Allowed",
    410: "❌ 410 Gone",
    429: "⏳ 429 Rate Limited",
    500: "⚠️  500 Server Error",
    502: "⚠️  502 Bad Gateway",
    503: "⚠️  503 Service Unavailable",
}

STATUS_LABELS = {
    2: "✅ OK",
    3: "↪️  Redirect",
    4: "❌ Client Error",
    5: "⚠️  Server Error",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def normalise(url: str) -> str:
    """Strip fragment so #anchors don't create duplicate entries."""
    parsed = urlparse(url)
    return parsed._replace(fragment="").geturl()


def same_domain(url: str, base: str) -> bool:
    def root(u: str) -> str:
        return urlparse(u).netloc.removeprefix("www.")
    return root(url) == root(base)


def status_label(code: int) -> str:
    if code in SPECIFIC_LABELS:
        return SPECIFIC_LABELS[code]
    return STATUS_LABELS.get(code // 100, "❓ Unknown")


def get_links(html: str, page_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        full = normalise(urljoin(page_url, href))
        links.append(full)
    return links


# ── Crawler ───────────────────────────────────────────────────────────────────

def crawl(start_url: str, max_pages: int, delay: float, timeout: int,
          include_external: bool, verbose: bool = False) -> list[dict]:
    """
    BFS crawl starting from start_url using a headless Chromium browser.
    Returns a list of result dicts with keys: url, status_code, label, source.
    """
    start_url = normalise(start_url)
    queue     = deque([(start_url, "")])   # (url, source)
    visited   = {start_url}
    results   = []

    print(f"\n🔍 Crawling: {start_url}")
    print(f"   Max pages : {max_pages}")
    print(f"   Delay     : {delay}s\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        page    = context.new_page()

        while queue and len(results) < max_pages:
            url, source = queue.popleft()
            final_url   = url
            code        = 0
            html        = ""

            # ── Request ──────────────────────────────────────────────────────
            for attempt in range(3):
                try:
                    resp = page.goto(url, timeout=timeout * 1000,
                                     wait_until="domcontentloaded")
                    code = resp.status if resp else 0
                    final_url = page.url
                    # Let JS render links
                    try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        pass
                    html = page.content()
                    break
                except Exception as exc:
                    if attempt == 2:
                        print(f"  ⚡ ERROR    {url}  ({exc})")

            label = status_label(code) if code else "⏱  Timeout/Error"
            results.append({"url": url, "status_code": code, "label": label, "source": source})
            print(f"  [{code:>3}] {label}  {url}")

            # ── Discover links ───────────────────────────────────────────────
            if verbose:
                print(f"       final_url  : {final_url}")
                print(f"       html found : {bool(html)}")
                print(f"       same_domain: {same_domain(final_url, start_url)}")

            if html and same_domain(final_url, start_url):
                all_links = get_links(html, final_url)
                if verbose:
                    print(f"       links found: {len(all_links)}")
                for link in all_links:
                    if link in visited:
                        if verbose:
                            print(f"         SKIP (visited): {link}")
                        continue
                    if not include_external and not same_domain(link, start_url):
                        if verbose:
                            print(f"         SKIP (external): {link}")
                        continue
                    if verbose:
                        print(f"         QUEUE: {link}")
                    visited.add(link)
                    queue.append((link, final_url))

            jitter = delay + random.uniform(0, 0.5)
            time.sleep(jitter)

        browser.close()

    print(f"\n✔  Done — {len(results)} URL(s) checked.\n")
    return results


# ── Output ────────────────────────────────────────────────────────────────────

def save_csv(results: list[dict], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "status_code", "label", "source"])
        writer.writeheader()
        writer.writerows(results)
    print(f"📄 CSV saved  → {path}")


def print_summary(results: list[dict]) -> None:
    counts = Counter(r["status_code"] // 100 if r["status_code"] else 0
                     for r in results)
    print("── Summary ──────────────────────────────────")
    for group, label in sorted(STATUS_LABELS.items()):
        n = counts.get(group, 0)
        if n:
            print(f"  {label}: {n}")
    errors = counts.get(0, 0)
    if errors:
        print(f"  ⏱  Timeout/Error: {errors}")
    print(f"  Total: {len(results)}")
    print("─────────────────────────────────────────────\n")

    broken = [r for r in results if r["status_code"] in (0, 404, 410) or
              (r["status_code"] >= 500)]
    if broken:
        print("🚨 Broken / Error URLs:")
        for r in broken:
            print(f"   [{r['status_code']}] {r['url']}")
        print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl a site and report link status codes.")
    parser.add_argument("url",                   help="Starting URL (e.g. https://example.com)")
    parser.add_argument("--output",  "-o",       default="",
                        help="Output CSV filename (default: site_<domain>_<date>.csv)")
    parser.add_argument("--max-pages", "-m",     type=int, default=DEFAULT_MAX,
                        help=f"Maximum pages to crawl (default: {DEFAULT_MAX})")
    parser.add_argument("--delay",   "-d",       type=float, default=DEFAULT_DELAY,
                        help=f"Delay between requests in seconds (default: {DEFAULT_DELAY})")
    parser.add_argument("--timeout", "-t",       type=int, default=DEFAULT_TIMEOUT,
                        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--external", action="store_true",
                        help="Also check external links (not crawled, just checked)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print debug info for each page (links found, skip reasons)")
    args = parser.parse_args()

    if not args.output:
        domain = urlparse(args.url).netloc.replace(".", "_")
        date   = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"site_{domain}_{date}.csv"

    results = crawl(
        start_url       = args.url,
        max_pages       = args.max_pages,
        delay           = args.delay,
        timeout         = args.timeout,
        include_external= args.external,
        verbose         = args.verbose,
    )

    save_csv(results, args.output)
    print_summary(results)


if __name__ == "__main__":
    main()
