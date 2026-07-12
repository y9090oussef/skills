#!/usr/bin/env python3
"""Check changed Git files against explicit phase allow/forbid globs.

The script is read-only. It checks tracked working-tree/staged changes and,
optionally, untracked files. Globs use pathlib-style matching.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path


class ScopeError(RuntimeError):
    pass


def run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ScopeError(
            f"git {' '.join(args)} failed with {result.returncode}: {result.stderr.strip()}"
        )
    return result.stdout


def normalise(path: str) -> str:
    return path.strip().replace("\\", "/")


def matches(path: str, patterns: list[str]) -> bool:
    path_obj = Path(path)
    for pattern in patterns:
        pattern = normalise(pattern)
        if fnmatch.fnmatchcase(path, pattern) or path_obj.match(pattern):
            return True
    return False


def collect_changes(repo_root: Path, include_untracked: bool) -> list[str]:
    changed = set()
    for args in (("diff", "--name-only"), ("diff", "--cached", "--name-only")):
        for line in run_git(repo_root, *args).splitlines():
            if line.strip():
                changed.add(normalise(line))
    if include_untracked:
        for line in run_git(repo_root, "ls-files", "--others", "--exclude-standard").splitlines():
            if line.strip():
                changed.add(normalise(line))
    return sorted(changed)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--allow", action="append", default=[], help="Allowed glob; repeatable")
    parser.add_argument("--forbid", action="append", default=[], help="Forbidden glob; repeatable")
    parser.add_argument("--no-untracked", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    try:
        top_level = Path(run_git(repo_root, "rev-parse", "--show-toplevel").strip()).resolve()
        if top_level != repo_root:
            repo_root = top_level
        changed = collect_changes(repo_root, include_untracked=not args.no_untracked)
        forbidden = [path for path in changed if matches(path, args.forbid)]
        outside_allow = [
            path for path in changed if args.allow and not matches(path, args.allow)
        ]
        violations = sorted(set(forbidden + outside_allow))
        result = {
            "status": "PASS" if not violations else "BLOCKED",
            "repo_root": str(repo_root),
            "changed": changed,
            "forbidden_matches": forbidden,
            "outside_allowlist": outside_allow,
            "violations": violations,
        }
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"changed_files={len(changed)}")
            for path in changed:
                print(f"  {path}")
            if violations:
                print("BLOCKED: phase scope violations:", file=sys.stderr)
                for path in violations:
                    print(f"  {path}", file=sys.stderr)
            else:
                print("PASS: all changed files satisfy the supplied phase scope")
        return 0 if not violations else 4
    except ScopeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
