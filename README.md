# Copilot Agents

Reusable GitHub Copilot chat agents for AWS infrastructure design and documentation workflows.

## Agents

| Agent | Description |
|-------|-------------|
| publisher | Mermaid diagram conversion to PNG and Confluence publishing |
| researcher | Web research and documentation gathering |
| solution-designer | AWS infrastructure design document creation |
| critic | Design document review and validation |
| orchestrator | Multi-agent workflow coordination |
| devops | Terraform deployment and AWS infrastructure |

## Installation

### Option 1: Git Submodule (Recommended)

```bash
# Add as submodule in your project
git submodule add git@github.com:YOUR-ORG/copilot-agents.git .github/copilot-agents

# Create symlinks
ln -s copilot-agents/agents .github/agents
ln -s copilot-agents/instructions .github/instructions
ln -s copilot-agents/skills .github/skills
```

### Option 2: Direct Clone to .github

```bash
# Clone directly into .github folder
git clone git@github.com:YOUR-ORG/copilot-agents.git .github
```

### Option 3: Copy Files

```bash
# Copy files manually
cp -r copilot-agents/agents .github/
cp -r copilot-agents/instructions .github/
cp -r copilot-agents/skills .github/
```

## Usage

After installation, agents are available in VS Code via `@agent-name`:

```
@publisher publish document to Confluence
@researcher research AWS autoscaling best practices
@orchestrator create solution design for TTS service
```

## Project-Specific Configuration

Add project-specific instructions in `.github/copilot-instructions.md`:

```markdown
# Project Instructions

## Project Context
[Your project description]

## Naming Convention
[Project naming rules]
```

## Structure

```
copilot-agents/
├── agents/           # Agent definitions (.agent.md files)
├── instructions/     # Detailed agent instructions
│   ├── publisher/
│   ├── orchestrator/
│   ├── critic/
│   ├── solution-designer/
│   └── shared/
├── skills/           # Reusable skill modules
│   ├── workflow-logger/
│   ├── workflow-state-manager/
│   └── ...
└── README.md
```

## Updating

```bash
# Update submodule to latest version
git submodule update --remote .github/copilot-agents
```

## License

MIT
