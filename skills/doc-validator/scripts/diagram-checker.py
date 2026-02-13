#!/usr/bin/env python3
"""
diagram-checker.py — Verifies Mermaid diagrams in Project_Documentation.md.

Checks:
  - Minimum 6 diagrams present
  - Required types: flowchart, mindmap, sequenceDiagram
  - Forbidden types: C4Context, C4Container, C4Deployment, C4Component
  - Each diagram has an italic caption: *Fig N: Description*

Usage:
    python3 diagram-checker.py /path/to/Project_Documentation.md
"""

import re
import sys


MIN_DIAGRAMS = 6

REQUIRED_TYPES = {'flowchart', 'mindmap', 'sequenceDiagram'}

FORBIDDEN_TYPES = {'C4Context', 'C4Container', 'C4Deployment', 'C4Component'}


def extract_diagrams(content):
    """Extract all Mermaid code blocks with their positions."""
    pattern = re.compile(r'```mermaid\s*\n(.*?)```', re.DOTALL)
    diagrams = []
    for match in pattern.finditer(content):
        block = match.group(1).strip()
        start_pos = match.start()
        first_line = block.split('\n')[0].strip()
        diagram_type = first_line.split()[0] if first_line else 'unknown'
        diagrams.append({
            'type': diagram_type,
            'content': block,
            'position': start_pos,
        })
    return diagrams


def check_captions(content, diagrams):
    """Check each diagram has an italic caption below it."""
    caption_pattern = re.compile(r'\*Fig\s+\d+\s*:\s*.+\*')
    issues = []

    for i, diag in enumerate(diagrams, 1):
        end_pos = content.find('```', diag['position'] + 10)
        if end_pos == -1:
            continue
        after_block = content[end_pos + 3:end_pos + 200]

        if not caption_pattern.search(after_block):
            issues.append(f"Diagram {i} ({diag['type']}): missing italic caption '*Fig N: ...*'")

    return issues


def validate(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"FAIL: File not found: {filepath}")
        return False

    diagrams = extract_diagrams(content)
    print(f"Diagrams found: {len(diagrams)}")

    ok = True

    types_found = set()
    for i, d in enumerate(diagrams, 1):
        print(f"  {i}. {d['type']}")
        types_found.add(d['type'])

    print()

    if len(diagrams) < MIN_DIAGRAMS:
        print(f"FAIL: Need at least {MIN_DIAGRAMS} diagrams, found {len(diagrams)}")
        ok = False
    else:
        print(f"OK: Diagram count ({len(diagrams)} >= {MIN_DIAGRAMS})")

    missing_types = REQUIRED_TYPES - types_found
    if missing_types:
        print(f"FAIL: Missing required diagram types: {', '.join(missing_types)}")
        ok = False
    else:
        print(f"OK: All required types present ({', '.join(REQUIRED_TYPES)})")

    forbidden_found = FORBIDDEN_TYPES & types_found
    if forbidden_found:
        print(f"FAIL: Forbidden diagram types used: {', '.join(forbidden_found)}")
        ok = False
    else:
        print("OK: No forbidden diagram types")

    caption_issues = check_captions(content, diagrams)
    if caption_issues:
        for issue in caption_issues:
            print(f"WARN: {issue}")
    else:
        print("OK: All diagrams have italic captions")

    print()
    if ok and not caption_issues:
        print("PASS: All diagram checks passed")
    elif ok:
        print("WARN: Diagram structure OK but caption issues found")
    else:
        print("FAIL: Diagram validation failed")
        return False

    return True


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-markdown>")
        sys.exit(1)
    success = validate(sys.argv[1])
    sys.exit(0 if success else 1)
