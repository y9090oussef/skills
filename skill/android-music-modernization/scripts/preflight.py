#!/usr/bin/env python3
"""Validate the intended Android project and its project-local Revision 10 phase gate."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_FLAVORS = ("mahrgnat", "faresSokar", "eslamKabonga")
PACK_CANDIDATES = (
    Path(".agent/android-modernization"),
    Path("docs/android-modernization"),
    Path("android_modernization_agent_pack_revision_10"),
)


def run_git(repo: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def find_repo(start: Path) -> Path:
    start = start.resolve()
    top = run_git(start, "rev-parse", "--show-toplevel")
    if top:
        return Path(top).resolve()
    for current in (start, *start.parents):
        if (current / "settings.gradle").exists() or (current / "settings.gradle.kts").exists():
            return current
    return start


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"null", "~", ""}:
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if (value.startswith("'") and value.endswith("'")) or (
        value.startswith('"') and value.endswith('"')
    ):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def parse_top_level_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line or raw_line.startswith((" ", "\t", "#", "-")):
            continue
        match = re.match(r"^([A-Za-z0-9_]+):(?:\s*(.*))?$", raw_line)
        if match:
            data[match.group(1)] = parse_scalar(match.group(2) or "")
    return data


def locate_pack(repo: Path, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).expanduser().resolve()
    for relative in PACK_CANDIDATES:
        path = repo / relative
        if (path / "project_state.yaml").is_file():
            return path
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--pack")
    parser.add_argument("--require-phase", choices=[f"P{i:02d}" for i in range(20)])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = find_repo(Path(args.repo))
    errors: list[str] = []
    warnings: list[str] = []

    marker_groups = [
        ("settings.gradle", "settings.gradle.kts"),
        ("app/build.gradle", "app/build.gradle.kts"),
        ("gradle/libs.versions.toml",),
        ("app/src/main/AndroidManifest.xml",),
    ]
    for group in marker_groups:
        if not any((repo / item).is_file() for item in group):
            errors.append("missing project marker: " + " or ".join(group))

    build_file = repo / "app/build.gradle"
    if not build_file.is_file():
        build_file = repo / "app/build.gradle.kts"
    if build_file.is_file():
        text = build_file.read_text(encoding="utf-8", errors="replace")
        missing = [flavor for flavor in EXPECTED_FLAVORS if flavor not in text]
        if missing:
            errors.append("missing expected product flavor(s): " + ", ".join(missing))

    pack = locate_pack(repo, args.pack)
    state: dict[str, Any] = {}
    if pack is None:
        errors.append(
            "project-local Revision 10 Agent Pack is not installed; run install_agent_pack.py"
        )
    else:
        state_path = pack / "project_state.yaml"
        if not state_path.is_file():
            errors.append(f"project_state.yaml not found in Agent Pack: {pack}")
        else:
            state = parse_top_level_yaml(state_path)
            if state.get("pack_revision") != 10:
                errors.append(f"expected pack_revision 10, found {state.get('pack_revision')!r}")

    phase = args.require_phase
    if phase and pack is not None:
        expected_action = f"execute_{phase}_only"
        if state.get("plan_approved") is not True:
            errors.append("plan_approved is not true")
        if state.get("approved_phase") != phase:
            errors.append(f"approved_phase is {state.get('approved_phase')!r}, required {phase!r}")
        if state.get("next_allowed_action") != expected_action:
            errors.append(
                f"next_allowed_action is {state.get('next_allowed_action')!r}, required {expected_action!r}"
            )
        prompt_count = len(list((pack / "phase_prompts").glob(f"{phase}_*.md")))
        if prompt_count != 1:
            errors.append(f"expected exactly one phase prompt for {phase}, found {prompt_count}")

    if not phase and pack is not None and state.get("plan_approved") is not True:
        warnings.append("Agent Pack is installed in owner-review mode; production execution is blocked")

    result = {
        "repository": str(repo),
        "agent_pack": str(pack) if pack else None,
        "required_phase": phase,
        "state": {
            key: state.get(key)
            for key in (
                "pack_revision",
                "plan_approved",
                "approved_phase",
                "implementation_status",
                "current_phase",
                "next_allowed_action",
            )
        },
        "errors": errors,
        "warnings": warnings,
        "status": "OK" if not errors else "PRECONDITION_FAILED",
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status: {result['status']}")
        print(f"repository: {repo}")
        print(f"agent_pack: {result['agent_pack']}")
        for warning in warnings:
            print(f"warning: {warning}")
        for error in errors:
            print(f"error: {error}", file=sys.stderr)

    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
