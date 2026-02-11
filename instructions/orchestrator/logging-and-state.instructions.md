---
description: Workflow logging format and state tracking for the orchestrator.
---

# Workflow Logging and State

## Workflow Log File
Create generated_docs_[TIMESTAMP]/workflow_log.md at workflow start.
Update after every significant event.

### Initial Template
```markdown
# Workflow Execution Log
Project: [From user request]
Started: [YYYY-MM-DD HH:MM:SS]
Status: In Progress

## Summary
- Current Phase: 1 (Research)
- Total Iterations: 0
- Status: Starting workflow

## Execution Timeline
```

### Event Formats

Phase start:
```
### [YYYY-MM-DD HH:MM:SS] Phase N: [Phase Name]
- Activated: [Agent name(s)]
- Task: [Description]
- Status: In progress
```

Research complete:
```
- Status: Completed
- Files created: [list of research file paths]
```

Design complete:
```
- Document created:
  - Solution Design: [path]
```

Critic verdict:
```
### [YYYY-MM-DD HH:MM:SS] Review - Iteration N/5
- Verdict: [APPROVED/CONDITIONAL/REJECTED]
- Critical: [count], Major: [count], Minor: [count]

Issues:

| # | Severity | Section | Issue | Required Action |
|---|----------|---------|-------|-----------------|
| 1 | CRITICAL | 4 | [issue description] | [action] |
| 2 | MAJOR | 6 | [issue description] | [action] |
```

IMPORTANT: Always log the FULL issues table from the Critic verdict. Do not summarize — copy all rows.

Final summary (append when workflow completes):
```
## Final Summary
- Status: COMPLETED
- Total iterations: [N]
- Completion time: [YYYY-MM-DD HH:MM:SS]
- Processing time: [Xm Ys] (calculated from Started timestamp)
- Documents approved: YES
- Next steps: Invoke DevOps agent with 'deploy' command
```

## Update Frequency
Update the log at:
- Start of each phase
- Each agent activation
- Each Critic verdict
- Each phase completion
- Workflow completion

## State Tracking
Maintain in context throughout workflow:
| State Variable | Values |
|---------------|--------|
| Current phase | 1 (Research), 2 (Design), 3 (Review), 4 (Delivery) |
| Iteration number | 1-5 |
| Documents status | draft / in-review / approved |
| Research files | list of created file paths |
| Last Critic verdict | APPROVED / CONDITIONAL / REJECTED / none |
| Timestamp folder | generated_docs_[YYYYMMDD_HHMMSS] |
