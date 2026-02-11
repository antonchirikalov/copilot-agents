---
description: Phase definitions, transition rules, and iteration management for the orchestrator multi-agent workflow.
---

# Workflow Phases

## Phase 1: Research (PARALLEL)
Trigger: Workflow start or mid-workflow research request.

1. Identify ALL research topics from user requirements
2. Launch MULTIPLE researcher subagents IN PARALLEL:
   - Each researcher gets one specific topic and output file path
   - All write to generated_docs_[TIMESTAMP]/research/
3. Wait for ALL researchers to complete
4. Verify all research files created
5. Proceed to Phase 2

Parallel research invocation pattern:
```
Launch 3 researcher subagents IN PARALLEL:
  Subagent 1: Research [Topic 1 with context]. Output: research/[topic1]_research.md
  Subagent 2: Research [Topic 2 with context]. Output: research/[topic2]_research.md
  Subagent 3: Research [Topic 3 with context]. Output: research/[topic3]_research.md
Run all subagents simultaneously and return when all complete.
```

## Phase 2: Initial Design
1. Activate Solution Designer with:
   - User requirements
   - Research folder path: generated_docs_[TIMESTAMP]/research/
   - Output path for Solution Design Document
2. Designer creates Solution Design Document
3. Verify file exists on disk before proceeding
4. Set iteration counter = 1
5. Proceed to Phase 3

If Designer requests additional research mid-design:
- Pause design work
- Execute research (Phase 1 pattern)
- Resume design with new findings

## Phase 3: Iterative Review (max 5 iterations)
1. Submit Solution Design to Critic
2. Receive verdict: APPROVED / CONDITIONAL / REJECTED
3. If NOT APPROVED:
   - Forward Critic feedback to Solution Designer
   - Designer revises Solution Design
   - Verify file updated
   - Increment iteration counter
   - If iteration <= 5: resubmit to Critic (go to step 1)
   - If iteration > 5: report max iterations reached to user
4. If APPROVED: proceed to Phase 4

Mid-phase research: Any agent can request research. Orchestrator pauses, runs research, resumes.

## Phase 4: Delivery
1. Update workflow log with final summary
2. Present to user:
   - Solution Design path
   - All research files list
   - Iteration count summary
   - Workflow log path
3. Suggest: "Invoke DevOps agent with 'deploy' command"
4. YOU MAY NOW FINISH YOUR TURN

## Phase Transitions
```
INIT ──[start]──> RESEARCH
RESEARCH ──[all complete]──> DESIGN
DESIGN ──[doc exists]──> REVIEW
REVIEW ──[APPROVED]──> DELIVERY
REVIEW ──[NOT APPROVED, iter<=5]──> REVIEW (loop)
REVIEW ──[NOT APPROVED, iter>5]──> DELIVERY (with warning)
ANY PHASE ──[research needed]──> RESEARCH ──[complete]──> (resume)
```

## Iteration Management
- Iteration 1: Initial design submission to Critic
- Iterations 2-5: Revisions based on Critic feedback
- Maximum 5 iterations to prevent infinite loops

When submitting revised documents:
- Include iteration number: "Submitting Iteration N/5 for review"
- Remind Critic to reference previous feedback
- Track which issues were addressed vs new issues

## Loop Prevention
Monitor for signs of infinite loop:
- Same issues repeated across multiple iterations
- No measurable progress between iterations
- Iteration count approaching 5

If detected: Alert user "Potential loop detected at iteration N" with summary of persistent issues.

## Completion Rules
DO NOT finish your turn until ALL of:
- Critic returned APPROVED verdict
- Solution Design Document exists and is finalized
- User received final deliverables with paths
- Workflow log updated with final summary

If Critic returns CONDITIONAL or REJECTED:
- AUTOMATICALLY continue to next iteration
- DO NOT ask user "Should I continue?"
- DO NOT wait for user approval between iterations
- Keep working through iterations 1-5
