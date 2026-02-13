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
- NO per-service subsections (e.g., "3.1 ChatService (app/services/chat_service.py)" is FORBIDDEN)
- ONE summary table of all services/components:
  # | Service/Component | Description (1 sentence) | Key Technologies
- Inter-component communication patterns (HTTP, queues, shared DB, etc.) as 1-2 sentences
- Diagrams: Component diagram (showing all services + relationships) + Deployment diagram
- Let diagrams tell the story of how components connect, NOT prose paragraphs per component

### 4. Data Model and Flow
- Data entities table: # | Entity | Fields Summary | Storage
- Relationships between entities (1-2 sentences, NOT per-entity subsections)
- Key data flows: describe in 2-3 short paragraphs, NOT per-flow subsections
- Diagrams: 2-3 Sequence diagrams for main scenarios (derived from API routes and handlers)
- Sequence diagrams ARE the detailed documentation — minimize surrounding text

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
| Section | Target Lines | Max Lines |
|---------|-------------|----------|
| References | 15-25 | 30 |
| Solution Overview | 30-50 | 60 |
| System Architecture | 50-80 | 100 |
| Data Model and Flow | 50-80 | 100 |
| API Specification | 30-60 | 80 |
| Infrastructure and Deployment | 20-40 | 50 |
| Monitoring and Operations | 15-30 | 40 |
| Assumptions and Constraints | 15-25 | 30 |

## Total Document Size
- TARGET: 4000-5000 words
- HARD LIMIT: 6000 words absolute max
- Be CONCISE: tables over paragraphs, short statements over explanations
- Let DIAGRAMS do the heavy lifting — diagrams + captions replace paragraphs
- If you are writing more than 3 sentences about one component, STOP and use a table instead

## Structure Anti-Patterns (FORBIDDEN)
- Per-service subsections like "3.1 ChatService", "3.2 LLMService", etc.
- Per-config-file subsections like "4.3 Configuration Management (app/config.py)"
- Repeating information that is already in a table or diagram
- Long prose descriptions of what a class/function does (use tables)
- Nested subsections deeper than ###

## Forbidden Content
- Recommendations or suggestions ("consider adding", "it would be better to")
- Future plans, roadmaps, next steps
- Cost estimates or pricing
- Timeline or phases
- Performance benchmarks (unless found in test files)
- Security audit results (unless documented in code)
- Comparisons with alternative approaches
```
