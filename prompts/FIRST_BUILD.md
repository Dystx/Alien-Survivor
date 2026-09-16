# M0: first playable combat prototype

Use this brief with the implementation agent connected to `Dystx/Alien-Survivor`.

## Context

The repository was initialized with planning documents, not a game. Read `README.md`, `AGENTS.md`, `docs/GAME_DESIGN.md`, `docs/TECHNICAL_PLAN.md`, and `docs/ART_AND_ASSETS.md`. Inspect the current branch before making changes; there may now be implementation work from another session.

Alien Survivor is a Steam-first alien survival roguelite with flat retro 2D graphics and later native Android/iOS exports. This task is a technical combat prototype, not the final visual sample and not the complete game.

## Goal

Produce a bootable, restartable Godot prototype that demonstrates movement, automatic fire, manual aim override, approaching enemies, damage, death, and honest diagnostic information. Keep the code ready for a touch-input path without creating a second gameplay implementation.

## Required steps

1. Create a feature branch. If code already exists, build on it rather than generating a parallel project. Summarize the starting state.
2. Create `game/project.godot` with Godot 4.7.2 stable, standard/GDScript build, Compatibility rendering, matching export templates where available, and a visible boot scene. Record the engine pin in `.godot-version`. Keep documentation outside the exported game content.
3. Establish a fixed 16:9 combat reference and a separately laid-out HUD. Use a small original placeholder arena with a boundary and a few clear blockers. Do not spend this milestone producing final art.
4. Implement an input-intent path for movement, aim override, and pause. Support WASD and controller input. Include a simple adjustable touch movement control and right-side aim override if feasible in this milestone; do not claim device testing merely because mouse emulation works.
5. Implement a movable player, one rifle with cooldown-driven automatic fire, and one runner enemy. Automatic targeting picks a valid nearby target; holding the primary mouse button or providing a nonzero aim-stick/gesture overrides the firing direction. Input cannot bypass cooldowns. Respect world blockers.
6. Implement damage, bounded hit detection, simple contact damage, enemy death, player death, and clean restart. Use original placeholder flashes/corpses rather than unlicensed artwork. Put enemy updates in a simple central manager; avoid a separate heavyweight physics/navigation stack per alien.
7. Add pause/resume with cleared input state. Pause menus must consume input. Return from focus loss in a safe paused state. Do not implement full interrupted-run serialization yet.
8. Add a repeatable debug scenario with a seed, controllable enemy counts such as 25/50/100, and a HUD showing live enemies, projectiles, frame time, and engine/build information. Label this as a prototype benchmark, not final game performance. Repeated starts must reset counts and seed-dependent state.
9. Add a small real GDScript test runner for movement normalization, weapon cooldown, hit-once logic, enemy/pool reset behavior, and restart state. Definitions should have stable IDs and must not be mutated globally during play.
10. Add sanitized Windows and Android development-export presets where supported. Keep credentials and machine-specific secrets out of the repository. Export and test a Windows build when possible. Attempt an Android debug deployment only when the SDK/device environment is available; otherwise report exactly what remains to be done. Do not configure production signing or publish builds to stores.
11. Run actual engine import/tests when the toolchain is available. Add a minimal CI check only if its commands can genuinely run against the created project. Do not create a permanently skipped or fake-green workflow.
12. Update README with setup, controls, run/test/export instructions, and the true status. Open a reviewable pull request and report its identifier only if creation succeeds.

## Acceptance criteria

- A developer can follow the README and boot into the arena.
- Movement has no diagonal speed advantage and respects the arena boundary.
- Rifle fire follows its cooldown and damage applies correctly.
- Auto-targeting and manual aim override do not require separate combat code.
- Enemies pursue the player without passing through solid world blockers.
- The player can die, see a simple result state, and restart ten times without leaked enemies, old timers, duplicate signals, or retained run state.
- Pausing does not advance gameplay or preserve stuck movement/fire input.
- The debug scene exposes real values; it does not print an invented FPS target.
- Tests run and fail correctly when a known test condition is broken.
- All imported assets have a known source/rights status; original placeholders are identified as such.
- The delivery distinguishes editor tests, exported-build tests, touch emulation, and physical-device tests.

## Not in this task

No boss, complete fifteen-minute run, XP/upgrade catalogue, meta shop, overload terminals, second map, all weapons, cloud saves, Steam SDK, accounts, multiplayer, advertising, purchases, real-time 3D, or sprite-generation pipeline. Those belong to later milestones. Do not create placeholder architecture for them merely to look complete.

## Intended commands once the project and runner exist

```sh
godot --headless --path game --editor --import --quit
godot --headless --path game --script res://tests/run_tests.gd
```

Verify these against the actual installation. If Godot or export tools cannot run in the environment, state that limitation, perform the checks that are available, and provide reproducible local steps. Do not report unexecuted commands as successful.

## Delivery summary

Return: starting branch/state; implemented changes and important paths; exact checks/results; screenshots or clips only from the actual build if available; exported artifacts if actually produced; device specifications for any measured performance; remaining issues; and a proposed next task limited to M1's combat/art proof.

The result should be a fight we can test, not a large framework with no playable encounter.
