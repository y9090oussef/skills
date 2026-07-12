# Maintaining the Fork Against Upstream

## Goal

Keep the project-specific `android-music-modernization` skill while continuing to receive updates from the original Matt Pocock repository.

## Remotes

Use:

```text
origin   → y9090oussef/skills
upstream → mattpocock/skills
```

Add upstream once when missing:

```bash
git remote add upstream https://github.com/mattpocock/skills.git
git fetch upstream
```

## Safe update workflow

Never replace the fork with a fresh ZIP and never hard-reset `main` to upstream. Use a branch and pull request:

```bash
git fetch upstream
git checkout main
git pull --ff-only origin main
git checkout -b chore/sync-upstream-YYYYMMDD
git merge upstream/main
```

Resolve conflicts by retaining both:

- upstream additions and fixes;
- `skills/engineering/android-music-modernization/**`;
- the custom entry in `.claude-plugin/plugin.json`;
- the custom entries in `README.md` and `skills/engineering/README.md`;
- `docs/engineering/android-music-modernization.md`;
- `CUSTOMIZATIONS.md` and the customization changeset.

Then validate and package the skill before merging the sync PR.

## Expected conflict surface

The custom skill directory is isolated and should rarely conflict. Likely conflicts are limited to:

- `.claude-plugin/plugin.json`;
- `README.md`;
- `skills/engineering/README.md`.

Do not modify upstream skills such as `tdd`, `research`, `diagnosing-bugs`, `code-review`, or `handoff` merely to integrate this project skill.

## Never use for synchronization

Avoid:

```bash
git reset --hard upstream/main
git push --force origin main
```

Also avoid copying a fresh upstream ZIP over the fork. These approaches can discard custom commits or hide conflicts.

## Recovery

Because the customization is committed, recover it from Git history:

```bash
git log -- skills/engineering/android-music-modernization
git restore --source <known-good-commit> -- skills/engineering/android-music-modernization
```

Keep upstream synchronization and project-skill development in separate pull requests.
