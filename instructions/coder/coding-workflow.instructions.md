# Coding Workflow Instructions

The Coder agent follows a strict PLAN → CODE → VERIFY → DELIVER cycle. Never skip phases.

## Phase 0: BRANCH

Before starting any work, ask the user whether to create a new git branch.

**CRITICAL:** When using `ask_questions` tool, do NOT mark any option as `recommended`. Do NOT proceed until the user explicitly answers. This is a blocking question — wait for the user's choice.

**Prompt:**
> Create a new branch from current for this work? (yes/no)

**If yes:**
```bash
git checkout -b feat/<short-description>
```

Branch naming convention:
- Features: `feat/<description>` (e.g., `feat/jwt-auth`)
- Fixes: `fix/<description>` (e.g., `fix/redis-ttl`)
- Refactor: `refactor/<description>` (e.g., `refactor/chat-service`)

**If no:** work on the current branch.

---

## Phase 1: PLAN

### Input Analysis

The user provides one of:
- **Text description** — natural language task description
- **Document** — PRD, issue, design doc, or technical spec
- **Code reference** — "refactor this", "add feature to X"
- **Bug report** — error message, failing test, unexpected behavior

### Codebase Discovery

Before planning, understand the existing codebase:

1. **Read project structure** — `list_dir` to understand layout
2. **Read config** — `pyproject.toml`, `pytest.ini`, `.env.example` for tooling and settings
3. **Read related code** — files that will be modified or depend on new code
4. **Check existing tests** — understand test patterns already in use
5. **Look up library docs** — use Context7 for any unfamiliar APIs

### TASKS.md Generation

Generate `TASKS.md` in the project root (or working directory). See [task-management](task-management.instructions.md) for exact format.

Rules:
- Break work into **atomic tasks** (each task = one logical unit of work)
- Order tasks by dependency (independent tasks first)
- Include test tasks explicitly (handled by test-writer subagent)
- Estimate complexity: `[S]` small, `[M]` medium, `[L]` large
- Maximum 15 tasks — if more, group into phases

### Approval Gate

Present TASKS.md to the user. Wait for approval before coding.
- If user says "go" / "да" / "approved" → proceed to Phase 2
- If user gives feedback → revise plan → re-present

## Phase 2: CODE

### Task Loop

For each task in TASKS.md:

```
1. Mark task → 🔄 in_progress
2. Read relevant source files
3. Look up library docs via Context7 if needed
4. Implement the code change
5. Launch @test-writer to write tests (parallel)
6. Run quick lint: ruff check <changed_files>
7. Fix lint issues if any
8. Mark task → ✅ completed
9. Next task
```

### Coding Principles

- **Read before write** — always read the file before editing it
- **Small edits** — prefer multiple small `replace_string_in_file` over rewriting whole files
- **Run frequently** — lint after every task, not just at the end
- **Context7 for APIs** — look up docs when using library features, don't guess parameters
- **Follow existing patterns** — match the codebase's style, not your preferences

### Test-Writer Coordination

When launching test-writer:
- Provide the source file path
- Describe what was implemented
- Specify any critical edge cases to test
- Don't wait for test-writer to finish before starting next coding task

## Phase 3: VERIFY

After all coding tasks are complete:

### 3a. Test Suite
```bash
pytest --tb=short -q
```
- If ALL PASS → proceed to lint
- If FAIL → read failures → fix code → rerun (max 5 cycles)
- Track fix cycles in TASKS.md log

### 3b. Lint & Type Check
```bash
ruff check .
mypy .
```
- Fix all errors (ruff auto-fix: `ruff check --fix .`)
- Rerun until clean

### 3c. Final Test Run
```bash
pytest --tb=short -q --co  # dry run to count tests
pytest --tb=short -q       # full run
```

## Phase 4: DELIVER

### 4a. Commit

Commit all changes:
```bash
git add -A
git commit -m "<type>: <description>"
```

Commit message format: `<type>: <short description>` + bullet list of changes.
Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.

### 4b. Summary

Present to the user:

```markdown
## Summary
- Branch: feat/jwt-auth
- Tasks: 8/8 completed
- Tests: 24 passed, 0 failed
- Lint: clean (ruff + mypy)
- Files changed: 5 modified, 3 created
```

### 4c. Pull Request

Ask the user:
> Create a Pull Request? (yes/no)

**CRITICAL:** When using `ask_questions` tool, do NOT mark any option as `recommended`. Do NOT proceed until the user explicitly answers. This is a blocking question — wait for the user's choice.

**If yes:**
```bash
git push origin <branch-name>
```
Then create a PR using GitHub MCP with:
- **Title:** commit message
- **Body:** summary from 4b + task list from TASKS.md
- **Base:** the branch that was current before Step 0

**If no:** inform the user the branch is ready for manual PR creation.
