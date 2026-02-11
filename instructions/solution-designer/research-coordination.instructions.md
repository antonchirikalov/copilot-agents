---
description: How Solution Designer coordinates research with Researcher agent before and during design work.
---

# Research Coordination

## Rule: ALWAYS Research First
Conduct thorough research BEFORE creating any design. This is NOT optional.
Even if you think you know the answer, research validates assumptions and provides authoritative sources.

## Research File Location
All research goes to: generated_docs_[TIMESTAMP]/research/[topic]_research.md

## Parallel Research Pattern
CRITICAL: Request PARALLEL execution of multiple researchers for faster results.

### Initial Research (before design starts)
Identify 2-4 main technical domains from requirements. Launch researchers simultaneously:

```
Launch researchers IN PARALLEL:

Subagent 1: Research [Domain 1 with full context].
  Find: AWS official documentation, best practices, real-world examples, case studies.
  Output: research/[domain1]_research.md

Subagent 2: Research [Domain 2 with full context].
  Find: AWS official documentation, integration patterns, production implementations.
  Output: research/[domain2]_research.md

Subagent 3: Research [Domain 3 with full context].
  Find: AWS official documentation, performance data, common issues, solutions.
  Output: research/[domain3]_research.md

Run all subagents simultaneously.
```

### Targeted Research (during design or revision)
For specific knowledge gaps discovered during work:
```
Research [specific technical question with context].
Find: [specific information needed].
Output: research/[specific_topic]_research.md
```

## After Research Completes
1. Read ALL research files from generated_docs_[TIMESTAMP]/research/
2. Extract vendor URLs from Sources sections for References table
3. Incorporate findings into architecture decisions
4. If gaps remain, request additional targeted research

## Invoking Researcher
Use runSubagent tool:
```
runSubagent(
  description: "Research [brief topic]",
  prompt: "Research [detailed topic with context]. Find: [specific items]. Output file: generated_docs_[TIMESTAMP]/research/[topic]_research.md"
)
```

## Extended Thinking Protocol
Match thinking depth to decision complexity:
- think: Basic architectural decisions, straightforward component selection
- think hard: Multi-component integration, trade-off analysis between 2-3 options
- think harder: Complex distributed systems, 4+ alternative approaches
- ultrathink: Critical architecture decisions, security-sensitive designs

Before finalizing architecture, always:
"Ultrathink about optimal architecture considering: scalability, reliability, performance, cost drivers, operational complexity, security, and how research findings validate or challenge this approach."
