# Coding Workflow Instructions

The Coder agent follows a strict PLAN → CODE → VERIFY → DELIVER cycle. Never skip phases.

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

Present to the user:

```markdown
## Summary
- Tasks: 8/8 completed
- Tests: 24 passed, 0 failed
- Lint: clean (ruff + mypy)
- Files changed: 5 modified, 3 created

## Suggested commit message
feat: implement user memory service with Redis caching

- Add UserMemoryService with CRUD operations
- Add Redis cache layer with TTL
- Add pytest tests for all service methods
- Update dependencies in pyproject.toml
```
