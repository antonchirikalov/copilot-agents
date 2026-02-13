```instructions
---
description: Required structure and section definitions for the Project Documentation document generated from existing codebases.
---

# Project Documentation Template

## Document Rules
- Single document: Project_Documentation.md
- Describes ONLY what exists in the codebase
- NO recommendations, future plans, roadmaps, timelines, cost estimates
- NO bold formatting (**text**) anywhere
- NO code examples or code snippets
- NO Table of Contents
- Professional technical language throughout

## Required Sections (ALL mandatory, in this order)

### 1. References
- Table with # column
- 5-10 URLs to official documentation of frameworks/libraries found in codebase
- Sources: official docs of detected technologies (e.g., fastapi.tiangolo.com, docs.sqlalchemy.org)
- Use Context7 and Tavily to find accurate URLs
- DO NOT include internal file paths

### 2. Solution Overview
- 2-3 paragraphs: what the system does, who uses it, what problem it solves
- Key architectural decisions visible from the code
- Technology stack summary
- Diagrams: Context diagram + Technology mindmap

### 3. System Architecture
- Component descriptions with responsibilities (derived from modules/packages)
- Component table: # | Component | Responsibility | Key Technologies
- Inter-component communication patterns (HTTP, queues, shared DB, etc.)
- Diagrams: Component diagram + Architecture/Deployment diagram

### 4. Data Model and Flow
- Data entities table: # | Entity | Fields Summary | Storage
- Relationships between entities
- Key data flows through the system
- Diagrams: 2-3 Sequence diagrams for main scenarios (derived from API routes and handlers)

### 5. API Specification
- Endpoints table: # | Method | Path | Description | Auth
- Derived from route decorators (@app.route, @router.get, etc.)
- Request/response model summaries from Pydantic/dataclass definitions
- If no REST API found, describe the system's primary interfaces (CLI, message consumers, etc.)

### 6. Infrastructure and Deployment
- What is defined in Dockerfile, docker-compose.yml, Terraform, CI/CD configs
- Environment configurations found (.env.example, config files)
- Deployment topology as visible from infrastructure code
- If no IaC found, state "Infrastructure as Code not present in repository"

### 7. Monitoring and Operations
- Logging configuration found in code (loggers, log levels, handlers)
- Health check endpoints if present
- Metrics collection if configured (Prometheus, StatsD, etc.)
- Alerting rules if defined
- If minimal, describe what IS configured, do not invent

### 8. Assumptions and Constraints
- Technical constraints evident from code (Python version, dependency pins, platform requirements)
- External service dependencies (databases, message brokers, third-party APIs)
- Known limitations visible from code comments, TODOs, or configuration

## Section Size Guidelines
| Section | Target Lines |
|---------|-------------|
| References | 15-25 |
| Solution Overview | 40-60 |
| System Architecture | 80-120 |
| Data Model and Flow | 60-100 |
| API Specification | 40-80 |
| Infrastructure and Deployment | 30-50 |
| Monitoring and Operations | 20-40 |
| Assumptions and Constraints | 15-30 |

## Total Document Size
- Target: 4000-6000 words
- Hard limit: 8000 words
- Be CONCISE: tables over paragraphs, short statements over explanations

## Forbidden Content
- Recommendations or suggestions ("consider adding", "it would be better to")
- Future plans, roadmaps, next steps
- Cost estimates or pricing
- Timeline or phases
- Performance benchmarks (unless found in test files)
- Security audit results (unless documented in code)
- Comparisons with alternative approaches
```
