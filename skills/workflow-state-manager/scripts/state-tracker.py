#!/usr/bin/env python3
"""Workflow state tracker for multi-agent design workflows.

Manages workflow_state.json in the generated_docs folder.
Tracks phase, iteration, verdict, and document status.
"""

import argparse
import json
import os
import sys
from datetime import datetime


def get_state_path(folder: str) -> str:
    return os.path.join(folder, "workflow_state.json")


def load_state(folder: str) -> dict:
    path = get_state_path(folder)
    if not os.path.exists(path):
        print(f"Error: No state file found at {path}", file=sys.stderr)
        print("Run 'init' first to create workflow state.", file=sys.stderr)
        sys.exit(1)
    with open(path, "r") as f:
        return json.load(f)


def save_state(folder: str, state: dict) -> None:
    path = get_state_path(folder)
    with open(path, "w") as f:
        json.dump(state, f, indent=2, default=str)
    print(f"State saved: {path}")


def add_history(state: dict, event: str) -> None:
    state["history"].append({
        "timestamp": datetime.now().isoformat(),
        "event": event
    })


def cmd_init(args):
    folder = args.folder
    os.makedirs(folder, exist_ok=True)
    state = {
        "project": args.project or os.path.basename(folder),
        "started": datetime.now().isoformat(),
        "phase": "research",
        "iteration": 0,
        "max_iterations": 5,
        "verdict": None,
        "documents": {
            "solution_design": "not_started"
        },
        "research_files": [],
        "history": []
    }
    add_history(state, "Workflow initialized")
    save_state(folder, state)
    print(json.dumps(state, indent=2, default=str))


def cmd_set_phase(args):
    valid_phases = ["research", "design", "review", "delivery"]
    if args.phase not in valid_phases:
        print(f"Error: Invalid phase '{args.phase}'. Must be one of: {valid_phases}", file=sys.stderr)
        sys.exit(1)
    state = load_state(args.folder)
    old_phase = state["phase"]
    state["phase"] = args.phase
    add_history(state, f"Phase changed: {old_phase} -> {args.phase}")
    save_state(args.folder, state)
    print(f"Phase: {old_phase} -> {args.phase}")


def cmd_increment_iteration(args):
    state = load_state(args.folder)
    state["iteration"] += 1
    iteration = state["iteration"]
    max_iter = state["max_iterations"]
    add_history(state, f"Iteration incremented to {iteration}/{max_iter}")
    save_state(args.folder, state)
    print(f"Iteration: {iteration}/{max_iter}")
    if iteration >= max_iter:
        print(f"WARNING: Max iterations ({max_iter}) reached!", file=sys.stderr)


def cmd_set_verdict(args):
    valid_verdicts = ["APPROVED", "CONDITIONAL", "REJECTED"]
    if args.verdict not in valid_verdicts:
        print(f"Error: Invalid verdict '{args.verdict}'. Must be one of: {valid_verdicts}", file=sys.stderr)
        sys.exit(1)
    state = load_state(args.folder)
    state["verdict"] = args.verdict
    if args.verdict == "APPROVED":
        state["documents"]["solution_design"] = "approved"
    elif args.verdict in ("CONDITIONAL", "REJECTED"):
        state["documents"]["solution_design"] = "in_review"
    add_history(state, f"Verdict set: {args.verdict}")
    save_state(args.folder, state)
    print(f"Verdict: {args.verdict}")


def cmd_add_research(args):
    state = load_state(args.folder)
    if args.file not in state["research_files"]:
        state["research_files"].append(args.file)
    add_history(state, f"Research file added: {args.file}")
    save_state(args.folder, state)
    print(f"Research files: {state['research_files']}")


def cmd_status(args):
    state = load_state(args.folder)
    print(json.dumps(state, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="Workflow state tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", help="Initialize workflow state")
    p_init.add_argument("--folder", required=True, help="Path to generated_docs folder")
    p_init.add_argument("--project", help="Project name")
    p_init.set_defaults(func=cmd_init)

    # set-phase
    p_phase = subparsers.add_parser("set-phase", help="Set current workflow phase")
    p_phase.add_argument("--folder", required=True, help="Path to generated_docs folder")
    p_phase.add_argument("--phase", required=True, help="Phase: research|design|review|delivery")
    p_phase.set_defaults(func=cmd_set_phase)

    # increment-iteration
    p_iter = subparsers.add_parser("increment-iteration", help="Increment iteration counter")
    p_iter.add_argument("--folder", required=True, help="Path to generated_docs folder")
    p_iter.set_defaults(func=cmd_increment_iteration)

    # set-verdict
    p_verdict = subparsers.add_parser("set-verdict", help="Set Critic verdict")
    p_verdict.add_argument("--folder", required=True, help="Path to generated_docs folder")
    p_verdict.add_argument("--verdict", required=True, help="Verdict: APPROVED|CONDITIONAL|REJECTED")
    p_verdict.set_defaults(func=cmd_set_verdict)

    # add-research
    p_research = subparsers.add_parser("add-research", help="Register a research file")
    p_research.add_argument("--folder", required=True, help="Path to generated_docs folder")
    p_research.add_argument("--file", required=True, help="Research file path")
    p_research.set_defaults(func=cmd_add_research)

    # status
    p_status = subparsers.add_parser("status", help="Show current workflow state")
    p_status.add_argument("--folder", required=True, help="Path to generated_docs folder")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
