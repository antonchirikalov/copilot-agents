---
description: Complete validation checklist for Critic agent when reviewing Solution Design documents.
---

# Review Checklist

## STEP 1: MANDATORY STRUCTURE VALIDATION (before content review)
If ANY item fails, immediately return REJECTED with CRITICAL issue.

### 1.1 Document Structure
Verify Solution Design has ALL required sections in order:
1. References - Table with # column, 5-10 vendor URLs
2. Requirements - Functional and non-functional requirements tables
3. Solution Overview - 2-3 paragraph description, TEXT ONLY (no diagrams)
4. Proposed Solution - Architecture + 1-2 Mermaid diagrams + Component table
5. Technology Map - Overview + Mermaid mindmap (max 4 categories, 8-10 elements)
6. AWS Services Specification and Deployment Architecture - AWS diagram + Services table
7. Monitoring and Observability - Capabilities table + metrics/alerting
8. Assumptions and Constraints - Assumptions table + Constraints table

Missing section → CRITICAL: "Missing required section [NAME]"

### 1.2 Requirements Compliance
- [ ] All requirements from user prompt addressed in design
- [ ] Requirements section lists all user-stated requirements
- [ ] Architecture fulfills functional requirements
- [ ] Non-functional requirements addressed (performance, scalability, reliability)
- [ ] If research exists: design follows research best practices

Missing user requirement → CRITICAL
Contradicts research → MAJOR

### 1.3 Mermaid Diagram Validation
- [ ] All diagrams use ```mermaid code blocks
- [ ] Valid types: flowchart, graph, sequenceDiagram, mindmap
- [ ] NO C4 syntax (C4Context, C4Container, C4Component are FORBIDDEN)
- [ ] Each diagram has caption: "Fig N: Description"
- [ ] No ASCII art (┌─┐│└┘ characters)
- [ ] Section 3 (Solution Overview) has NO diagrams
- [ ] Section 4 (Proposed Solution) has 1-2 diagrams

### 1.4 Diagram Abstraction
- [ ] No specific instances: Instance 1/2/3, EC2_1/EC2_2
- [ ] Uses abstract components: Auto-Scaling Group, GPU Instances (generic)
- [ ] No fixed deployment counts as separate nodes

Specific instances found → CRITICAL

### 1.5 Low-Level Details Check
FORBIDDEN in Solution Design:
- [ ] No exact CIDR blocks, IP addresses, subnet sizes
- [ ] No timeout values, memory/CPU specs, bandwidth numbers
- [ ] No port numbers, retention policies, connection pool sizes
- [ ] No implementation sequences or step-by-step procedures

Low-level details found → CRITICAL

### 1.6 Forbidden Sections
- [ ] No "Table of Contents"
- [ ] No "Future Enhancements" / "Future Improvements"
- [ ] No "Cost Estimation" / "Cost Analysis" / "Pricing"
- [ ] No "Implementation Roadmap" / "Implementation Timeline"
- [ ] No "Project Timeline" / "Development Schedule"

Forbidden section found → REJECTED with CRITICAL

### 1.7 Content Guidelines
- [ ] No bold formatting (**text**)
- [ ] No code examples in Solution Design
- [ ] No pricing/cost estimates

## STEP 2: SIZE VALIDATION (CRITICAL - check before content review)

### 2.1 Document Size Limits
- [ ] Solution Design: max 4000 words (hard limit 5000)
- Estimate word count by reading the document
- If clearly over limit → CRITICAL: "Document exceeds size limit. Estimated [X] words, max [Y]. Cut verbose descriptions, merge sections, remove redundancy."

### 2.2 Section Balance
- [ ] No single section dominates (>40% of document)
- [ ] Tables used instead of long paragraphs where possible
- [ ] Component descriptions are 1-3 sentences, not multi-paragraph essays

## STEP 3: TECHNICAL CONTENT REVIEW (only after Steps 1-2 pass)

### Completeness
- All architecture components specified
- Scaling policies detailed (if applicable)
- Health check parameters defined
- Monitoring strategy complete

### Consistency
- Diagrams match textual descriptions
- Instance types, configurations consistent throughout
- Resource naming conventions consistent
- Internal consistency maintained throughout document

### Feasibility
- AWS service limits respected
- Implementation realistic
- Timing realistic (grace periods, cooldowns)
- Technical soundness validated

## OUT OF SCOPE (do not critique)
- Cost optimization
- Load testing approaches
- Model performance
- AMI building process
- Implementation timelines
- Pricing estimates
