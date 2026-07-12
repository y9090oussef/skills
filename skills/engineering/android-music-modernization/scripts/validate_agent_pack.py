#!/usr/bin/env python3
"""Validate the Revision 10 Android modernization Agent Pack and execution gate.

This script is read-only and uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

REQUIRED_FILES = (
    "00_START_HERE.md",
    "01_MASTER_PLAN_REVISION_10.md",
    "02_TASKS_AND_CHECKPOINTS.md",
    "03_TARGET_ARCHITECTURE.md",
    "04_PROPOSED_PROJECT_STRUCTURE.md",
    "05_BUILD_TEST_RELEASE_MATRIX.md",
    "06_FUNCTIONAL_PARITY_CHECKLIST.md",
    "07_DEPENDENCY_TOOLCHAIN_MATRIX.md",
    "08_AGENT_EXECUTION_PROTOCOL.md",
    "09_RISKS_DECISIONS_ROLLBACK.md",
    "10_FILE_CHANGE_MAP.md",
    "11_PHASE_REPORT_TEMPLATE.md",
    "12_OFFICIAL_REFERENCE_INDEX.md",
    "13_CURRENT_CODEBASE_AUDIT.md",
    "14_PROGRESS_LEDGER.md",
    "15_OWNER_DECISIONS.md",
    "agent_context.yaml",
    "tasks.yaml",
    "decisions.yaml",
    "project_state.yaml",
)

EXCLUDED_DIRS = {".git", ".gradle", ".idea", "build", "node_modules", "out", "dist"}
MUTABLE_CHECKSUM_FILES = {"project_state.yaml", "tasks.yaml", "14_PROGRESS_LEDGER.md"}
PHASE_RE = re.compile(r"^P(?:0[0-9]|1[0-9])$")


class ValidationError(RuntimeError):
    pass


def normalize_scalar(value: str):
    value = value.strip()
    if not value:
        return ""
    if value[0:1] in {"'", '"'} and value[-1:] == value[0:1]:
        value = value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none", "~"}:
        return None
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def read_top_level_scalars(path: Path) -> dict[str, object]:
    result: dict[str, object] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line or raw_line[0].isspace() or raw_line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(?:\s*(.*))?$", raw_line)
        if match:
            result[match.group(1)] = normalize_scalar(match.group(2) or "")
    return result


def is_pack_root(path: Path) -> bool:
    return all((path / name).is_file() for name in REQUIRED_FILES) and (path / "phase_prompts").is_dir()


def discover_pack_roots(repo_root: Path, max_depth: int = 4) -> list[Path]:
    candidates: list[Path] = []
    if is_pack_root(repo_root):
        candidates.append(repo_root)

    root_depth = len(repo_root.parts)
    for current, dirs, files in os.walk(repo_root):
        current_path = Path(current)
        depth = len(current_path.parts) - root_depth
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".")]
        if depth >= max_depth:
            dirs[:] = []
        if "project_state.yaml" in files and "01_MASTER_PLAN_REVISION_10.md" in files:
            if is_pack_root(current_path) and current_path not in candidates:
                candidates.append(current_path)
    return sorted(candidates)


def verify_required_files(pack_root: Path) -> None:
    missing = [name for name in REQUIRED_FILES if not (pack_root / name).is_file()]
    if not (pack_root / "phase_prompts").is_dir():
        missing.append("phase_prompts/")
    if missing:
        raise ValidationError("missing required pack entries: " + ", ".join(missing))


def verify_checksums(pack_root: Path) -> dict[str, object]:
    checksum_file = pack_root / "checksums.sha256"
    if not checksum_file.is_file():
        return {"status": "NOT_EXECUTED", "reason": "checksums.sha256 is absent"}

    checked = 0
    skipped = []
    failures = []
    line_re = re.compile(r"^([0-9a-fA-F]{64})\s+\.?/?(.+)$")
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        match = line_re.match(line.strip())
        if not match:
            failures.append({"entry": line, "reason": "invalid checksum line"})
            continue
        expected, relative = match.groups()
        relative = relative.replace("\\", "/")
        if relative in MUTABLE_CHECKSUM_FILES:
            skipped.append(relative)
            continue
        target = pack_root / relative
        if not target.is_file():
            failures.append({"file": relative, "reason": "missing"})
            continue
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        checked += 1
        if actual.lower() != expected.lower():
            failures.append({"file": relative, "expected": expected.lower(), "actual": actual})

    if failures:
        raise ValidationError("immutable pack checksum verification failed: " + json.dumps(failures, ensure_ascii=False))
    return {"status": "PASS", "checked": checked, "skipped_mutable": skipped}


def validate_state(pack_root: Path, mode: str, requested_phase: str | None) -> dict[str, object]:
    state = read_top_level_scalars(pack_root / "project_state.yaml")
    pack_revision = state.get("pack_revision")
    if pack_revision != 10:
        raise ValidationError(f"expected pack_revision 10, found {pack_revision!r}")

    approved_phase = state.get("approved_phase")
    plan_approved = state.get("plan_approved")
    next_action = state.get("next_allowed_action")

    if mode == "review":
        return {
            "plan_approved": plan_approved,
            "approved_phase": approved_phase,
            "next_allowed_action": next_action,
        }

    if plan_approved is not True:
        raise ValidationError("execution is not approved: plan_approved must be true")
    if not isinstance(approved_phase, str) or not PHASE_RE.fullmatch(approved_phase):
        raise ValidationError("approved_phase must be exactly one phase from P00 through P19")
    if requested_phase and requested_phase != approved_phase:
        raise ValidationError(
            f"requested phase {requested_phase} does not match approved_phase {approved_phase}"
        )
    expected_action = f"execute_{approved_phase}_only"
    if next_action != expected_action:
        raise ValidationError(
            f"next_allowed_action must be {expected_action!r}, found {next_action!r}"
        )

    prompts = sorted((pack_root / "phase_prompts").glob(f"{approved_phase}_*.md"))
    if len(prompts) != 1:
        raise ValidationError(
            f"expected exactly one prompt for {approved_phase}, found {len(prompts)}"
        )

    tasks_text = (pack_root / "tasks.yaml").read_text(encoding="utf-8")
    if not re.search(rf"(?m)^- id:\s*{re.escape(approved_phase)}\s*$", tasks_text):
        raise ValidationError(f"tasks.yaml does not contain phase {approved_phase}")

    return {
        "plan_approved": True,
        "approved_phase": approved_phase,
        "next_allowed_action": next_action,
        "phase_prompt": str(prompts[0]),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Android repository root")
    parser.add_argument("--pack-root", help="Explicit Agent Pack directory")
    parser.add_argument("--phase", help="Requested phase, for example P00")
    parser.add_argument("--mode", choices=("review", "execute"), default="execute")
    parser.add_argument("--verify-checksums", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.is_dir():
        print(f"ERROR: repository root does not exist: {repo_root}", file=sys.stderr)
        return 2

    try:
        if args.pack_root:
            pack_root = Path(args.pack_root).expanduser().resolve()
            if not is_pack_root(pack_root):
                raise ValidationError(f"not a valid Revision 10 pack root: {pack_root}")
        else:
            candidates = discover_pack_roots(repo_root)
            if not candidates:
                raise ValidationError("no Revision 10 Agent Pack found; pass --pack-root")
            if len(candidates) > 1:
                raise ValidationError(
                    "multiple Agent Packs found; pass --pack-root: "
                    + ", ".join(str(path) for path in candidates)
                )
            pack_root = candidates[0]

        verify_required_files(pack_root)
        state_result = validate_state(pack_root, args.mode, args.phase)
        checksum_result = (
            verify_checksums(pack_root)
            if args.verify_checksums
            else {"status": "NOT_EXECUTED", "reason": "flag not supplied"}
        )
        result = {
            "status": "PASS",
            "mode": args.mode,
            "repo_root": str(repo_root),
            "pack_root": str(pack_root),
            "state": state_result,
            "checksums": checksum_result,
        }
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("PASS: Revision 10 Agent Pack is structurally valid")
            print(f"pack_root={pack_root}")
            print(f"mode={args.mode}")
            print(f"approved_phase={state_result.get('approved_phase')}")
            print(f"checksum_status={checksum_result.get('status')}")
        return 0
    except ValidationError as exc:
        result = {"status": "BLOCKED", "error": str(exc)}
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"BLOCKED: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
