# Task Planner Skill

Parses user input or documents and generates a structured `TASKS.md` for the Coder agent.

## Usage

```bash
python3 scripts/task-planner.py --input "description text" [--output TASKS.md]
python3 scripts/task-planner.py --file requirements.md [--output TASKS.md]
python3 scripts/task-planner.py --existing TASKS.md --status
```

## Modes

| Mode | Flag | Purpose |
|------|------|---------|
| Generate | `--input` or `--file` | Create TASKS.md from text or document |
| Status | `--existing --status` | Print current progress summary |
| Update | `--existing --complete N` | Mark task N as completed |

## Output

`TASKS.md` in the specified location (default: current directory).

## Requirements

- Python 3.8+
- Standard library only
