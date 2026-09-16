# Technical plan

Prepared 2026-09-16. This document describes the intended implementation. None of the systems, exports, or performance results below exists yet.

## 1. Stack decision

| Concern | Recommended choice |
|---|---|
| Engine | Godot 4.7.2 stable, standard/non-.NET distribution |
| Language | Typed GDScript |
| Renderer | Compatibility |
| Runtime graphics | 2D sprites, tile layers, restrained CanvasItem effects |
| Data | Typed Resource definitions saved as text `.tres`; stable string IDs |
| Saves | Versioned local data under `user://`; atomic-style replacement and backup |
| UI | Godot Control nodes, Containers, anchors, themes, focus navigation |
| Asset authoring | Blender for optional sprite rendering; Krita/GIMP or a selected 2D editor for paint-over; audio editor |
| Version control | Git and GitHub; LFS only for source files we have rights to publish |
| Automated tests | A small GDScript headless test runner initially; no external test dependency required |
| Automation | GitHub Actions for checks and unsigned test builds after M0 |
| Steam | Isolated platform adapter; select/pin a compatible binding during the Steam integration milestone |
| Mobile | Native Android and iOS exports from the same project |
| Backend | None in the initial release |

The official [Godot release archive](https://godotengine.org/download/archive/) listed 4.7.2-stable, released 2026-08-18, as the newest stable release when checked on 2026-09-16. Match editor and export templates exactly. Store the selected version in `.godot-version` when the project is created. Do not follow `latest`, use nightly builds, or upgrade engine versions inside an unrelated feature change.

Godot describes Compatibility as the broad-hardware/2D starting point; the renderer named Mobile is not required merely because the destination is a phone. This is a project choice, not a guarantee that Compatibility wins every benchmark. [Renderer documentation](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html).

Alternatives considered: Unity 2D remains technically viable, but changing engines has no demonstrated benefit for this small GDScript-first plan. A browser renderer, Electron shell, or JavaScript-to-mobile wrapper is unnecessary. No custom C++ engine or general-purpose ECS framework is planned.

## 2. Project layout to create during implementation

```text
Alien-Survivor/
  README.md
  AGENTS.md
  docs/
    GAME_DESIGN.md
    TECHNICAL_PLAN.md
    ART_AND_ASSETS.md
    PRODUCTION_PLAN.md
  prompts/
    FIRST_BUILD.md
  game/
    project.godot
    export_presets.cfg
    scenes/
      boot/
      arena/
      player/
      ui/
      tests/
    scripts/
      core/
      combat/
      enemies/
      progression/
      input/
      platform/
      saving/
      presentation/
    data/
      weapons/
      modules/
      enemies/
      upgrades/
      encounters/
      arenas/
    assets/
      sprites/
      tiles/
      vfx/
      audio/
      ui/
      licences/
    tests/
      run_tests.gd
      unit/
      integration/
  tools/
    asset_validation/
    build/
  .github/
    workflows/
```

This tree is a proposal, not a list of already-created folders. Create modules only when their current milestone requires them. Avoid empty manager classes, parallel frameworks, and boilerplate for future multiplayer.

## 3. Separation of responsibilities

The core rule is: **input describes intent, gameplay changes state, presentation displays it, and platform services save or report it.**

| System | Owns | Must not own |
|---|---|---|
| `RunController` | Run lifecycle, phase, clock, victory/death transition | Store APIs or individual bullet visuals |
| `InputRouter` | Move vector, aim override, dash/pause intent | Damage calculations |
| `CombatSystem` | Cooldowns, hits, damage, status effects | OS input polling or UI text layout |
| `EnemyManager` | Enemy state, cheap steering, lifecycle, nearby queries | Account services |
| `SpawnDirector` | Seeded encounter budget and safe spawn selection | Rendering quality settings |
| `ProgressionSystem` | XP, valid offers, ranks, breakthroughs | Direct Steam achievement calls |
| `ArenaController` | Geometry, blockers, terminal sockets, navigation data | Global save ownership |
| `SaveService` | Versioned serialization and recovery | Combat tuning |
| `PlatformServices` | Platform capabilities and optional integrations | Core win/loss rules |
| Presentation | Sprites, animation, sound, HUD, cosmetic quality | Authoritative health or cooldown state |

Use direct typed method calls within hot simulation paths. Use signals for bounded high-level events such as a level-up, a run ending, or a settings change. Do not broadcast a heavyweight event for every particle or every enemy movement.

Keep autoloads small: boot/configuration, settings/saving, and a platform service entry point as needed. Do not create an autoload for every weapon or enemy family.

## 4. First implementation versus scaling implementation

M0 may use lightweight pooled Node2D enemies with simple sprite children and one central update loop. The player can use CharacterBody2D for world collision. No physics rigid body, full navigation agent, timer, and independent `_process()` tree on every regular alien by default.

Profile before replacing a readable implementation. When needed, move enemy state into contiguous arrays owned by EnemyManager while preserving the public gameplay interface. Separate entity identity from pooled view identity; use generation counters or equivalent checks so a recycled enemy slot cannot be hit through a stale reference.

A spatial grid limits nearby collision and target queries. Use simple circle or capsule approximations for crowds, swept segment tests for fast projectiles, and simple world blockers. Avoid all-enemy-versus-all-enemy loops. Resolve world collision explicitly; monsters must not gain the ability to pass through walls as an optimization.

Open arenas need steering, not a full path search per enemy per frame. If obstacles cause persistent jams, add a shared coarse flow field or cached navigation solution. Recalculate when the target changes cell or geometry changes, not separately for each creature.

Pooling requires complete reset of health, team, effects, timers, animation, hit history, and identifiers. Add tests for reuse bugs. Do not assume pooling is automatically faster; measure allocation and reset cost.

## 5. Time, randomness, damage, and state

Use a fixed simulation step, initially 60 Hz, independent of render FPS. A phone rendering at 30 FPS must not run half as many gameplay seconds or change cooldown behavior. Expensive target/steering decisions can update less often while positions and safety-critical collision remain correct. Apply any gameplay scheduling policy consistently across platforms.

Run states: BOOT -> MENU -> RUNNING -> UPGRADE_SELECTION/PAUSED -> RUNNING -> FINALE -> RESULTS. Transitions are idempotent: simultaneous damage events must not award rewards twice or show both victory and defeat. Define simultaneous boss/player death explicitly during M1 testing; recommended default is defeat if the player has no health when the resolution step completes.

Use separate seeded random streams for encounters, upgrade offers, and cosmetic effects. Turning off blood must not change the next enemy or upgrade. Record seed plus game/content version for diagnostics. Do not promise cross-platform deterministic replays: floating-point behavior and engine changes need additional work and validation.

Damage rules must define additive versus multiplicative modifiers, caps, armor handling, critical hits, per-source hit intervals, pierce history, invulnerability, status stacking, and on-death effects. Bound chain reactions and define which effects may trigger other effects. A proc loop must not generate unbounded damage events.

## 6. Data contracts

Use Resource definitions such as WeaponDef, ModuleDef, EnemyDef, UpgradeDef, EncounterDef, and ArenaDef. Fields should include stable ID, localized name/description keys, runtime scene/visual references, relevant numeric values, tags, ranks, and prerequisites. Do not embed upgrade text or balance values throughout UI scripts.

Definitions are immutable during a run. Separate per-run mutable values from shared Resource files so upgrading one weapon cannot modify the starting weapon in the next run.

Validation must reject duplicate IDs, broken references, impossible prerequisites, missing visual/licence references, negative cooldowns, invalid ranks, and unreachable progression. A complete upgrade pool always has a safe fallback when fewer than three distinct offers remain.

Save data contains IDs and values, not executable scripts or arbitrary Resource paths received from outside the application. Clamp and validate loaded data. Player-edited local saves are not prevented by a security backend in this single-player scope.

## 7. Rendering and camera

Flat art remains flat. No rotating camera, perspective orbit, overlapping combat floors, real-time 3D characters, or simulated volumetric lighting.

Initial art-layout reference: a 960 x 540 world view. The precise raster/filtering decision is an M1 art test, not an established minimum device specification. Compare crisp nearest sampling against restrained linear sampling using actual pre-rendered art; do not equate retro with compulsory coarse pixel art.

Keep a canonical 16:9 combat view at first. Fit it inside the available display; use extra aspect-ratio space for unobtrusive margins or controls rather than silently revealing more combat area on wider phones. UI and safe areas are computed separately. A 16:10 Steam Deck display may use the remaining space for HUD/margins. Never crop away threats to fill a phone screen.

Draw floors -> floor stains/shadows -> depth-sorted units/props -> appropriate effects -> UI. Use a shared foot-pivot convention for Y sorting. Do not rotate a directional character sprite through arbitrary angles; select a facing animation. Ensure foreground props cannot hide essential warnings.

Start with ordinary sprite rendering and sensible atlases. MultiMesh is a possible measured optimization for repeated objects, not a blanket solution: per-unit depth ordering, animation frame selection, and culling need explicit handling. Godot documents whole-MultiMesh rather than individual-instance culling; its optimization page also carries an update warning, so verify behavior in the pinned engine. [MultiMesh documentation](https://docs.godotengine.org/en/stable/tutorials/performance/using_multimesh.html).

Godot's multiple-resolution controls provide the layout/scaling tools, but the project still needs real aspect-ratio tests. [Multiple resolutions](https://docs.godotengine.org/en/stable/tutorials/rendering/multiple_resolutions.html).

## 8. Performance budgets: targets, not claims

Establish named reference devices in M0 using hardware actually available to the team. Do not publish minimum specs until release-build measurements support them.

| Budget | Initial target |
|---|---|
| Designed regular-enemy peak | 250 simultaneously active, same gameplay limit across platforms |
| Stress scenes | 500 and optionally 1,000; diagnostic only, no marketing promise |
| Desktop reference | 60 FPS at a tested output resolution |
| Lower-end mobile reference | Stable 30 FPS; optional 60 FPS on devices that sustain it |
| Warm test length | At least 30 minutes with repeated restarts and late-run scenarios |
| Active arena texture residency | Aim below 128 MiB; measure imported textures, not PNG download size |
| Whole-process mobile memory | Initial investigation threshold around 350 MiB, not a guaranteed platform limit |
| Initial complete game download | Aim below 250 MB, revisable with measured audio/art needs |

A useful frame-time goal is desktop 95th-percentile frame time at or below 16.7 ms and lower-end mobile at or below 33.3 ms. Record 99th-percentile spikes separately and investigate recurring spikes; mean FPS alone is insufficient. Report device, OS, engine version, build type, renderer, resolution, seed, enemy count, effects settings, and whether the device was already warm.

The representative benchmark includes actual animated enemies, player combat, projectiles, status effects, deaths, pickups, audio, and UI. A thousand static unlit sprites are not an equivalent test.

Scale cosmetic cost first: blood history, corpse count, smoke, particles, decorative lights, and resolution. Do not hide real enemy projectiles, omit damage zones, lower the enemy count, or change difficulty on slow devices. If the shared encounter is too expensive, optimize it or revise the global encounter target and re-test every platform.

Use bounded corpse/stain collections; consider compositing old cosmetic marks into limited chunks after profiling. Watch fill rate and transparent overdraw. Flat sprites are not automatically cheap when textures, overlapping effects, and simulation grow.

## 9. Mobile from the same project

Android debug export belongs in M0 if a device/toolchain is available; otherwise record the blocker explicitly. It is not evidence of mobile readiness until installed and played on physical hardware. Keep Android checks at every milestone.

Schedule an iOS feasibility build by M1/M2 when Mac and iPhone access is available, rather than discovering plugin/renderer issues after Steam launch. Godot documents native Android export; iOS export requires macOS with Xcode and appropriate project/signing setup. [Android export](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_android.html), [iOS export](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_ios.html).

Shared content/code does not imply that mobile is only 5% of the work. Test touch occlusion, safe areas, DPI, text, input cancellation, interrupted audio, app backgrounding, screen locking, process termination, memory pressure, heat, battery use, controller attachment, and store packaging.

Maintain one gameplay implementation. Platform-specific adapters cover storage paths/capabilities, lifecycle events, purchases only if later selected, achievements, and store integrations. Input types are not platform types: a phone may use a controller and a PC may expose touch.

Landscape is the release baseline. Portrait is excluded until explicitly designed and tested as its own layout.

## 10. Saving and interrupted runs

Separate `profile` (unlocks/results), `run_checkpoint` (resumable run), and `settings` (device-specific preferences). Version their schemas independently where useful. Keep at least one previous-good profile.

Write to a temporary sibling file, validate it, then replace the active file using the safest supported local-filesystem operation. Test interruptions around each step; do not promise absolute power-loss safety merely because a rename is used.

Profile saves occur after confirmed results or unlock changes. Run checkpoints occur at key transitions and a bounded periodic interval, initially 15 seconds, with additional lifecycle attempts on backgrounding. Unexpected termination can lose progress since the last completed checkpoint. Serialization must not stall late-run combat; measure duration.

A run checkpoint needs phase/time, random-stream state, player state, equipped weapons/ranks, cooldowns, enemies, projectiles or a documented equivalent reconstruction policy, statuses, pickups, terminal state, and encounter budget. Exact restoration of relevant gameplay state is the default; simplifying it requires documented fairness tests.

M0 only needs a settings or smoke-test persistence path. Full interruption-safe run restoration is a later milestone and a mobile release blocker. Implement migration, corruption handling, version rejection, and a visible recovery path. Never silently erase the only usable profile.

Steam Cloud may later sync profile/run files through Steam's supported mechanisms. Keep device bindings and graphics settings local. Steam Cloud is not automatic PC/Android/iOS cross-save. Cross-store saves would require a separate identity/sync design and are excluded initially. [Steam Cloud documentation](https://partner.steamgames.com/doc/features/cloud).

## 11. Steam and platform services

The game must launch and run without Steam during development. Start with a local/no-op platform implementation. Later select a maintained Godot-to-Steamworks binding, test it against the pinned engine and required architectures, and lock its exact revision before release.

Keep achievement and cloud calls outside combat/player code. Handle missing Steam, offline startup, user changes, failed initialization, and cloud conflicts. Do not fabricate platform success when the adapter is absent.

Initial Windows release may be tested on Steam Deck through Proton. A native Linux export is optional and should be selected only after comparing real compatibility/support costs. Do not advertise Deck Verified before Valve grants that status. Valve's review covers controls, legibility, configuration, and compatibility; a working keyboard/mouse build alone is not sufficient. [Valve compatibility guidance](https://partner.steamgames.com/doc/steamhardware/compat).

No service-role keys, account backend, Redis, Supabase, remote balance editor, or mandatory telemetry is needed for this scope.

## 12. Testing, CI, and delivery

M0 creates the real project and a small test runner. Once present, expected commands include:

```sh
godot --headless --path game --editor --import --quit
godot --headless --path game --script res://tests/run_tests.gd
```

These are intended project commands, not commands successfully executed during pre-production. Verify them against the installed pinned engine and actual test runner. A missing runner is a failure, not a skipped green check.

Test: movement normalization, cooldowns, hit-once semantics, pool reuse, weapon definitions, upgrade eligibility, modifier caps, XP thresholds, win/death resolution, random-stream separation, save migrations, and interrupted-write recovery. Add smoke tests for boot -> play -> death/result -> restart without accumulating run state.

CI should import the project, run tests, validate data and asset records, then produce unsigned development exports where the runner supports them. Pin tools/actions to reviewed versions/commit hashes. Do not expose signing keys to untrusted pull requests. Release uploads, Steam credentials, and app-store signing remain manual/secured workflows until deliberately authorized.

Headless CI cannot validate touch usability, audio, animation quality, rendering correctness, or actual device performance. Those require recorded manual checks. Every delivery reports what ran, what failed, and what was not tested.
