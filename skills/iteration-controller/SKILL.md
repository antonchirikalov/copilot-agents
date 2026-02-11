---
name: iteration-controller
description: Detects infinite loops and stale iterations in design-review cycles. Compares Critic feedback across iterations to find repeated issues. Use when managing iterative review workflows to prevent wasted cycles on unresolvable issues.
---

# Iteration Controller

## When to use
- After receiving Critic verdict in iteration 2+
- When suspecting the design-review cycle is stuck
- Before submitting for another review iteration
- When iteration count approaches maximum (5)

## How to use

### Check for loops after a Critic review
```bash
python3 .github/skills/iteration-controller/scripts/loop-detector.py check --folder generated_docs_[TIMESTAMP]
```

The script reads `workflow_state.json` history and compares Critic issues across iterations.

### Output
```json
{
  "iteration": 3,
  "max_iterations": 5,
  "loop_detected": true,
  "repeated_issues": ["Missing monitoring section", "Diagram uses C4 syntax"],
  "progress_score": 0.3,
  "recommendation": "ESCALATE - same 2 issues persist across 2+ iterations"
}
```

### Interpret results
- `loop_detected: false` + `progress_score > 0.5` → Continue normally
- `loop_detected: false` + `progress_score < 0.5` → Progress slow, consider targeted fixes
- `loop_detected: true` → Alert user, show persistent issues, ask for guidance

## How it works
1. Reads all Critic verdicts from workflow_state.json history
2. Extracts issue descriptions from each iteration
3. Compares issues using fuzzy string matching
4. Calculates progress_score = (resolved / total) across iterations
5. Flags loop if same issues appear in 2+ consecutive iterations
