```instructions
---
description: Mermaid diagram types, formatting rules, and caption standards for Project Documentation.
---

# Diagram Standards

## Required Diagrams (6-7 per document)

### Fig 1: Context Diagram
- Type: flowchart TD or LR
- Shows: the system as central node, external actors (users, services, APIs) around it
- Use subgraph for the system boundary
- All external interactions visible

### Fig 2: Technology Map
- Type: mindmap
- Shows: technology stack organized by category
- Categories: max 4 categories (e.g., Backend, Data, Infrastructure, External)
- Max 3-4 items per category, 10-14 total leaves
- Each leaf = single technology name (e.g., "FastAPI", "Redis"), NOT descriptions
- Max depth: 2 levels (root → category → technology)
- NO nested sub-categories within categories
- Derived from imports, package.json/requirements.txt, configs

### Fig 3: Component Diagram
- Type: flowchart TD with subgraph
- Shows: internal modules/packages and their dependencies
- Each component = a subgraph or node
- Arrows show dependency direction (who calls whom)
- Group by layer: API/Presentation, Business Logic/Services, Data Access, Infrastructure

### Fig 4: Architecture / Deployment Diagram
- Type: flowchart LR or TD
- Shows: deployment units (containers, servers, services) and network topology
- Derived from Dockerfile, docker-compose.yml, Terraform, Kubernetes manifests
- Use subgraph for environments/networks

### Fig 5-7: Sequence Diagrams (Key Flows)
- Type: sequenceDiagram
- Shows: 2-3 most important request flows through the system
- Choose flows based on: main API endpoints, core business logic, data processing pipelines
- Participants = actual components/services from the codebase
- Include: HTTP calls, DB queries, queue messages, external API calls

## Caption Rules
- Every diagram MUST have a caption
- Caption format: italic text below the diagram
- Pattern: `*Fig N: Description*`
- Examples:
  - `*Fig 1: System context diagram*`
  - `*Fig 2: Technology stack*`
  - `*Fig 3: Component diagram*`
  - `*Fig 4: Deployment architecture*`
  - `*Fig 5: User authentication flow*`

## Mermaid Rules
- Allowed types: flowchart, graph, sequenceDiagram, mindmap
- FORBIDDEN types: C4Context, C4Container, C4Component, block-beta (rendering issues)
- Use subgraph for logical grouping
- Use abstract names (Auto-Scaling Group, not Instance-1, Instance-2)
- Node labels should match component names in text and tables
- Keep diagrams SIMPLE and READABLE:
  - flowchart/graph: max 12-15 nodes
  - sequenceDiagram: max 6 participants, max 15 interactions
  - mindmap: max 2 levels deep, max 14 leaves total
- If architecture is complex, split into multiple focused diagrams rather than one huge one
- ALWAYS test that diagrams render correctly — avoid complex nested subgraphs

## Diagram Accuracy Rule
Every node in a diagram MUST correspond to something found in the codebase:
- A module, package, or directory
- A class or service
- A configuration entry (docker-compose service, Terraform resource)
- An external dependency (from requirements.txt, package.json)

DO NOT add components that are not in the code.
```
