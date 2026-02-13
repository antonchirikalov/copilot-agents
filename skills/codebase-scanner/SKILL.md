# Codebase Scanner Skill

Scans a Python project directory and produces a structured `project_map.json` with metadata for documentation generation.

## Usage

```bash
python3 scripts/codebase-scanner.py /path/to/project [--output project_map.json]
```

## What It Extracts

| Category | Source | Method |
|----------|--------|--------|
| Structure | Directory tree | `os.walk` |
| Modules | Classes, functions, decorators | `ast` module |
| Imports | Internal and external | `ast.Import`, `ast.ImportFrom` |
| Routes | API endpoints | Decorator parsing |
| Models | ORM/Pydantic/dataclass definitions | Class inheritance |
| Dependencies | requirements.txt, pyproject.toml | File parsing |
| Configs | .env, docker-compose, Terraform | File detection + parsing |
| Infrastructure | Docker, CI/CD, IaC | Pattern matching |

## Output

`project_map.json` — single JSON file consumed by the Project Documenter agent.

## Requirements

- Python 3.8+
- Standard library only (no external dependencies)
