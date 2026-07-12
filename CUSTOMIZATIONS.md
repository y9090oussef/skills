# Fork Customizations

This fork tracks `mattpocock/skills` and adds one project-specific skill:

```text
skills/engineering/android-music-modernization/
```

## Purpose

The skill governs phase-by-phase work on the owner's multi-flavor Android offline/online music application. It stores the reviewed Revision 10 Agent Pack as ordered Base64 transport chunks that reconstruct an immutable ZIP bootstrap and installs a mutable copy into the Android repository only after explicit owner approval.

## Shared upstream files changed

- `.claude-plugin/plugin.json`
- `README.md`
- `skills/engineering/README.md`

The fork also adds:

- `.changeset/android-music-modernization.md`
- `docs/engineering/android-music-modernization.md`
- `CUSTOMIZATIONS.md`
- `.github/workflows/validate-android-music-skill.yml`
- `skills/engineering/android-music-modernization/**`

Do not modify upstream skills such as `tdd`, `research`, `diagnosing-bugs`, `code-review`, or `handoff` for this integration.

## Syncing upstream

```bash
git remote add upstream https://github.com/mattpocock/skills.git
git fetch upstream
git checkout main
git pull --ff-only origin main
git checkout -b chore/sync-upstream-YYYYMMDD
git merge upstream/main
```

Resolve conflicts by preserving upstream work and the custom files listed above. Validate the skill and its scripts before merging.

Never use `git reset --hard upstream/main`, force-push `main`, or copy a fresh upstream ZIP over this fork.

## Validation

Run the self-contained distribution and integration check after every upstream sync or project-skill edit:

```bash
python skills/engineering/android-music-modernization/scripts/validate_distribution.py \
  --repo-root .
python -m py_compile skills/engineering/android-music-modernization/scripts/*.py
```

Then run the Skill validator/packager supplied by the host agent environment. The standalone output must be named `skill.zip`. Do not hard-code a machine-specific validator path in this repository.
