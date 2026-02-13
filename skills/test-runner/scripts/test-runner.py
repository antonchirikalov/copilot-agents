#!/usr/bin/env python3
"""
test-runner.py — Run pytest and output structured JSON results.

Usage:
    python3 test-runner.py /path/to/project [--tests tests/] [--markers unit]

Output: JSON summary to stdout.
"""

import argparse
import json
import os
import re
import subprocess
import sys


def run_pytest(project_path: str, test_dir: str = "tests", markers: str | None = None) -> dict:
    """Run pytest and parse output into structured result."""
    cmd = ["python", "-m", "pytest", "--tb=short", "-q"]

    if markers:
        cmd.extend(["-m", markers])

    cmd.append(test_dir)

    try:
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "message": "pytest timed out after 300 seconds",
            "total": 0, "passed": 0, "failed": 0, "errors": [],
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "pytest not found — install with: pip install pytest",
            "total": 0, "passed": 0, "failed": 0, "errors": [],
        }

    output = result.stdout + result.stderr
    return parse_pytest_output(output, result.returncode)


def parse_pytest_output(output: str, returncode: int) -> dict:
    """Parse pytest text output into structured dict."""
    result = {
        "status": "pass" if returncode == 0 else "fail",
        "returncode": returncode,
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "failures": [],
        "error_details": [],
    }

    # Parse summary line: "24 passed, 2 failed, 1 error in 3.45s"
    summary_match = re.search(
        r'(\d+) passed'
        r'(?:, (\d+) failed)?'
        r'(?:, (\d+) error)?'
        r'(?:, (\d+) skipped)?',
        output
    )
    if summary_match:
        result["passed"] = int(summary_match.group(1) or 0)
        result["failed"] = int(summary_match.group(2) or 0)
        result["errors"] = int(summary_match.group(3) or 0)
        result["skipped"] = int(summary_match.group(4) or 0)
        result["total"] = result["passed"] + result["failed"] + result["errors"]

    # Also check for "N failed" without passed
    if not summary_match:
        failed_only = re.search(r'(\d+) failed', output)
        if failed_only:
            result["failed"] = int(failed_only.group(1))
            result["total"] = result["failed"]

    # Parse individual failures: "FAILED tests/test_x.py::test_name - reason"
    failure_pattern = re.compile(r'FAILED\s+(.+?)::(.+?)(?:\s+-\s+(.+))?$', re.MULTILINE)
    for match in failure_pattern.finditer(output):
        result["failures"].append({
            "file": match.group(1),
            "test": match.group(2),
            "message": (match.group(3) or "").strip(),
        })

    # Parse ERROR lines
    error_pattern = re.compile(r'ERROR\s+(.+?)(?:\s+-\s+(.+))?$', re.MULTILINE)
    for match in error_pattern.finditer(output):
        result["error_details"].append({
            "location": match.group(1),
            "message": (match.group(2) or "").strip(),
        })

    # Include raw output for debugging (truncated)
    result["raw_output"] = output[-2000:] if len(output) > 2000 else output

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pytest and output JSON results")
    parser.add_argument("project_path", help="Path to the project root")
    parser.add_argument("--tests", default="tests", help="Test directory (default: tests)")
    parser.add_argument("--markers", "-m", help="pytest markers to filter (e.g., 'unit')")
    args = parser.parse_args()

    if not os.path.isdir(args.project_path):
        print(json.dumps({"status": "error", "message": f"Not a directory: {args.project_path}"}))
        sys.exit(1)

    result = run_pytest(args.project_path, args.tests, args.markers)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
