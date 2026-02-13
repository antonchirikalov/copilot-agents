#!/usr/bin/env python3
"""
task-planner.py — Manages TASKS.md for the Coder agent.

Modes:
  --input "text"          Parse text and generate TASKS.md skeleton
  --file path.md          Parse document and generate TASKS.md skeleton
  --existing TASKS.md     Work with existing TASKS.md
    --status              Print progress summary
    --complete N          Mark task N as completed
    --progress N          Mark task N as in_progress
    --add "description"   Add a new task

Usage:
    python3 task-planner.py --input "Add user authentication with JWT"
    python3 task-planner.py --existing TASKS.md --status
    python3 task-planner.py --existing TASKS.md --complete 3
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path


TEMPLATE = """# Tasks: {title}

**Source:** {source}
**Generated:** {timestamp}
**Status:** planning

## Context

{context}

## Tasks

{tasks}

## Test Coverage

| Module | Tests | Pass | Fail |
|--------|-------|------|------|
| — | — | — | — |

## Log

- {time} — NOTE: TASKS.md generated from {source_type}
"""

TASK_PATTERN = re.compile(
    r'^- \[([x \-])\] (🔲|🔄|✅|❌) \[([SML])\] (.+)$',
    re.MULTILINE
)

STATUS_MAP = {
    ' ': ('🔲', 'not_started'),
    '-': ('🔄', 'in_progress'),
    'x': ('✅', 'completed'),
}

EMOJI_TO_STATUS = {
    '🔲': 'not_started',
    '🔄': 'in_progress',
    '✅': 'completed',
    '❌': 'failed',
}


def generate_skeleton(text: str, source: str = "user input") -> str:
    """Generate a TASKS.md skeleton from free-form text."""
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]

    title = lines[0][:60] if lines else "Untitled Task"
    context = text.strip()[:300]

    # Generate placeholder tasks
    tasks_lines = []
    for i, line in enumerate(lines[:15], 1):
        # Clean up the line for task description
        clean = line.lstrip('0123456789.-) ').strip()
        if clean:
            tasks_lines.append(f"- [ ] 🔲 [M] {clean}")

    if not tasks_lines:
        tasks_lines = [
            "- [ ] 🔲 [M] Analyze requirements and existing code",
            "- [ ] 🔲 [M] Implement core logic",
            "- [ ] 🔲 [M] Add error handling",
            "- [ ] 🔲 [S] Write tests",
            "- [ ] 🔲 [S] Run lint and type checks",
        ]

    now = datetime.now()
    return TEMPLATE.format(
        title=title,
        source=source,
        timestamp=now.strftime("%Y-%m-%d %H:%M"),
        context=context,
        tasks='\n'.join(tasks_lines),
        time=now.strftime("%H:%M"),
        source_type=source,
    )


def parse_tasks(content: str) -> list[dict]:
    """Parse tasks from TASKS.md content."""
    tasks = []
    for i, match in enumerate(TASK_PATTERN.finditer(content), 1):
        checkbox, emoji, size, description = match.groups()
        tasks.append({
            'number': i,
            'status': EMOJI_TO_STATUS.get(emoji, 'unknown'),
            'size': size,
            'description': description,
            'raw': match.group(0),
        })
    return tasks


def print_status(content: str) -> None:
    """Print progress summary from TASKS.md."""
    tasks = parse_tasks(content)
    if not tasks:
        print("No tasks found in TASKS.md")
        return

    total = len(tasks)
    completed = sum(1 for t in tasks if t['status'] == 'completed')
    in_progress = sum(1 for t in tasks if t['status'] == 'in_progress')
    failed = sum(1 for t in tasks if t['status'] == 'failed')
    not_started = sum(1 for t in tasks if t['status'] == 'not_started')

    pct = (completed / total) * 100 if total else 0

    print(f"Progress: {completed}/{total} ({pct:.0f}%)")
    print(f"  ✅ Completed:   {completed}")
    print(f"  🔄 In progress: {in_progress}")
    print(f"  🔲 Not started: {not_started}")
    if failed:
        print(f"  ❌ Failed:      {failed}")
    print()

    for t in tasks:
        emoji = {'not_started': '🔲', 'in_progress': '🔄', 'completed': '✅', 'failed': '❌'}.get(t['status'], '?')
        print(f"  {t['number']}. {emoji} [{t['size']}] {t['description']}")


def update_task_status(content: str, task_num: int, new_status: str) -> str:
    """Update a task's status in TASKS.md content."""
    tasks = parse_tasks(content)

    target = None
    for t in tasks:
        if t['number'] == task_num:
            target = t
            break

    if not target:
        print(f"Error: Task {task_num} not found (total: {len(tasks)})", file=sys.stderr)
        sys.exit(1)

    status_symbols = {
        'completed': ('[x]', '✅'),
        'in_progress': ('[-]', '🔄'),
        'not_started': ('[ ]', '🔲'),
        'failed': ('[x]', '❌'),
    }

    checkbox, emoji = status_symbols.get(new_status, ('[ ]', '🔲'))
    old_line = target['raw']
    new_line = f"- {checkbox} {emoji} [{target['size']}] {target['description']}"

    updated = content.replace(old_line, new_line, 1)

    # Add log entry
    time_str = datetime.now().strftime("%H:%M")
    event = 'DONE' if new_status == 'completed' else 'START' if new_status == 'in_progress' else 'NOTE'
    log_entry = f"- {time_str} — {event}: Task {task_num} — {target['description']}"
    updated = updated.rstrip() + f"\n{log_entry}\n"

    return updated


def add_task(content: str, description: str, size: str = "M") -> str:
    """Add a new task to TASKS.md."""
    new_task = f"- [ ] 🔲 [{size}] {description}"

    # Find last task line and insert after it
    lines = content.split('\n')
    last_task_idx = -1
    for i, line in enumerate(lines):
        if TASK_PATTERN.match(line):
            last_task_idx = i

    if last_task_idx >= 0:
        lines.insert(last_task_idx + 1, new_task)
    else:
        # No tasks found, add after ## Tasks header
        for i, line in enumerate(lines):
            if line.strip() == '## Tasks':
                lines.insert(i + 2, new_task)
                break

    updated = '\n'.join(lines)

    time_str = datetime.now().strftime("%H:%M")
    log_entry = f"- {time_str} — NOTE: Added task — {description}"
    updated = updated.rstrip() + f"\n{log_entry}\n"

    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage TASKS.md for Coder agent")
    parser.add_argument('--input', '-i', help='Text description to generate TASKS.md from')
    parser.add_argument('--file', '-f', help='Document file to parse for task generation')
    parser.add_argument('--output', '-o', default='TASKS.md', help='Output file path')
    parser.add_argument('--existing', '-e', help='Path to existing TASKS.md')
    parser.add_argument('--status', '-s', action='store_true', help='Print progress status')
    parser.add_argument('--complete', '-c', type=int, help='Mark task N as completed')
    parser.add_argument('--progress', '-p', type=int, help='Mark task N as in_progress')
    parser.add_argument('--add', '-a', help='Add a new task')
    parser.add_argument('--size', default='M', choices=['S', 'M', 'L'], help='Size for --add')
    args = parser.parse_args()

    # Generate mode
    if args.input:
        content = generate_skeleton(args.input, source="user input")
        Path(args.output).write_text(content, encoding='utf-8')
        print(f"Generated: {args.output}")
        return

    if args.file:
        try:
            doc_text = Path(args.file).read_text(encoding='utf-8')
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        content = generate_skeleton(doc_text, source=args.file)
        Path(args.output).write_text(content, encoding='utf-8')
        print(f"Generated: {args.output}")
        return

    # Existing mode
    if args.existing:
        try:
            content = Path(args.existing).read_text(encoding='utf-8')
        except FileNotFoundError:
            print(f"Error: File not found: {args.existing}", file=sys.stderr)
            sys.exit(1)

        if args.status:
            print_status(content)
            return

        if args.complete:
            updated = update_task_status(content, args.complete, 'completed')
            Path(args.existing).write_text(updated, encoding='utf-8')
            print(f"Task {args.complete} marked as completed")
            return

        if args.progress:
            updated = update_task_status(content, args.progress, 'in_progress')
            Path(args.existing).write_text(updated, encoding='utf-8')
            print(f"Task {args.progress} marked as in_progress")
            return

        if args.add:
            updated = add_task(content, args.add, args.size)
            Path(args.existing).write_text(updated, encoding='utf-8')
            print(f"Added task: {args.add}")
            return

        # Default: print status
        print_status(content)
        return

    parser.print_help()


if __name__ == '__main__':
    main()
