# Task Management Instructions

## TASKS.md Format

```markdown
# Tasks: [short task name]

**Source:** [user input / document name / issue link]
**Generated:** YYYY-MM-DD HH:MM
**Status:** planning | in_progress | completed

## Context

[2-3 sentences describing the task from user input]

## Tasks

- [ ] 🔲 [S] Task description
- [-] 🔄 [M] Task currently in progress
- [x] ✅ [S] Completed task
- [ ] 🔲 [L] Future task

## Test Coverage

| Module | Tests | Pass | Fail |
|--------|-------|------|------|
| — | — | — | — |

## Log

[Timestamped entries added during execution]
```

## Task Statuses

| Symbol | Markdown | Meaning |
|--------|----------|---------|
| 🔲 | `- [ ] 🔲` | Not started |
| 🔄 | `- [-] 🔄` | In progress (max 1 at a time) |
| ✅ | `- [x] ✅` | Completed |
| ❌ | `- [x] ❌` | Failed / blocked (with reason) |

## Size Estimates

| Tag | Meaning | Typical Scope |
|-----|---------|---------------|
| `[S]` | Small | Single function, config change, import |
| `[M]` | Medium | New class/module, multiple functions |
| `[L]` | Large | New service, multiple files, complex logic |

## Rules

1. **Maximum 1 task in_progress** at any time
2. **Mark completed immediately** after finishing — don't batch
3. **Update Test Coverage table** after each test run
4. **Add Log entries** for: task start, task complete, test results, lint results, fix cycles
5. **Never delete tasks** — mark as ❌ with reason if skipped
6. **Task order = execution order** — don't jump ahead unless dependencies allow
7. **Maximum 15 tasks** — group into phases if more needed

## Log Entry Format

```
- HH:MM — [event]: description
```

Events: `START`, `DONE`, `TEST`, `LINT`, `FIX`, `BLOCKED`, `NOTE`

Example:
```
- 14:01 — START: Task 3 — Implement UserMemoryService
- 14:08 — DONE: Task 3 — Created app/services/user_memory_service.py
- 14:08 — START: Task 4 — Add Redis cache layer
- 14:12 — TEST: 12 passed, 2 failed (test_cache_ttl, test_cache_invalidation)
- 14:15 — FIX: Fixed TTL calculation in cache.py
- 14:15 — TEST: 14 passed, 0 failed
- 14:16 — LINT: ruff clean, mypy 0 errors
```

## TASKS.md Location

Create TASKS.md in the project root directory or the working directory specified by the user. If a TASKS.md already exists, read it first — it may contain a partially completed plan from a previous session.
