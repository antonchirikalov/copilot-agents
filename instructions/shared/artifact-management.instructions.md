---
description: File path conventions and artifact folder structure for multi-agent workflow output.
---

# Artifact Management

## Folder Structure
All workflow output goes into a timestamped folder created by Orchestrator at workflow start:

```
generated_docs_[YYYYMMDD_HHMMSS]/
├── Solution_Design_Document.md
├── workflow_log.md
├── workflow_state.json
├── research/
│   ├── [topic1]_research.md
│   ├── [topic2]_research.md
│   └── ...
├── terraform/              (DevOps agent only)
│   ├── main.tf
│   ├── variables.tf
│   └── ...
├── images/                 (Publisher agent only)
│   ├── mermaid-fig-1.png
│   └── ...
└── Deployment_Report.md    (DevOps agent only)
```

## Rules
- Orchestrator creates the timestamp folder and communicates path to all agents
- ALL agents use the SAME timestamp folder for the workflow run
- Never hardcode absolute paths; always use the provided folder path
- Research files go in: generated_docs_[TIMESTAMP]/research/
- Name research files descriptively: [topic]_research.md

## File Naming
| Document | Filename |
|----------|----------|
| Solution Design | Solution_Design_Document.md |
| Workflow Log | workflow_log.md |
| Research | [topic]_research.md |
| Deployment Report | Deployment_Report.md |
| Terraform outputs | terraform_outputs.json |
