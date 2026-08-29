#!/usr/bin/env python3
"""
commit_bost.py — Populate your GitHub commit history with N commits.

Usage:
    python commit_bost.py [OPTIONS]

Options:
    -n, --count        Number of commits to create (default: 100)
    -r, --repo         Path to the git repo (default: current directory)
    -f, --file         Name of the text file to update (default: log.txt)
    -m, --message      Commit message prefix (default: "chore: update log")
    --start-date       Earliest date for commits, ISO format YYYY-MM-DD
                       (default: today, commits are spread backwards in time)
    --end-date         Latest date for commits, ISO format YYYY-MM-DD
                       (default: today)
    --push             Push to origin/main after all commits (add --push flag)
    --branch           Branch to push to (default: main)

Examples:
    # 100 commits in the current repo, spread over the past 90 days
    python commit_bost.py -n 100 --start-date 2025-01-01

    # 50 commits in a specific repo, then push
    python commit_bost.py -n 50 -r ~/projects/my-repo --push

    # Custom file name and message
    python commit_bost.py -n 200 -f activity.txt -m "docs: daily update"
"""

import argparse
import os
import random
import subprocess
import sys
from datetime import datetime, timedelta, timezone


# ── helpers ──────────────────────────────────────────────────────────────────

def run(cmd: list[str], cwd: str, env: dict | None = None) -> str:
    """Run a shell command and return stdout; raise on non-zero exit."""
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, env=env
    )
    if result.returncode != 0:
        print(f"[ERROR] Command failed: {' '.join(cmd)}")
        print(result.stderr.strip())
        sys.exit(1)
    return result.stdout.strip()


def random_time(date: datetime) -> datetime:
    """Add a random time-of-day to a date so commits look organic."""
    hour   = random.randint(8, 22)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return date.replace(hour=hour, minute=minute, second=second,
                        tzinfo=timezone.utc)


def spread_dates(start: datetime, end: datetime, n: int) -> list[datetime]:
    """
    Return n datetime objects distributed between start and end.
    Adds a small random offset so the commits don't stack on the same second.
    """
    delta = (end - start).total_seconds()
    if delta < 0:
        print("[ERROR] --start-date must be before --end-date")
        sys.exit(1)

    if n == 1:
        return [random_time(start + timedelta(seconds=delta / 2))]

    timestamps = sorted(
        random_time(start + timedelta(seconds=random.uniform(0, delta)))
        for _ in range(n)
    )
    return timestamps


def make_env(commit_date: datetime) -> dict:
    """Return an env dict that overrides Git's author/committer date."""
    date_str = commit_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"]    = date_str
    env["GIT_COMMITTER_DATE"] = date_str
    return env


ENTRIES = [
    "Reviewed documentation and updated notes.",
    "Refactored internal module structure.",
    "Fixed minor inconsistencies in the codebase.",
    "Improved error handling and logging.",
    "Cleaned up unused variables and imports.",
    "Optimised loop performance.",
    "Added edge-case handling.",
    "Updated configuration defaults.",
    "Synced latest upstream changes.",
    "Resolved merge conflict residues.",
    "Ran linter and applied auto-fixes.",
    "Updated dependency versions.",
    "Wrote additional inline comments.",
    "Reorganised project directory layout.",
    "Validated input sanitisation logic.",
    "Benchmarked critical code paths.",
    "Checked for potential memory leaks.",
    "Reviewed security best practices.",
    "Verified API response schemas.",
    "Polished README and inline docs.",
]


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate N git commits to boost your GitHub activity graph."
    )
    parser.add_argument("-n", "--count",      type=int,  default=100,
                        help="Number of commits (default: 100)")
    parser.add_argument("-r", "--repo",       type=str,  default=".",
                        help="Path to git repo (default: current directory)")
    parser.add_argument("-f", "--file",       type=str,  default="log.txt",
                        help="File to update in each commit (default: log.txt)")
    parser.add_argument("-m", "--message",    type=str,  default="chore: update log",
                        help="Commit message prefix (default: 'chore: update log')")
    parser.add_argument("--start-date",      type=str,  default=None,
                        help="Start date YYYY-MM-DD (default: 90 days before end-date)")
    parser.add_argument("--end-date",        type=str,  default=None,
                        help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--push",            action="store_true",
                        help="Push to remote after all commits")
    parser.add_argument("--branch",          type=str,  default="main",
                        help="Branch to push to (default: main)")
    args = parser.parse_args()

    repo = os.path.abspath(args.repo)
    if not os.path.isdir(os.path.join(repo, ".git")):
        print(f"[ERROR] '{repo}' is not a git repository.")
        print("        Run `git init` inside the target folder first.")
        sys.exit(1)

    # ── date range ────────────────────────────────────────────────────────────
    today = datetime.now(tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_date = (
        datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if args.end_date else today
    )
    start_date = (
        datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if args.start_date else end_date - timedelta(days=90)
    )

    timestamps = spread_dates(start_date, end_date, args.count)
    filepath   = os.path.join(repo, args.file)

    print(f"Repository : {repo}")
    print(f"File       : {args.file}")
    print(f"Commits    : {args.count}")
    print(f"Date range : {start_date.date()} → {end_date.date()}")
    print()

    for i, ts in enumerate(timestamps, start=1):
        # Build / update file content
        entry   = random.choice(ENTRIES)
        line    = f"[{ts.strftime('%Y-%m-%d %H:%M:%S UTC')}] commit {i:>5}/{args.count} — {entry}\n"

        if i == 1:
            with open(filepath, "w") as fh:
                fh.write(f"# Activity log\n# Generated by commit_bost.py\n\n")
                fh.write(line)
        else:
            with open(filepath, "a") as fh:
                fh.write(line)

        env = make_env(ts)
        run(["git", "add", args.file], cwd=repo, env=env)
        msg = f"{args.message} ({i}/{args.count})"
        run(["git", "commit", "-m", msg], cwd=repo, env=env)

        # Progress indicator every 10 commits
        if i % 10 == 0 or i == args.count:
            print(f"  ✓ {i}/{args.count} commits done …")

    print()
    print(f"Done! {args.count} commits created.")

    if args.push:
        print(f"Pushing to origin/{args.branch} …")
        run(["git", "push", "origin", args.branch], cwd=repo)
        print("Pushed successfully.")
    else:
        print(f"Tip: run `git push origin {args.branch}` to sync with GitHub.")


if __name__ == "__main__":
    main()
