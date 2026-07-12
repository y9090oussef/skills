#!/usr/bin/env python3
"""Check that an Android modernization phase report contains the required evidence sections."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_GROUPS = {
    "scope": ("approved phase", "scope"),
    "files read": ("files read",),
    "files changed": ("files changed", "files created", "files deleted"),
    "official documentation": ("official", "documentation", "sources"),
    "commands and exit codes": ("commands", "exit code"),
    "tests": ("tests", "test results"),
    "flavors": ("mahrgnat", "faressokar", "eslamkabonga"),
    "behavior evidence": ("behavior", "parity"),
    "risks and unknowns": ("risks", "unknowns", "blockers"),
    "git evidence": ("git diff", "git status"),
    "rollback": ("rollback",),
    "final status": ("ready for review", "blocked", "failed", "rolled back", "failed rolled back", "precondition failed"),
}


def normalise(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[`*_#:\-]+", " ", text)
    return re.sub(r"\s+", " ", text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report")
    args = parser.parse_args()

    path = Path(args.report)
    if not path.is_file():
        print(f"error: report not found: {path}")
        return 2

    text = normalise(path.read_text(encoding="utf-8", errors="replace"))
    missing: list[str] = []

    for label, alternatives in REQUIRED_GROUPS.items():
        if label == "flavors":
            if not all(term in text for term in alternatives):
                missing.append(label)
        elif not any(term in text for term in alternatives):
            missing.append(label)

    if missing:
        print("status: INVALID_REPORT")
        for item in missing:
            print(f"missing: {item}")
        return 3

    print("status: VALID_REPORT_STRUCTURE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
