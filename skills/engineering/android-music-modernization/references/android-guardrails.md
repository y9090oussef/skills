# Android Project Guardrails

## Architecture

- Use a practical UI → ViewModel/state holder → Repository → data-source flow.
- Add domain/use-case classes only for shared business rules or orchestration that benefits from a pure testable boundary.
- Start with constructor injection and the approved `AppContainer`; do not add Hilt during playback or UI cutover without its own evidence gate.
- Keep one application module until stable boundaries and build measurements justify modularization.

## Playback

Target flow:

```text
Compose/XML UI
→ ViewModel or UI adapter
→ PlaybackControllerRepository
→ MediaController
→ MediaSession in MediaSessionService
→ one long-lived ExoPlayer
```

Enforce:

- no new custom Binder;
- no `bindService()` in Activity, Fragment, or ViewModel for the new engine;
- no raw Service or ExoPlayer in UI;
- no reflection to reach playback internals;
- one enabled playback service, one long-lived player, one session, and one notification owner per APK;
- service owns queue, playback, source resolution, and premium gate authority;
- native Player commands before custom SessionCommands;
- only IDs and small resolver data cross the session boundary;
- one shared progress stream, not per-screen polling;
- UI connection lifetime must not control player/service lifetime;
- ringtone preview may use a short-lived isolated player with no session or notification.

Preserve legacy behavior through characterization tests, including queue mutation, shuffle/repeat, local/online/download/device sources, premium/ad flows, equalizer, audio focus, process death, notification, lock screen, Bluetooth, and previous-button boundaries at 2999/3000/3001 ms.

## Java to Kotlin

- Write new code in Kotlin.
- Migrate leaf values, mappers, validators, interfaces, and small repositories before giant activities/services/controllers.
- Do not auto-convert thousand-line classes and clean them later.
- Keep Java bridges small and temporary.
- Use immutable models, main-safe repositories, injected dispatchers, suspend for one-shot work, and Flow for streams.
- Do not migrate RxJava, DI, Room compiler, and architecture simultaneously.

## XML to Compose

- Migrate screen by screen behind the approved coexistence path.
- Preserve XML fallback until functional, visual, RTL, accessibility, adaptive, performance, and flavor parity are proven.
- Use resources and `MaterialTheme`; do not hardcode strings, colors, app names, package IDs, Ad IDs, or flavor identity.
- Use lifecycle-aware collection and unidirectional data flow.
- Keep existing Navigation during mixed UI unless the approved phase explicitly migrates a complete graph with back-stack and deep-link tests.

## Data and background work

- Never change Room schema without exported schemas, known migration paths, and migration tests.
- Do not use destructive migration as a silent upgrade strategy.
- Keep disk/network/DB work off the main thread.
- Use WorkManager for persistent deferrable work; use foreground services only for user-visible ongoing work allowed by current Android rules.
- Deduplicate downloads and sync using one authoritative repository/state path and unique work policies.

## Ads and privacy

- Centralize UMP and ad initialization.
- Gate ad requests on current consent state.
- Prevent duplicate rewarded/interstitial/app-open callbacks.
- Preserve prior playback intent across ad display.
- Keep all flavor-specific IDs in approved resources/configuration and redact their values from reports.

## Performance and size

- Measure before optimizing.
- Record device, API, flavor, build type, scenario, sample count, median, and P90.
- Do not use `System.gc()`, fixed delays, `largeHeap`, broad keep rules, or dependency removal as unmeasured fixes.
- Add Baseline Profiles only after critical journeys stabilize.
- Validate R8/resource shrinking on installed Release builds for all flavors.
- Check 16 KB page-size compatibility whenever native libraries or native-bearing SDKs are present or updated.

## Versions and official documentation

- Do not use “latest” as sufficient justification.
- Confirm the project’s pinned version, the latest stable version, compatibility matrix, migration guide, release notes, breaking changes, and API annotation.
- Keep dependency-family upgrades separate from architectural and behavioral changes.
- Require an ADR for alpha, beta, rc, or `@UnstableApi` use.
