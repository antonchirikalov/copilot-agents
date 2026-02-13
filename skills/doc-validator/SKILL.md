# Doc Validator Skill

Validates the generated `Project_Documentation.md` against quality rules.

## Scripts

| Script | Purpose |
|--------|---------|
| `validate-structure.py` | Checks all 8 mandatory sections are present |
| `word-counter.py` | Counts words per section, flags target/limit violations |
| `diagram-checker.py` | Verifies Mermaid diagrams: count, types, captions |

## Usage

```bash
python3 scripts/validate-structure.py /path/to/Project_Documentation.md
python3 scripts/word-counter.py /path/to/Project_Documentation.md
python3 scripts/diagram-checker.py /path/to/Project_Documentation.md
```

## Exit Codes

- `0` — all checks passed
- `1` — validation errors found (details printed to stdout as JSON)

## Requirements

- Python 3.8+
- Standard library only (no external dependencies)
