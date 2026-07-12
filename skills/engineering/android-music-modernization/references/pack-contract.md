# Agent Pack Contract

## Purpose

The Revision 10 Agent Pack is the project-specific source of execution scope. This skill must not reconstruct the plan from memory or replace it with a generic workflow.

## Required pack markers

A valid pack root contains:

```text
00_START_HERE.md
01_MASTER_PLAN_REVISION_10.md
02_TASKS_AND_CHECKPOINTS.md
03_TARGET_ARCHITECTURE.md
04_PROPOSED_PROJECT_STRUCTURE.md
05_BUILD_TEST_RELEASE_MATRIX.md
06_FUNCTIONAL_PARITY_CHECKLIST.md
07_DEPENDENCY_TOOLCHAIN_MATRIX.md
08_AGENT_EXECUTION_PROTOCOL.md
09_RISKS_DECISIONS_ROLLBACK.md
10_FILE_CHANGE_MAP.md
11_PHASE_REPORT_TEMPLATE.md
12_OFFICIAL_REFERENCE_INDEX.md
13_CURRENT_CODEBASE_AUDIT.md
14_PROGRESS_LEDGER.md
15_OWNER_DECISIONS.md
agent_context.yaml
tasks.yaml
decisions.yaml
project_state.yaml
phase_prompts/
```

`bundle_manifest.json` and `checksums.sha256` are strongly recommended. `source_review_inventory.csv` is supporting evidence, not authorization.

## State gate

Execution is permitted only when all conditions are true:

```yaml
plan_approved: true
approved_phase: Pxx
next_allowed_action: execute_Pxx_only
```

The requested phase must equal `approved_phase`. Only one phase may be approved. The corresponding prompt must exist under `phase_prompts/`, and `tasks.yaml` must contain that phase.

The following states allow review only, not production changes:

```yaml
plan_approved: false
approved_phase: null
next_allowed_action: owner_review_only
```

## Mutable and immutable pack files

Expected mutable evidence files:

- `project_state.yaml`
- `tasks.yaml`
- `14_PROGRESS_LEDGER.md`
- phase reports or audit artifacts explicitly allowed by the phase

Treat the master plan, architecture documents, build matrix, parity checklist, and phase prompts as immutable during phase execution unless the owner explicitly approves a documentation correction task.

When validating checksums after approval, ignore expected mutable state files. Any unexpected mutation to an immutable pack file is a blocker.

## Discovery

Prefer an explicit `--pack-root`. If absent, search only shallow repository paths and ignore `.git`, `.gradle`, `build`, `node_modules`, generated output, and caches. Stop when more than one candidate is found; do not guess.

## Conflicts

When the pack disagrees with current source or official APIs:

1. stop the implementation checkpoint;
2. capture source/build/API evidence;
3. classify the conflict;
4. request a plan correction or owner decision;
5. do not silently alter the architecture or phase scope.
