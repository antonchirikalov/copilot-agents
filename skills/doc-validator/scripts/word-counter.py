#!/usr/bin/env python3
"""
word-counter.py — Counts words per section and validates limits.

Target: 4000-6000 words
Hard limit: 8000 words

Usage:
    python3 word-counter.py /path/to/Project_Documentation.md
"""

import re
import sys


TARGET_MIN = 4000
TARGET_MAX = 6000
HARD_LIMIT = 8000


def count_words(text):
    """Count words excluding Mermaid code blocks and metadata."""
    cleaned = re.sub(r'```mermaid.*?```', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'```.*?```', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'\|[^\n]+\|', '', cleaned)
    words = re.findall(r'[a-zA-Zа-яА-ЯёЁ0-9]+', cleaned)
    return len(words)


def split_sections(content):
    """Split document into sections by ## headings."""
    parts = re.split(r'^(##\s+.+)$', content, flags=re.MULTILINE)

    sections = []
    preamble = parts[0] if parts else ''
    if preamble.strip():
        sections.append(('Preamble', preamble))

    for i in range(1, len(parts), 2):
        heading = parts[i].strip().lstrip('#').strip()
        body = parts[i + 1] if i + 1 < len(parts) else ''
        sections.append((heading, body))

    return sections


def validate(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"FAIL: File not found: {filepath}")
        return False

    total_words = count_words(content)
    sections = split_sections(content)

    print(f"{'Section':<40} {'Words':>6}")
    print('-' * 48)

    for name, body in sections:
        wc = count_words(body)
        print(f"{name:<40} {wc:>6}")

    print('-' * 48)
    print(f"{'TOTAL':<40} {total_words:>6}")
    print()

    ok = True
    if total_words < TARGET_MIN:
        print(f"WARN: Below target minimum ({total_words} < {TARGET_MIN})")
    elif total_words > HARD_LIMIT:
        print(f"FAIL: Exceeds hard limit ({total_words} > {HARD_LIMIT})")
        ok = False
    elif total_words > TARGET_MAX:
        print(f"WARN: Above target maximum ({total_words} > {TARGET_MAX}), within hard limit")
    else:
        print(f"PASS: Word count within target range ({TARGET_MIN}-{TARGET_MAX})")

    return ok


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-markdown>")
        sys.exit(1)
    success = validate(sys.argv[1])
    sys.exit(0 if success else 1)
