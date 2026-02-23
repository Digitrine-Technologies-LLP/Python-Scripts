import os

def build_tree(path=".", prefix="", ignore=None):
    if ignore is None:
        ignore = {".git", "__pycache__", ".DS_Store", "node_modules", ".venv"}
    
    lines = []
    entries = sorted(
        [e for e in os.scandir(path) if e.name not in ignore],
        key=lambda e: (e.is_file(), e.name)
    )
    
    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        lines.append(prefix + connector + entry.name)
        if entry.is_dir():
            extension = "    " if i == len(entries) - 1 else "│   "
            lines.extend(build_tree(entry.path, prefix + extension, ignore))
    
    return lines

def update_readme(tree_lines, readme_path="README.md"):
    marker_start = "<!-- TREE_START -->"
    marker_end = "<!-- TREE_END -->"
    tree_block = f"{marker_start}\n```\n" + "\n".join(tree_lines) + f"\n```\n{marker_end}"

    # Read existing README or start fresh
    if os.path.exists(readme_path):
        with open(readme_path, "r") as f:
            content = f.read()
        
        # Replace existing tree block if present
        if marker_start in content and marker_end in content:
            start = content.index(marker_start)
            end = content.index(marker_end) + len(marker_end)
            content = content[:start] + tree_block + content[end:]
        else:
            content += f"\n\n## Project Structure\n\n{tree_block}\n"
    else:
        content = f"## Project Structure\n\n{tree_block}\n"

    with open(readme_path, "w") as f:
        f.write(content)
    
    print(f"README.md updated with project tree.")

tree_lines = build_tree()
update_readme(tree_lines)
