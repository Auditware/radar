import re
from pathlib import Path
from collections import defaultdict

def main():
    templates_dir = Path("/api/builtin_templates")
    templates = []

    for template_file in sorted(templates_dir.glob("*.yaml")):
        try:
            with open(template_file, 'r') as f:
                content = f.read()
                
                # Simple regex parsing for YAML fields
                name = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
                author = re.search(r'^author:\s*(.+)$', content, re.MULTILINE)
                accent = re.search(r'^accent:\s*(.+)$', content, re.MULTILINE)
                severity = re.search(r'^severity:\s*(.+)$', content, re.MULTILINE)
                
                templates.append({
                    'name': name.group(1).strip() if name else 'Unknown',
                    'author': author.group(1).strip() if author else 'Unknown',
                    'accent': accent.group(1).strip() if accent else 'Unknown',
                    'severity': severity.group(1).strip() if severity else 'Unknown',
                    'file': template_file.name
                })
        except Exception as e:
            continue

    # Summary stats
    COL_WIDTH = 30
    SEPARATOR_WIDTH = 80
    
    print("[i] Showing radar template information\n")

    by_accent = defaultdict(int)
    by_author = defaultdict(int)
    by_severity = defaultdict(int)

    for t in templates:
        by_accent[t['accent']] += 1
        by_author[t['author']] += 1
        by_severity[t['severity']] += 1

    # Three columns for summaries
    print(f"{'ACCENT':<{COL_WIDTH}} {'CONTRIBUTOR':<{COL_WIDTH}} {'SEVERITY':<{COL_WIDTH}}")
    print("=" * SEPARATOR_WIDTH)

    accent_items = sorted(by_accent.items())
    author_items = sorted(by_author.items())
    severity_order = ['Critical', 'High', 'Medium', 'Low', 'Informational', 'Unknown']
    severity_items = [(s, by_severity[s]) for s in severity_order if s in by_severity]

    max_rows = max(len(accent_items), len(author_items), len(severity_items))

    for i in range(max_rows):
        accent_str = f"{accent_items[i][0]}: {accent_items[i][1]}" if i < len(accent_items) else ""
        author_str = f"{author_items[i][0]}: {author_items[i][1]}" if i < len(author_items) else ""
        severity_str = f"{severity_items[i][0]}: {severity_items[i][1]}" if i < len(severity_items) else ""
        print(f"{accent_str:<{COL_WIDTH}} {author_str:<{COL_WIDTH}} {severity_str:<{COL_WIDTH}}")

    # Total templates
    print(f"\n[i] Total: {len(templates)} templates (run `radar update` to get latest templates)\n")

if __name__ == "__main__":
    main()
