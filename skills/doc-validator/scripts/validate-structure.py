#!/usr/bin/env python3#!/usr/bin/env python3























































































    sys.exit(0 if success else 1)    success = validate(sys.argv[1])        sys.exit(1)        print(f"Usage: {sys.argv[0]} <path-to-markdown>")    if len(sys.argv) != 2:if __name__ == '__main__':        return True        print("\nPASS: All required sections present")    else:        return False        print(f"\nFAIL: {len(missing)} required section(s) missing")    if missing:            print("WARN: Sections are out of expected order")        if actual_order != expected_order:        expected_order = [s for s in req_order if s in found_normalized]        actual_order = [s for s in found_normalized if s in req_order]        req_order = [normalize(r) for r in REQUIRED_SECTIONS]    if found_sections:        print(f"  MISSING  {s}")    for s in missing:        print(f"  OK  {s}")    for s in present:    print(f"Sections found: {len(present)}/{len(REQUIRED_SECTIONS)}")            missing.append(req)        else:            present.append(req)        if req_norm in found_normalized:        req_norm = normalize(req)    for req in REQUIRED_SECTIONS:    present = []    missing = []        print("WARN: Document missing H1 title")    if not has_title:    has_title = bool(re.match(r'^#\s+', content))    found_normalized = [normalize(s) for s in found_sections]    found_sections = extract_h2_sections(content)        return False        print(f"FAIL: File not found: {filepath}")    except FileNotFoundError:            content = f.read()        with open(filepath, 'r', encoding='utf-8') as f:    try:def validate(filepath):    return re.sub(r'[^a-z0-9]', '', title.lower())    """Normalize section title for comparison."""def normalize(title):    return [m.group(1).strip() for m in pattern.finditer(content)]    pattern = re.compile(r'^##\s+\d*\.?\s*(.+)$', re.MULTILINE)    """Extract all ## headings from the document."""def extract_h2_sections(content):]    "Assumptions & Constraints",    "Monitoring & Operations",    "Infrastructure & Deployment",    "API Specification",    "Data Model & Flow",    "System Architecture",    "Solution Overview",    "References",REQUIRED_SECTIONS = [import sysimport re"""    python3 validate-structure.py /path/to/Project_Documentation.mdUsage:contains all 8 mandatory sections in the correct order.validate-structure.py — Checks that Project_Documentation.md""""""
validate-structure.py — Checks that Project_Documentation.md contains
all 8 mandatory sections in the correct order.

Usage:
    python3 validate-structure.py /path/to/Project_Documentation.md

Exit code 0 = all sections present; 1 = missing sections.
"""

import json
import re
import sys

MANDATORY_SECTIONS = [
    "References",
    "Solution Overview",
    "System Architecture",
    "Data Model & Flow",
    "API Specification",
    "Infrastructure & Deployment",
    "Monitoring & Operations",
    "Assumptions & Constraints",
]


def extract_h2_sections(content):
    """Extract all ## headings from the document."""
    pattern = re.compile(r'^##\s+\d*\.?\s*(.+)$', re.MULTILINE)
    return [m.group(1).strip() for m in pattern.finditer(content)]


def validate(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, FileNotFoundError) as e:
        return {'status': 'error', 'message': str(e)}

    found_sections = extract_h2_sections(content)
    found_lower = [s.lower() for s in found_sections]

    missing = []
    present = []
    for section in MANDATORY_SECTIONS:
        if section.lower() in found_lower:
            present.append(section)
        else:
            missing.append(section)

    # Check order of present mandatory sections
    order_issues = []
    mandatory_indices = []
    for section in MANDATORY_SECTIONS:
        if section.lower() in found_lower:
            idx = found_lower.index(section.lower())
            mandatory_indices.append((section, idx))

    for i in range(len(mandatory_indices) - 1):
        if mandatory_indices[i][1] > mandatory_indices[i + 1][1]:
            order_issues.append(
                f"'{mandatory_indices[i][0]}' appears after '{mandatory_indices[i + 1][0]}'"
            )

    # Check for H1 title
    has_title = bool(re.search(r'^#\s+.+', content, re.MULTILINE))

    result = {
        'status': 'pass' if not missing and not order_issues else 'fail',
        'has_title': has_title,
        'total_sections': len(found_sections),
        'mandatory_present': len(present),
        'mandatory_total': len(MANDATORY_SECTIONS),
        'missing_sections': missing,
        'order_issues': order_issues,
        'all_sections': found_sections,
    }

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: validate-structure.py <path-to-markdown>", file=sys.stderr)
        sys.exit(1)

    result = validate(sys.argv[1])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['status'] == 'pass' else 1)


if __name__ == '__main__':
    main()
