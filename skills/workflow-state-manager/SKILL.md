---
name: workflow-state-manager
description: Manages workflow state for multi-agent design workflows. Tracks current phase, iteration count, document status, and agent activity. Use when orchestrating multi-phase workflows that need persistent state between agent invocations, or when checking workflow progress.
---

# Workflow State Manager

## When to use
- Starting a new multi-agent workflow (initialize state)
- Transitioning between workflow phases
- Tracking iteration count during design-review cycles
- Checking current workflow status
- Resuming an interrupted workflow

## How to use

### Initialize state
Run the state tracker script to create a new state file:
```bash
python3 .github/skills/workflow-state-manager/scripts/state-tracker.py init --folder generated_docs_[TIMESTAMP]
```
This creates `generated_docs_[TIMESTAMP]/workflow_state.json` with initial state.

### Update phase
```bash
python3 .github/skills/workflow-state-manager/scripts/state-tracker.py set-phase --folder generated_docs_[TIMESTAMP] --phase [research|design|review|delivery]
```

### Increment iteration
```bash
python3 .github/skills/workflow-state-manager/scripts/state-tracker.py increment-iteration --folder generated_docs_[TIMESTAMP]
```

### Set verdict
```bash
python3 .github/skills/workflow-state-manager/scripts/state-tracker.py set-verdict --folder generated_docs_[TIMESTAMP] --verdict [APPROVED|CONDITIONAL|REJECTED]
```

### Read current state
```bash
python3 .github/skills/workflow-state-manager/scripts/state-tracker.py status --folder generated_docs_[TIMESTAMP]
```

## State file format
The script manages `workflow_state.json`:
```json
{
  "project": "...",
  "started": "2026-02-10T17:28:21",
  "phase": "review",
  "iteration": 2,
  "max_iterations": 5,
  "verdict": "CONDITIONAL",
  "documents": {
    "solution_design": "draft"
  },
  "research_files": [],
  "history": []
}
```
