#!/usr/bin/env python3
"""Preview or safely install the bundled Revision 10 Agent Pack into an Android repository."""

from __future__ import annotations

import argparse
import base64
import io
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

ARCHIVE_NAME = "android_modernization_agent_pack_revision_10.zip"
CHUNK_GLOB = ARCHIVE_NAME + ".b64.*"
EXPECTED_ROOT = "android_modernization_agent_pack_revision_10"


def repo_root(start: Path) -> Path:
    try:
        result = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
        return Path(result.stdout.strip()).resolve()
    except (OSError, subprocess.CalledProcessError):
        return start.resolve()


def archive_bytes() -> tuple[bytes, str]:
    """Return the bundled archive bytes and a human-readable source label.

    GitHub connector writes are text-oriented, so the repository stores the
    archive as ordered Base64 chunks. A direct ZIP is also accepted for local
    development or future repository migrations.
    """
    assets = Path(__file__).resolve().parent.parent / "assets"
    direct = assets / ARCHIVE_NAME
    if direct.is_file():
        return direct.read_bytes(), str(direct)

    chunks = sorted(assets.glob(CHUNK_GLOB))
    if not chunks:
        raise FileNotFoundError(
            f"neither {ARCHIVE_NAME} nor chunks matching {CHUNK_GLOB} exist in {assets}"
        )
    expected = [f"{index:03d}" for index in range(1, len(chunks) + 1)]
    actual = [path.suffix.removeprefix(".") for path in chunks]
    if actual != expected:
        raise ValueError(f"Agent Pack chunk sequence is not contiguous: {actual}")
    encoded = "".join(path.read_text(encoding="ascii").strip() for path in chunks)
    try:
        return base64.b64decode(encoded, validate=True), f"{len(chunks)} Base64 chunks"
    except ValueError as exc:
        raise ValueError(f"invalid bundled Agent Pack base64: {exc}") from exc


def safe_members(archive: zipfile.ZipFile) -> list[tuple[zipfile.ZipInfo, Path]]:
    result: list[tuple[zipfile.ZipInfo, Path]] = []
    for info in archive.infolist():
        raw = PurePosixPath(info.filename)
        if raw.is_absolute() or ".." in raw.parts:
            raise ValueError(f"unsafe archive path: {info.filename}")
        if not raw.parts or raw.parts[0] != EXPECTED_ROOT:
            raise ValueError(f"unexpected archive root: {info.filename}")
        relative = Path(*raw.parts[1:])
        if not relative.parts or info.is_dir():
            continue
        result.append((info, relative))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--destination", default=".agent/android-modernization")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    repo = repo_root(Path(args.repo))
    destination = (repo / args.destination).resolve()
    try:
        destination.relative_to(repo)
    except ValueError:
        print("error: destination must remain inside the target repository", file=sys.stderr)
        return 2

    try:
        payload, source_label = archive_bytes()
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            bad_member = archive.testzip()
            if bad_member:
                raise ValueError(f"corrupt archive member: {bad_member}")
            members = safe_members(archive)
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        print(f"error: invalid bundled Agent Pack archive: {exc}", file=sys.stderr)
        return 2

    print(f"repository: {repo}")
    print(f"destination: {destination}")
    print(f"archive_source: {source_label}")
    print(f"archive_bytes: {len(payload)}")
    print(f"files: {len(members)}")

    if destination.exists() and any(destination.iterdir()) and not args.force:
        print(
            "error: destination exists and is not empty; back it up and use --force only with owner approval",
            file=sys.stderr,
        )
        return 3

    if not args.apply:
        print("dry-run: no files extracted; add --apply after explicit owner approval")
        return 0

    if destination.exists() and args.force:
        backup = destination.with_name(destination.name + ".backup")
        if backup.exists():
            print(f"error: backup destination already exists: {backup}", file=sys.stderr)
            return 4
        destination.rename(backup)
        print(f"backup: {backup}")

    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for info, relative in members:
            target = (destination / relative).resolve()
            try:
                target.relative_to(destination)
            except ValueError:
                print(f"error: unsafe extraction target: {relative}", file=sys.stderr)
                return 5
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)

    print("installed: true")
    print("note: project_state.yaml remains NOT_APPROVED until the owner explicitly approves a phase")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
