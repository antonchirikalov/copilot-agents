```instructions
---
description: How to interpret the project_map.json output from codebase-scanner and use it for documentation generation.
---

# Scan Analysis Guide

## project_map.json Structure

The codebase scanner produces a JSON file with these top-level keys:

### project_info
- `name`: Project name (from directory or setup.py/pyproject.toml)
- `root_path`: Scanned directory
- `total_files`: File count by extension
- `total_lines`: Line count by language

### structure
- Directory tree with file types
- Use to understand project organization and naming conventions

### modules
- Per-file analysis: classes, functions, decorators, docstrings
- Key fields per module:
  - `classes`: name, methods, bases (inheritance), decorators
  - `functions`: name, arguments, decorators, return type
  - `imports`: internal (within project) and external (third-party)

### routes
- API endpoints extracted from decorators
- Fields: method, path, function_name, file
- Supports: Flask (@app.route), FastAPI (@router.get), Django (urlpatterns)

### models
- Data model classes: SQLAlchemy, Django ORM, Pydantic, dataclasses
- Fields: class_name, fields (name, type), file, base_class

### dependencies
- From requirements.txt, setup.py, pyproject.toml, Pipfile
- Package names and version constraints

### configs
- Detected configuration files and their key entries
- .env.example variables, docker-compose services, Terraform resources

### infrastructure
- Docker: services from docker-compose, Dockerfile instructions
- CI/CD: pipeline stages from .github/workflows, Jenkinsfile, .gitlab-ci.yml
- IaC: Terraform resources, CloudFormation stacks

## Analysis Strategy

### Step 1: Big Picture (from project_info + structure)
- Determine project type: monolith, microservices, library, CLI tool
- Identify primary language and framework
- Count services and entry points

### Step 2: Architecture (from modules + imports)
- Map internal imports to understand module dependencies
- Identify layers: API, service, repository, model
- Find entry points (main.py, app.py, manage.py)

### Step 3: Data (from models + routes)
- Map data entities and relationships
- Connect routes to handler functions to models
- Identify key data flows

### Step 4: Infrastructure (from configs + infrastructure)
- Understand deployment topology
- Map environment variables to service configurations
- Identify external dependencies (databases, queues, APIs)

### Step 5: Deep Read
After analyzing project_map.json, deep-read these files:
1. Main entry point (app.py, main.py)
2. Configuration files (settings.py, config.py)
3. Key model files (models.py, schemas.py)
4. API route files (routes.py, views.py, api/)
5. Docker/infrastructure files
6. README.md (if exists, for project context)

## When project_map.json Is Insufficient
If scanner misses something (complex metaprogramming, dynamic routes):
- Use grep_search to find patterns manually
- Use semantic_search for concept-level discovery
- Read specific files with read_file
- State "Not determined from codebase" if truly unknowable
```
