# Copilot Agents

Reusable GitHub Copilot chat agents for AWS infrastructure design and documentation workflows.

## Agents

| Agent | Role | Model | Subagents | Key Capabilities |
|-------|------|-------|-----------|------------------|
| **orchestrator** | Workflow Manager | Claude Sonnet 4.5 | researcher, solution-designer, critic | Coordinates multi-agent workflows, manages iterations (max 5), prevents loops, delivers final artifacts |
| **researcher** | Research Specialist | Claude Sonnet 4.5 | — | Web research via Tavily MCP, AWS documentation discovery, source-backed findings |
| **solution-designer** | Solution Architect | Claude Opus 4.6 | researcher, critic | Creates Solution Design documents, AWS architecture, extended thinking for complex decisions |
| **critic** | Technical Reviewer | Claude Sonnet 4.5 | — | Reviews designs, structured feedback with severity levels, APPROVED/CONDITIONAL/REJECTED verdicts |
| **devops** | DevOps Engineer | Claude Sonnet 4.5 | critic | Terraform generation from approved designs, deployment execution, verification procedures |
| **publisher** | Publications Specialist | Claude Sonnet 4.5 | — | Mermaid to PNG conversion, Confluence page creation via Atlassian MCP |

## Typical Workflow

```mermaid
flowchart TB
    subgraph Phase1["Phase 1: Research"]
        O1[Orchestrator] -->|parallel| R1[Researcher 1]
        O1 -->|parallel| R2[Researcher 2]
        O1 -->|parallel| R3[Researcher N]
    end

    subgraph Phase2["Phase 2: Design"]
        SD[Solution Designer]
        SD -.->|may request| RX[Additional Research]
    end

    subgraph Phase3["Phase 3: Review"]
        C[Critic]
        C -->|APPROVED| Done[✓ Approved]
        C -->|REJECTED/CONDITIONAL| Rev[Revision]
        Rev --> SD
        SD --> C
    end

    subgraph Phase4["Phase 4: Delivery"]
        D[Deliver Artifacts]
    end

    Phase1 --> Phase2
    Phase2 --> Phase3
    Done --> Phase4

    subgraph Optional["Post-Approval (User-Triggered)"]
        DEV[DevOps Agent]
        PUB[Publisher Agent]
    end

    Phase4 -.->|"@devops deploy"| DEV
    Phase4 -.->|"@publisher publish"| PUB
```

## Installation

### Option 1: Git Submodule (Recommended)

```bash
git submodule add git@github.com:YOUR-ORG/copilot-agents.git .github/copilot-agents

ln -s copilot-agents/agents .github/agents
ln -s copilot-agents/instructions .github/instructions
ln -s copilot-agents/skills .github/skills
```

### Option 2: Direct Clone

```bash
git clone git@github.com:YOUR-ORG/copilot-agents.git .github
```

### Option 3: Copy Files

```bash
cp -r copilot-agents/agents .github/
cp -r copilot-agents/instructions .github/
cp -r copilot-agents/skills .github/
```

## Usage

```
@orchestrator create solution design for TTS service on AWS
@researcher research AWS autoscaling best practices
@devops deploy the approved solution
@publisher publish document to Confluence
```

## Project Structure

```
copilot-agents/
├── agents/              # Agent definitions (.agent.md)
├── instructions/        # Detailed instructions per agent
│   ├── orchestrator/
│   ├── solution-designer/
│   ├── critic/
│   ├── devops/
│   ├── publisher/
│   └── shared/
├── skills/              # Reusable skills with scripts
│   ├── devops/
│   ├── workflow-logger/
│   ├── workflow-state-manager/
│   └── iteration-controller/
└── README.md
```

## Configuration

Add project context in `.github/copilot-instructions.md`:

```markdown
# Project Context
[Your project description and naming conventions]
```

## Updating

```bash
git submodule update --remote .github/copilot-agents
```

## License

MIT
