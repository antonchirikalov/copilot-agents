---
description: Verdict definitions and output format rules for the Critic agent reviewing documents.
---

# Verdict Rules

## Verdicts

### REJECTED
Use when:
- ANY critical issues present
- Fundamental architecture components missing
- Contradictory or infeasible specifications
- Does not meet core requirements from user prompt
- Forbidden sections present

Message: "Design REJECTED. Critical issues must be resolved before resubmission."

### CONDITIONAL
Use when:
- No critical issues
- One or more major concerns identified
- Core architecture solid but needs refinement

Message: "Design CONDITIONALLY APPROVED. Address major concerns before implementation."

### APPROVED
Use when:
- No critical issues
- No major concerns
- Minor issues acceptable
- All checklist items satisfied

Message: "Design APPROVED. Ready for next phase."

## Issue Categories

### CRITICAL (Blockers)
```
| # | Severity | Section | Issue | Required Action |
```
Format: CRITICAL: [Specific issue]
Must be resolved before approval.

### MAJOR (Priority fixes)
Format: MAJOR: [Issue description]
Significant problems requiring attention.

### MINOR (Quality improvements)
Format: MINOR: [Issue description]
Not blockers, improve if feasible.

### QUESTIONS
Format: QUESTION: [Specific question]
Points requiring clarification from Solution Designer.

## Review Output Format
Return review in response text (Orchestrator captures it). Do NOT create separate review files.

```
=== CRITIC REVIEW - Iteration [N]/5 ===
Started: [YYYY-MM-DD HH:MM:SS]
Document: Solution Design

VERDICT: [APPROVED / CONDITIONAL / REJECTED]

ISSUES TABLE:
| # | Severity | Section | Issue | Required Action |
|---|----------|---------|-------|----------------|
| 1 | CRITICAL | ... | ... | ... |
| 2 | MAJOR | ... | ... | ... |

Total: [N] CRITICAL, [N] MAJOR, [N] MINOR

Completed: [YYYY-MM-DD HH:MM:SS]
=== END CRITIC REVIEW ===
```

## Iteration Tracking
- Reference previous iteration issues as RESOLVED / PERSISTENT
- Track iteration number clearly (N/5)
- Acknowledge improvements made
- Escalate if same issues persist across 2+ iterations

## Research Validation (if research files exist)
If generated_docs_[TIMESTAMP]/research/ has files:
- Read research files
- Validate design against research findings
- Raise MAJOR issue if design contradicts research recommendations
- Reference specific research file in feedback

If no research files exist: skip research validation, use general best practices.
