Quickstart:

```bash
npx skills add y9090oussef/skills --skill=android-music-modernization
```

```bash
npx skills update android-music-modernization
```

[Source](https://github.com/y9090oussef/skills/tree/main/skills/engineering/android-music-modernization)

## What it does

This skill is the project-specific control plane for modernizing the New_Mahrgnat multi-flavor Android music app. It carries the reviewed Revision 10 Agent Pack as ordered Base64 transport chunks that reconstruct one bundled ZIP, installs a mutable project-local copy only with owner approval, and enforces the plan, architecture, parity, flavor, build, test, security, evidence, and rollback gates.

It refuses production changes unless the repository markers match and the exact phase is explicitly approved in the project-local `project_state.yaml`.

## When to reach for it

Use `/android-music-modernization` when installing or validating the Agent Pack, auditing the plan or source, executing one approved phase, diagnosing a phase failure, or reviewing an agent diff against Revision 10.

For a generic bug outside this project, use `diagnosing-bugs`. For generic behavior-first implementation, use `tdd`.

## One approved phase

The skill reads progressively: repository rules and phase state first, then the current phase prompt, then only the references and source needed for that phase. It treats the plan as a gate, not a blanket permission slip.

Every execution follows:

```text
preflight → source audit → current official docs → smallest vertical slice
→ targeted tests → all-flavor gate → diff review → phase report → owner review
```

It never moves to the next phase automatically, removes the legacy fallback early, or hides a failing build with a dependency bump or broad suppression.

## Bundled Agent Pack

The complete Agent Pack is stored in the skill as:

```text
`assets/android_modernization_agent_pack_revision_10.zip.b64.001` ... contiguous chunks (the installer also accepts a direct `.zip` for local development)
```

Run the install script in dry-run mode first, then apply only after explicit approval. The extracted project-local copy becomes the mutable execution record; the bundled transport chunks remain an immutable bootstrap snapshot.

## Evidence over claims

A phase is not complete because an agent says it is. The skill requires exact commands, exit codes, flavor coverage, behavior evidence, Release/R8 checks where applicable, changed-file scope, and rollback status. `READY_FOR_REVIEW` still requires owner acceptance.

## It's working if

- The agent stops when the project or phase is not approved.
- Only the allowed risk family and files are changed.
- Android and third-party decisions cite current primary documentation.
- All relevant flavors and release gates are reported explicitly.
- Legacy code survives until parity, rollback, and owner approval are proven.
- Every phase ends with a structured report rather than silently starting the next one.
