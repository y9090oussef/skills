---
name: android-music-modernization
description: project-specific control plane for the new_mahrgnat multi-flavor android music app modernization. use when an agent must install or validate the revision 10 agent pack, audit the source or plan, execute exactly one owner-approved phase, diagnose a phase failure, or review a diff involving java/kotlin, xml/compose, media3 playback, room, downloads, sync, ads/ump, performance, r8, flavors, or release safety. block production changes until the intended project and exact approved phase are verified.
---

# Android Music Modernization

Govern work on the specific multi-flavor Android offline/online music application with its Revision 10 Agent Pack. Keep the owner in control, make one evidence-backed checkpoint at a time, and never advance phases automatically.

## 1. Prove that this is the intended project

Run the project preflight before reading or changing production code:

```bash
python <skill-directory>/scripts/preflight.py --repo .
```

The repository must contain:

- `settings.gradle` or `settings.gradle.kts`;
- `app/build.gradle` or `app/build.gradle.kts`;
- `gradle/libs.versions.toml`;
- `app/src/main/AndroidManifest.xml`;
- active flavors `mahrgnat`, `faresSokar`, and `eslamKabonga` in the real build configuration.

Stop when a marker or flavor is missing. Do not apply this skill to another Android project.

## 2. Install the Agent Pack once, with owner approval

The complete Revision 10 Agent Pack is bundled as ordered transport chunks:

```text
assets/android_modernization_agent_pack_revision_10.zip.b64.001
...
assets/android_modernization_agent_pack_revision_10.zip.b64.012
```

`install_agent_pack.py` concatenates and decodes these chunks into the exact reviewed ZIP in memory. It also accepts a direct `assets/android_modernization_agent_pack_revision_10.zip` when a local distribution uses one. Do not edit, reorder, or partially replace the chunks.

Prefer a mutable project-local copy at:

```text
.agent/android-modernization/
```

Preview installation first:

```bash
python <skill-directory>/scripts/install_agent_pack.py --repo .
```

Apply only after explicit owner approval:

```bash
python <skill-directory>/scripts/install_agent_pack.py --repo . --apply
```

Never overwrite an existing pack silently. Use `--force` only after backing up the current pack and receiving explicit approval. The script must create a sibling backup before replacement.

The ordered Base64 transport chunks reconstruct one immutable ZIP bootstrap in memory. Once installed, the project-local copy is the mutable execution record. Never edit the bundled chunks inside the installed skill.

Read [pack-contract.md](references/pack-contract.md) for required files, state rules, mutable files, and conflict handling.

## 3. Validate the exact operating mode

For audit or plan review:

```bash
python <skill-directory>/scripts/validate_agent_pack.py \
  --repo-root . \
  --pack-root .agent/android-modernization \
  --mode review \
  --verify-checksums
```

For execution, the owner must explicitly approve exactly one phase in `project_state.yaml`:

```yaml
plan_approved: true
approved_phase: P00
next_allowed_action: execute_P00_only
```

Then run:

```bash
python <skill-directory>/scripts/preflight.py --repo . --require-phase P00
python <skill-directory>/scripts/validate_agent_pack.py \
  --repo-root . \
  --pack-root .agent/android-modernization \
  --mode execute \
  --phase P00 \
  --verify-checksums
```

Treat any failure as a hard stop. Never edit `project_state.yaml` to grant yourself approval.

## 4. Apply the source-of-truth order

Use this precedence:

1. Current owner instruction.
2. Actual source, build files, manifests, resources, and generated evidence.
3. Reproducible tests and runtime behavior.
4. The installed Revision 10 Agent Pack.
5. Current official stable Android, Google, Kotlin, and library documentation.
6. Official third-party documentation.
7. Generic skills and remembered practices.

Do not let a generic skill, sample, or old plan override current project evidence.

## 5. Read progressively

Read in this order:

1. Repository `AGENTS.md`, `CLAUDE.md`, and local agent rules when present.
2. `.agent/android-modernization/00_START_HERE.md`.
3. `project_state.yaml` and `agent_context.yaml`.
4. `08_AGENT_EXECUTION_PROTOCOL.md`.
5. The approved `phase_prompts/Pxx_*.md` in full.
6. The matching phase entry in `tasks.yaml` and relevant entries in `decisions.yaml`.
7. Only the plan, architecture, parity, build, risk, file-map, and audit documents referenced by that phase.
8. Every source file listed under `read first`, in full.
9. All discovered call sites, manifests, resources, and flavor overlays affected by the change.

Do not load the entire codebase or pack into context when a smaller evidence set is sufficient.

## 6. Re-audit before editing

Before implementation:

- verify every referenced file, class, method, task, API, and variant exists;
- rerun call-site and dependency searches instead of trusting old line numbers;
- draw call, data, lifecycle, or dependency flow when architecture is touched;
- list assumptions, unknowns, risks, stop conditions, allowed files, forbidden files, and rollback;
- review current official documentation for every version-sensitive or policy-sensitive API;
- record URL, review date, project version, latest stable version, API availability, stability annotation, compatibility notes, and breaking changes.

Read [android-guardrails.md](references/android-guardrails.md) for project-specific architecture, playback, data, UI, ads, performance, and dependency rules.

## 7. Execute one approved checkpoint only

Use this loop:

```text
Audit → characterization/failing test → smallest change → targeted check
→ all-flavor gate → standards/spec review → phase report → owner review
```

Rules:

- Execute only the approved phase, preferably one task/checkpoint within it.
- Do not combine dependency upgrades, database migrations, playback refactors, UI migrations, and feature behavior changes in one diff.
- Use Kotlin for new production code and Compose/Material 3 for new UI only when the approved phase permits it.
- Preserve Java/XML and legacy playback fallback until parity, tests, rollback, observation, and explicit owner approval.
- Prefer stable APIs. Require an ADR, isolation, tests, and rollback for Alpha, Beta, RC, preview, or `@UnstableApi` use.
- Do not add Hilt, Retrofit, Paging, Navigation changes, multi-module architecture, or another framework without the corresponding evidence gate.
- Do not edit generated files manually.
- Do not commit, push, merge, rewrite history, or advance the phase unless the owner explicitly requests that Git operation.

Use the repository's `research`, `tdd`, `diagnosing-bugs`, `code-review`, and `handoff` skills as supporting disciplines when available. They remain subordinate to this skill and the Agent Pack.

## 8. Build and test with evidence

Read [execution-and-evidence.md](references/execution-and-evidence.md).

Always:

- discover Gradle task names before assuming them;
- use the project wrapper;
- avoid `clean` by default;
- run relevant flavors sequentially and stop at the first failure;
- require Release/R8 checks for Manifest, Service, dependency, Room, reflection, resource, or R8 changes;
- mark skipped checks as `NOT_EXECUTED — reason`;
- treat historical logs as context only;
- never claim runtime, release, migration, accessibility, performance, battery, size, Bluetooth, lock-screen, or process-death success without executing the matching check.

Before reporting completion, enforce the phase file scope:

```bash
python <skill-directory>/scripts/phase_scope.py \
  --repo-root . \
  --allow '<phase-allowed-glob>' \
  --forbid 'app/neama.jks' \
  --forbid '**/google-services.json'
```

Add every phase-specific allow/forbid glob from the approved prompt.

## 9. Protect flavors, users, and secrets

Never print, request, move, expose, or casually rewrite:

- application IDs, namespace, flavor identity, app names, logos, colors, assets, Firebase/AdMob/OneSignal configuration;
- signing configs, keystores, passwords, certificates, or private hashes;
- `google-services.json` contents;
- production databases or user data;
- media paths, tokens, sensitive URLs, UIDs, or signatures.

Do not delete or replace a component before understanding all callers and upgrade behavior. Do not remove Room fallback, Java/XML fallback, or legacy playback until its dedicated gate is satisfied.

## 10. Review and report; never auto-advance

Before declaring `READY_FOR_REVIEW`:

- inspect `git status --short`, `git diff --name-status`, and `git diff --stat`;
- verify every changed file is allowed;
- review the diff independently for standards and exact phase specification;
- use `.agent/android-modernization/11_PHASE_REPORT_TEMPLATE.md`;
- update mutable pack state only when the approved phase permits it and evidence exists;
- state the first failure, unexecuted checks, blockers, and rollback status accurately.

Run:

```bash
python <skill-directory>/scripts/verify_phase_report.py path/to/phase-report.md
```

Allowed final statuses are:

- `READY_FOR_REVIEW`
- `BLOCKED`
- `FAILED_ROLLED_BACK`
- `PRECONDITION_FAILED`

`READY_FOR_REVIEW` is not acceptance. Only the owner may accept a phase and authorize the next one.

## 11. Maintain the fork safely

Read [upstream-maintenance.md](references/upstream-maintenance.md) before syncing this fork with `mattpocock/skills`. Preserve this skill directory, the plugin registration, the documentation entries, and `CUSTOMIZATIONS.md` while also retaining upstream changes.

After a sync or skill edit, validate the complete distribution:

```bash
python <skill-directory>/scripts/validate_distribution.py --repo-root <skills-repository-root>
```
