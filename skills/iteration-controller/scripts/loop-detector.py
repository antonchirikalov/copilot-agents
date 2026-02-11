#!/usr/bin/env python3
"""Loop detector for design-review iteration cycles.

Analyzes workflow state history to detect repeated issues
across Critic review iterations and prevent infinite loops.
"""

import argparse
import json
import os
import re
import sys
from difflib import SequenceMatcher


def load_state(folder: str) -> dict:
    path = os.path.join(folder, "workflow_state.json")
    if not os.path.exists(path):
        print(f"Error: No state file at {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, "r") as f:
        return json.load(f)


def extract_issues_from_history(history: list) -> dict:
    """Extract Critic issues from history events, grouped by iteration."""
    iterations = {}
    current_iteration = 0
    for entry in history:
        event = entry.get("event", "")
        # Track iteration increments
        iter_match = re.search(r"Iteration incremented to (\d+)", event)
        if iter_match:
            current_iteration = int(iter_match.group(1))
        # Track verdicts (they contain implicit iteration info)
        verdict_match = re.search(r"Verdict set: (APPROVED|CONDITIONAL|REJECTED)", event)
        if verdict_match and current_iteration > 0:
            if current_iteration not in iterations:
                iterations[current_iteration] = {
                    "verdict": verdict_match.group(1),
                    "issues": []
                }
            else:
                iterations[current_iteration]["verdict"] = verdict_match.group(1)
        # Track issues if logged
        issue_match = re.search(r"Issue: (.+)", event)
        if issue_match and current_iteration > 0:
            if current_iteration not in iterations:
                iterations[current_iteration] = {"verdict": None, "issues": []}
            iterations[current_iteration]["issues"].append(issue_match.group(1))
    return iterations


def similarity(a: str, b: str) -> float:
    """Calculate string similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_repeated_issues(iterations: dict, threshold: float = 0.7) -> list:
    """Find issues that appear in 2+ consecutive iterations."""
    repeated = []
    sorted_iters = sorted(iterations.keys())
    if len(sorted_iters) < 2:
        return []
    for i in range(1, len(sorted_iters)):
        prev_issues = iterations[sorted_iters[i - 1]].get("issues", [])
        curr_issues = iterations[sorted_iters[i]].get("issues", [])
        for curr in curr_issues:
            for prev in prev_issues:
                if similarity(curr, prev) >= threshold:
                    if curr not in repeated:
                        repeated.append(curr)
    return repeated


def calculate_progress(iterations: dict) -> float:
    """Calculate progress score based on issue resolution across iterations."""
    sorted_iters = sorted(iterations.keys())
    if len(sorted_iters) < 2:
        return 1.0  # First iteration, full progress assumed
    first_count = len(iterations[sorted_iters[0]].get("issues", []))
    last_count = len(iterations[sorted_iters[-1]].get("issues", []))
    if first_count == 0:
        return 1.0
    resolved = max(0, first_count - last_count)
    return round(resolved / first_count, 2)


def cmd_check(args):
    state = load_state(args.folder)
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 5)
    history = state.get("history", [])
    iterations = extract_issues_from_history(history)
    repeated = find_repeated_issues(iterations)
    progress = calculate_progress(iterations)
    loop_detected = len(repeated) > 0 and iteration >= 2
    if loop_detected:
        recommendation = f"ESCALATE - {len(repeated)} issue(s) persist across iterations"
    elif iteration >= max_iterations - 1:
        recommendation = "WARNING - approaching max iterations, prioritize critical fixes"
    elif progress < 0.5 and iteration >= 2:
        recommendation = "SLOW PROGRESS - consider targeted fixes for remaining issues"
    else:
        recommendation = "CONTINUE - normal progress"
    result = {
        "iteration": iteration,
        "max_iterations": max_iterations,
        "loop_detected": loop_detected,
        "repeated_issues": repeated,
        "progress_score": progress,
        "recommendation": recommendation
    }
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Design-review loop detector")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_check = subparsers.add_parser("check", help="Check for iteration loops")
    p_check.add_argument("--folder", required=True, help="Path to generated_docs folder")
    p_check.set_defaults(func=cmd_check)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
