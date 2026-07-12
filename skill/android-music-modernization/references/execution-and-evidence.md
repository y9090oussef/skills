# Execution and Evidence Contract

## Before editing

Capture:

```bash
git rev-parse --show-toplevel
git status --short
git diff --name-status
./gradlew --version
./gradlew :app:tasks --all
```

Use the project wrapper and repository instructions. Do not run `clean` by default.

## Research

For any version-sensitive or policy-sensitive change, review primary sources:

- Android Developers and AndroidX release/API documentation;
- Kotlin official documentation;
- Google Play, Google Mobile Ads, UMP, Firebase, and WorkManager official documentation;
- official third-party release notes and migration guides.

Record URL, date, project version, target version, stability, compatibility, breaking changes, and the decision derived from the source. Current source behavior remains higher priority than a generic sample.

## Change loop

1. Establish a failing characterization or focused test when practical.
2. Make the smallest coherent change.
3. Run the narrowest compile/test that proves the step.
4. Run the required flavor gate.
5. Run Release/R8 when the touched area requires it.
6. Review the diff against both project standards and the phase specification.
7. Report evidence and stop for owner review.

Use a disciplined diagnosis loop after failure:

```text
reproduce → minimise → hypothesise → instrument → fix → regression-test
```

Do not continue modifying unrelated files after the first failure.

## Flavor gate

Active flavors:

- `mahrgnat`
- `faresSokar`
- `eslamKabonga`

Discover exact task names first. Run relevant variants sequentially and stop on first failure. Do not infer success for unexecuted variants.

## Release/R8 gate

Require Release/R8 evidence for changes involving:

- Manifest or components;
- Service, MediaSession, notification, foreground service;
- dependencies or plugins;
- Room schema/compiler/migrations;
- reflection;
- resources or flavor overlays;
- R8/ProGuard rules.

Never display signing secrets. Use the existing secure signing environment or mark the check `NOT_EXECUTED` with a blocker.

## Completion report

Use the pack’s `11_PHASE_REPORT_TEMPLATE.md`. Include:

- approval evidence and exact phase/task;
- files read fully;
- pre-change flow, risks, assumptions, and unknowns;
- files changed with purpose and risk;
- every command, exit code, result, and artifact;
- unit, integration, instrumented, runtime, flavor, API/device, parity, performance, size, 16 KB, Release/R8 evidence as relevant;
- exact diff summary;
- security and flavor verification;
- acceptance-gate table;
- blockers and gaps;
- rollback steps and whether rollback was tested;
- recommendation without authorizing the next phase.

Allowed statuses:

- `READY_FOR_REVIEW`
- `BLOCKED`
- `FAILED`
- `ROLLED_BACK`

Do not use `PASS` or `COMPLETED` for unexecuted checks.
