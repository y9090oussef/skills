#!/usr/bin/env python3
"""Validate the distributable Android music modernization skill and its fork integration."""

from __future__ import annotations

import argparse
import base64
import io
import json
import re
import sys
import zipfile
from pathlib import Path

SKILL_NAME = "android-music-modernization"
PLUGIN_ENTRY = "./skills/engineering/android-music-modernization"
ARCHIVE_NAME = "android_modernization_agent_pack_revision_10.zip"
ARCHIVE_GLOB = ARCHIVE_NAME + ".b64.*"
ARCHIVE_ROOT = "android_modernization_agent_pack_revision_10"
REQUIRED_SKILL_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/android-guardrails.md",
    "references/execution-and-evidence.md",
    "references/pack-contract.md",
    "references/upstream-maintenance.md",
    "scripts/install_agent_pack.py",
    "scripts/phase_scope.py",
    "scripts/preflight.py",
    "scripts/validate_agent_pack.py",
    "scripts/validate_distribution.py",
    "scripts/verify_phase_report.py",
)
REQUIRED_PACK_FILES = (
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


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md has no valid YAML frontmatter block")
    values: dict[str, str] = {}
    for raw in match.group(1).splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        key, sep, value = raw.partition(":")
        if not sep:
            raise ValueError(f"invalid frontmatter line: {raw}")
        values[key.strip()] = value.strip().strip("'\"")
    return values


def archive_payload(skill_root: Path) -> tuple[bytes, str, int]:
    assets = skill_root / "assets"
    direct = assets / ARCHIVE_NAME
    if direct.is_file():
        return direct.read_bytes(), ARCHIVE_NAME, 0

    chunks = sorted(assets.glob(ARCHIVE_GLOB))
    if not chunks:
        raise ValueError(
            f"bundled Agent Pack is missing: expected {direct} or {ARCHIVE_GLOB}"
        )
    expected = [f"{index:03d}" for index in range(1, len(chunks) + 1)]
    actual = [path.suffix.removeprefix(".") for path in chunks]
    if actual != expected:
        raise ValueError(f"Agent Pack chunk sequence is not contiguous: {actual}")
    encoded = "".join(path.read_text(encoding="ascii").strip() for path in chunks)
    try:
        payload = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise ValueError(f"invalid Agent Pack base64: {exc}") from exc
    return payload, ARCHIVE_GLOB, len(chunks)


def validate_archive(skill_root: Path) -> dict[str, object]:
    payload, source, chunk_count = archive_payload(skill_root)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"corrupt Agent Pack archive member: {bad}")
        names = {name.rstrip("/") for name in archive.namelist() if not name.endswith("/")}
    missing = [
        relative
        for relative in REQUIRED_PACK_FILES
        if f"{ARCHIVE_ROOT}/{relative}" not in names
    ]
    prompts = sorted(name for name in names if name.startswith(f"{ARCHIVE_ROOT}/phase_prompts/P"))
    expected_prompts = {f"P{index:02d}" for index in range(20)}
    actual_prompts = {Path(name).name.split("_", 1)[0] for name in prompts}
    if missing:
        raise ValueError("Agent Pack archive is missing: " + ", ".join(missing))
    if actual_prompts != expected_prompts:
        raise ValueError(
            "Agent Pack phase prompt set mismatch: "
            f"expected={sorted(expected_prompts)} actual={sorted(actual_prompts)}"
        )
    return {
        "bytes": len(payload),
        "source": source,
        "chunks": chunk_count,
        "files": len(names),
        "phase_prompts": 20,
    }


def validate_skill(skill_root: Path) -> dict[str, object]:
    missing = [relative for relative in REQUIRED_SKILL_FILES if not (skill_root / relative).is_file()]
    if missing:
        raise ValueError("skill distribution is missing: " + ", ".join(missing))

    skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(skill_text)
    if frontmatter.get("name") != SKILL_NAME:
        raise ValueError(f"unexpected skill name: {frontmatter.get('name')!r}")
    if not frontmatter.get("description"):
        raise ValueError("skill description is empty")
    unexpected = sorted(set(frontmatter) - {"name", "description"})
    if unexpected:
        raise ValueError("unexpected SKILL.md frontmatter keys: " + ", ".join(unexpected))

    broken_links: list[str] = []
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", skill_text):
        if "://" in target or target.startswith("#"):
            continue
        path = (skill_root / target.split("#", 1)[0]).resolve()
        try:
            path.relative_to(skill_root.resolve())
        except ValueError:
            broken_links.append(target)
            continue
        if not path.exists():
            broken_links.append(target)
    if broken_links:
        raise ValueError("broken local links in SKILL.md: " + ", ".join(broken_links))

    return {
        "name": SKILL_NAME,
        "skill_lines": len(skill_text.splitlines()),
        "archive": validate_archive(skill_root),
    }


def validate_repo(repo_root: Path) -> dict[str, object]:
    plugin = repo_root / ".claude-plugin/plugin.json"
    if not plugin.is_file():
        raise ValueError("repository plugin manifest is missing")
    payload = json.loads(plugin.read_text(encoding="utf-8"))
    if PLUGIN_ENTRY not in payload.get("skills", []):
        raise ValueError(f"plugin manifest does not register {PLUGIN_ENTRY}")

    required_mentions = {
        "README.md": "android-music-modernization",
        "skills/engineering/README.md": "android-music-modernization",
        "docs/engineering/android-music-modernization.md": "Revision 10",
        "CUSTOMIZATIONS.md": "skills/engineering/android-music-modernization/",
        ".github/workflows/validate-android-music-skill.yml": "validate_distribution.py",
    }
    missing_mentions: list[str] = []
    for relative, marker in required_mentions.items():
        path = repo_root / relative
        if not path.is_file() or marker not in path.read_text(encoding="utf-8"):
            missing_mentions.append(f"{relative}:{marker}")
    if missing_mentions:
        raise ValueError("repository integration markers are missing: " + ", ".join(missing_mentions))
    return {"plugin_registered": True, "integration_files": len(required_mentions)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--repo-root")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    try:
        skill_root = Path(args.skill_root).expanduser().resolve()
        result: dict[str, object] = {"status": "PASS", "skill": validate_skill(skill_root)}
        if args.repo_root:
            result["repository"] = validate_repo(Path(args.repo_root).expanduser().resolve())
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("PASS: android-music-modernization skill distribution is valid")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc)}
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"FAIL: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
