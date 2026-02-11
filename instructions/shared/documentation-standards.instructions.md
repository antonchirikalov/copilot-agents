---
description: Rules for creating and reviewing technical documentation. Applied when any agent creates Solution Design or reviews documents.
---

# Documentation Standards

## Formatting Rules
- NO bold formatting (**text**) anywhere in documents
- NO ASCII art diagrams (characters like ┌─┐│└┘)
- Use Mermaid diagrams ONLY (```mermaid code blocks)
- Number all figures sequentially: "Fig N: Description"
- Tables always include # column for row numbering
- Professional technical language throughout
- No code examples in Solution Design

## Mermaid Diagram Rules
- Allowed types: flowchart, graph, sequenceDiagram, mindmap
- FORBIDDEN types: C4Context, C4Container, C4Component
- Each diagram has caption: "Fig N: Description"
- Use abstract components (Auto-Scaling Group, not Instance 1/2/3)
- Use subgraph for logical grouping where applicable
- Width 1200px recommended for PNG export

## Forbidden Content in Solution Design
These sections and content types are NEVER allowed:
- Pricing / cost estimates
- Future Enhancements or Future Improvements section
- Implementation Roadmap or Timeline section
- Project Timeline or Development Schedule
- Table of Contents
- Low-level implementation details (CIDR blocks, IP addresses, exact timeout values, port numbers, memory specs)
- Specific instance representations in diagrams (Instance 1, Instance 2, EC2_1, EC2_2)

## References Section Rules
- Table with # column for row numbering
- 5-10 external vendor documentation URLs
- Valid sources: docs.aws.amazon.com, docs.nvidia.com, registry.terraform.io
- INVALID: internal file paths to research .md files
- Extract URLs from research findings files

## Document Size Limits (CRITICAL - applies to ALL documents)
- Solution Design: max 4000 words (hard limit 5000)
- Research files: max 2000 words per file
- Be CONCISE: tables over paragraphs, short sentences over long explanations
- After creating document, verify word count is within limits
- If over limit: cut verbose descriptions, merge sections, remove redundancy
