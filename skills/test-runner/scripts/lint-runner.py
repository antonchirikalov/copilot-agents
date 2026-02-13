#!/usr/bin/env python3
"""
lint-runner.py — Run ruff and mypy, output structured JSON results.

Usage:
    python3 lint-runner.py /path/to/project [--fix]

Output: JSON summary to stdout.
"""

import argparse
import json
import os
import re
import subprocess
import sys


def run_ruff(project_path: str, fix: bool = False) -> dict:
    """Run ruff check and parse output."""
    cmd = ["python", "-m", "ruff", "check"]
    if fix:
        cmd.append("--fix")
    cmd.append(".")

    try:
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"tool": "ruff", "status": "error", "message": str(e), "issues": []}

    issues = []
    # Parse ruff output: "app/main.py:10:5: E501 Line too long"
    pattern = re.compile(r'^(.+?):(\d+):(\d+): (\w+) (.+)$', re.MULTILINE)
    for match in pattern.finditer(result.stdout):
        issues.append({
            "file": match.group(1),
            "line": int(match.group(2)),
            "col": int(match.group(3)),
            "code": match.group(4),
            "message": match.group(5),
        })

    return {
        "tool": "ruff",
        "status": "pass" if result.returncode == 0 else "fail",
        "issue_count": len(issues),
        "issues": issues[:50],  # Limit to first 50
        "fixed": fix and result.returncode == 0,
    }


def run_mypy(project_path: str) -> dict:
    """Run mypy and parse output."""
    cmd = ["python", "-m", "mypy", "."]

    try:
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"tool": "mypy", "status": "error", "message": str(e), "issues": []}

    issues = []
    # Parse mypy output: "app/main.py:10: error: Incompatible types [assignment]"
    pattern = re.compile(r'^(.+?):(\d+): (error|warning|note): (.+?)(?:\s+\[(.+?)\])?$', re.MULTILINE)
    for match in pattern.finditer(result.stdout):
        issues.append({
            "file": match.group(1),
            "line": int(match.group(2)),
            "severity": match.group(3),
            "message": match.group(4),
            "code": match.group(5) or "",
        })

    # Parse summary: "Found 5 errors in 3 files"
    error_count = 0
    summary_match = re.search(r'Found (\d+) error', result.stdout)
    if summary_match:
        error_count = int(summary_match.group(1))

    return {
        "tool": "mypy",
        "status": "pass" if result.returncode == 0 else "fail",
        "error_count": error_count,
        "issues": issues[:50],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ruff + mypy and output JSON results")
    parser.add_argument("project_path", help="Path to the project root")
    parser.add_argument("--fix", action="store_true", help="Auto-fix ruff issues")
    args = parser.parse_args()

    if not os.path.isdir(args.project_path):
        print(json.dumps({"status": "error", "message": f"Not a directory: {args.project_path}"}))
        sys.exit(1)

    ruff_result = run_ruff(args.project_path, args.fix)
    mypy_result = run_mypy(args.project_path)

    combined = {
        "status": "pass" if ruff_result["status"] == "pass" and mypy_result["status"] == "pass" else "fail",
        "ruff": ruff_result,
        "mypy": mypy_result,
    }

    print(json.dumps(combined, indent=2))
    sys.exit(0 if combined["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
