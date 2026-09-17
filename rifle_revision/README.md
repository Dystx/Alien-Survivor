# Rifle trajectory correction — tested core source

The owner reported that bullets appeared to curve and seek the target. The current complete input is the conversation-delivered Creature Finish project at local commit `92666ca1527916080f29bb6c7caa370ff9ab8336`, not the old art-only checkout on this branch.

## Diagnosis

The old physics velocity was constant. However, `firing_presentation.gd` blended the displayed muzzle offset to `Vector2(0,-18)` across the first 110 world units. That changed the visible slope partway through flight and looked like homing. The new regression includes a negative control that detects the old bend.

## Implemented core

- `ballistics.patch`: exact simulation diff against Creature Finish. A bullet stores its immutable origin and range, uses one velocity chosen at launch, and retains no target object. Auto-aim chooses a point at the trigger, not during flight.
- `firing_presentation.gd`: exact tested replacement. Rifle rendering uses a constant projection offset, with no mid-flight blend or pull toward a current target. Pure calibrated muzzle geometry aligns physics and drawing without modifying the approved human pixels.
- `straight_shot_tests.gd`: the 41 executed regression assertions for muzzle alignment, straightness across the old blend boundary, target/shooter movement, subsequent automatic shots, free directional aim, close targets, cover, exact impact points, hit sockets, pause and invalid vectors.

The short body-to-muzzle segment is collision-tested before spawning a round, so muzzle placement cannot bypass cover or skip a touching enemy. Flight uses swept collision on the same displayed ray. Impact events record the real contact position, not merely the enemy centre. Damage, firing interval, speed and range values remain unchanged; the launch geometry and ray are intentionally corrected.

Caller wiring in the complete game computes `View.Firing.launch_geometry(view.human, dt, View.HUMAN_SCALE)`, adds `intent.get("aim_point", Vector2.INF)`, and passes that fourth argument to `sim.step`. Mouse intent now includes the existing unprojected cursor point; sticks remain direction-only. The view passes the current simulation events to `firing.advance` so the flash uses the actual shot axis. These three files are reviewable core source, NOT a self-contained playable checkout or an automatic patch installer. Do not overwrite an unknown project with them.

## Complete tested delivery

The complete Straight Shots source ZIP also includes all caller changes, manual reticle, depth-sorted projectile drawing, exact-contact feedback, a native Field Lab trajectory range, 48 new graphical checks, explicit preservation records and the updated Git bundle. No prior ZIP is required to play that complete package. The range supports moving target/shooter, pause, quarter speed, cursor aim and sampled launch-ray guides.

Executed locally with the pinned Godot 4.7.2 engine and actual included artwork:

- Import/compilation passed.
- 565 Godot gameplay/animation/effect/trajectory assertions passed (previous 524 plus 41 new).
- 65 Python checks passed.
- 139 graphical checks passed (previous 91 plus 48 new).
- Intentional failing runner control and the old-bend negative control behaved as required.
- Moving shooter/target samples stayed within 0.01 screen pixels of their frozen launch rays.
- 906 inherited sprite/model/preview files are byte-identical; the exact approved human atlas remains `e77d10fbeda8fa5ee3532e3e1b5618ce4f0e3084458af4c4745ed1f49ed9ba2c`.

All scenes used actual human, enemies, scenery and effects, not texture fixtures. Graphical execution was Linux Compatibility OpenGL with Mesa llvmpipe/Xvfb, not a Mac/device or performance test. A separate 96-frame engine recording captures the range at quarter speed.

## Publication and remaining limits

This branch commits the core correction source and regression tests. The complete consolidated game and newer artwork still require the included full-project Git-bundle transfer to `feat/consolidated-game`. This is not a claim that those binaries are now uploaded, that remote CI ran this complete build, or that main was merged.

Four baked gun views still limit visual alignment with every free aiming angle. This correction does not redraw the locked human, add homing, quantize aiming or complete player animation coverage. The retained hostile acid effect has its separate cosmetic loft; it was not converted into rifle ballistics. Creature/art approval, final environment/VFX polish, physical controls/audio, human-played balance, desktop exports and Steam release remain separate work.
