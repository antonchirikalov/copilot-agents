---
description: Required structure and section definitions for Solution Design documents created by Solution Designer.
---

# Solution Design Document Structure

## Required Sections (ALL mandatory, in this order)

### 1. References
- Table with # column for row numbering
- 5-10 vendor documentation URLs (AWS, NVIDIA, Terraform docs)
- Extract URLs from research findings files (Sources section)
- DO NOT include internal .md file paths

### 2. Requirements
- Functional requirements table from user input
- Non-functional requirements table (performance, scalability, reliability)

### 3. Solution Overview
- 2-3 paragraph HIGH-LEVEL description
- Key architectural decisions and main components
- How solution addresses requirements
- TEXT ONLY in this section - NO diagrams

### 4. Proposed Solution
- Detailed architecture description
- 1-2 Mermaid diagrams (flowchart/graph/sequenceDiagram, NOT C4)
- Component table with descriptions
- Show interactions and data flow

### 5. Technology Map
- Technology stack overview paragraph
- Mermaid mindmap diagram
- Max 4 categories, 8-10 total elements

### 6. AWS Services Specification and Deployment Architecture
- AWS infrastructure diagram (Mermaid)
- Services table: # | AWS Service | Purpose | Configuration Notes

### 7. Monitoring and Observability
- Overview description
- Capabilities table: # | Capability | Purpose | Implementation
- Metrics and alerting details

### 8. Assumptions and Constraints
- Assumptions table
- Constraints table

## Optional Sections (include if relevant)
9. Data Flow - data movement diagrams
10. Security Considerations - security controls
11. Scaling Strategy - scaling policies and diagrams

## Document Size Limits (CRITICAL)
- TARGET: 6000-7000 words (~18-20 pages)
- HARD LIMIT: 8000 words absolute max (~22 pages)
- If document exceeds limit, cut low-priority content:
  1. Reduce verbose descriptions to 2-3 sentences per component
  2. Merge similar sections
  3. Remove redundant explanations
  4. Keep diagrams but reduce surrounding text
- Each section target:
  - References: 15-30 lines (table with descriptions)
  - Requirements: 30-50 lines (detailed tables with acceptance criteria)
  - Solution Overview: 20-30 lines (3-4 paragraphs, thorough context)
  - Proposed Solution: 80-120 lines (diagrams + component tables + interactions)
  - Technology Map: 25-40 lines (paragraph + mindmap + justification)
  - AWS Services: 40-60 lines (diagram + detailed service table)
  - Monitoring: 30-45 lines (tables + alerting details + dashboard description)
  - Assumptions: 25-40 lines (detailed tables with risk notes)

## Content Level
- HIGH-LEVEL architecture only
- Conceptual descriptions, not exact parameters
- Focus on architectural decisions and rationale
- No CIDR blocks, IP addresses, subnet sizes, timeout values
- No implementation sequences or step-by-step procedures
- Be CONCISE: prefer tables over paragraphs, 1-2 sentences over long explanations

## Document Creation Checklist
Before saving, verify:
- [ ] All 8 mandatory sections present
- [ ] References has 5-10 vendor URLs (not internal paths)
- [ ] Section 3 has NO diagrams (text only)
- [ ] Section 4 has 1-2 Mermaid diagrams
- [ ] All diagrams have "Fig N: Description" captions
- [ ] NO bold formatting anywhere
- [ ] NO code examples
- [ ] NO forbidden sections (cost, timeline, future enhancements)
- [ ] NO low-level details (exact params, CIDR, ports)
