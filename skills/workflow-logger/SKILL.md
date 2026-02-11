---
name: workflow-logger
description: Structured markdown logging for multi-agent design workflows. Appends formatted events to workflow_log.md with timestamps, phase info, and agent activity. Use when recording workflow progress, phase transitions, Critic verdicts, or final summaries.
---

# Workflow Logger

## When to use
- At workflow start (create log with header)
- At each phase transition
- After each agent completes work
- After each Critic verdict
- At workflow completion (final summary)

## How to use

### Initialize log
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py init --folder generated_docs_[TIMESTAMP] --project "Project Name"
```

### Log phase start
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py phase --folder generated_docs_[TIMESTAMP] --phase "Phase 1: Research" --agents "Researcher x3"
```

### Log event
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py event --folder generated_docs_[TIMESTAMP] --message "Research complete. 3 files created."
```

### Log Critic verdict
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py verdict --folder generated_docs_[TIMESTAMP] --iteration 2 --verdict CONDITIONAL --critical 0 --major 2 --minor 1 --issues '[{"severity":"MAJOR","section":"4","issue":"Specific instance nodes in diagram","action":"Replace with abstract fleet node"},{"severity":"MINOR","section":"5","issue":"Mindmap exceeds 10 elements","action":"Consolidate items"}]'
```

If issues JSON is not available, fall back to summary:
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py verdict --folder generated_docs_[TIMESTAMP] --iteration 2 --verdict CONDITIONAL --critical 0 --major 2 --minor 1 --summary "Diagram issues and missing monitoring details"
```

### Log completion
```bash
python3 .github/skills/workflow-logger/scripts/workflow-logger.py complete --folder generated_docs_[TIMESTAMP] --iterations 3
```

## Output format
The script appends formatted markdown to `workflow_log.md`:
```markdown
# Workflow Execution Log
Project: Fish TTS Autoscaling
Started: 2026-02-10 17:28:21
Status: In Progress

## Execution Timeline

### [2026-02-10 17:28:21] Phase 1: Research
- Activated: Researcher x3
- Status: In progress

### [2026-02-10 17:30:45] Review - Iteration 2/5
- Verdict: CONDITIONAL
- Critical: 0, Major: 2, Minor: 1
- Key feedback: Diagram issues and missing monitoring details

## Final Summary
- Status: COMPLETED
- Total iterations: 3
- Completion time: 2026-02-10 17:42:15
- Processing time: 13m 54s
- Documents approved: YES
- Next steps: Invoke DevOps agent with 'deploy' command
```
