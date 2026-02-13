# Test Runner Skill

Runs pytest and linters (ruff, mypy), parses output into structured reports.

## Scripts

| Script | Purpose |
|--------|---------|
| `test-runner.py` | Run pytest, parse results into JSON summary |
| `lint-runner.py` | Run ruff + mypy, parse results into JSON summary |

## Usage

```bash
python3 scripts/test-runner.py /path/to/project [--tests tests/] [--markers unit]
python3 scripts/lint-runner.py /path/to/project [--fix]
```

## Output

Both scripts print JSON to stdout:

```json
{
  "status": "pass",
  "total": 24,
  "passed": 22,
  "failed": 2,
  "errors": [],
  "failures": [
    {"test": "test_cache_ttl", "file": "tests/test_cache.py", "message": "AssertionError..."}
  ]
}
```

## Requirements

- Python 3.8+
- pytest, ruff, mypy must be installed in the target project
