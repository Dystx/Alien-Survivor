# Alien Survivor — human animation review

Steam-first, sprite-based 2.5D survival game. This branch replaces the robotic player draft with an unhelmeted human survivor and provides a consistent set of six animated actor candidates.

**Review build, not final-art approval.** The owner approved the human design direction, not every resulting model or animation. The models still need visual refinement toward the detailed gritty reference.

## Actual contents

- `assets/pack_v1/families/`: 892 PNG frame slots covering the human player, runner, spitter, charger, brute and Brood Warden.
- `assets/pack_v1/source/complete_actors.py`: stable editable geometry and poses; no independent per-frame image generations.
- `assets/pack_v1/pack.json` and `SPEC.md`: the single current specification. Revision 0.2.0 explicitly adopts the human design and larger fixed canvases for complete death/attack bounds. No frame is independently zoomed to fit.
- `integration_review/assets/motion_review/`: trimmed review atlases with exact pivot and muzzle metadata.
- `integration_review/scripts/` and `integration.patch`: actor-state selection, runtime integration and an interactive Godot Animation Lab.
- `integration_review/reviews/`: current human/alien moving previews. The older root `art_reviews` images are superseded motion experiments, not the current human design.
- `integration_review/verification/`: actual engine logs and tested-script hashes.

The original gameplay remains on its own branch. Neither `main` nor `feat/first-playable` is changed by this review branch. The full scenery-equipped Godot source package is supplied in the project conversation; the repository contains the actor pack and integration source, not a signed executable.

## Animation coverage

| Actor | Frame slots, four facings |
| --- | ---: |
| Human survivor | 224 |
| Runner | 84 |
| Spitter | 108 |
| Charger | 124 |
| Brute | 112 |
| Brood Warden | 240 |
| Total | 892 |

Player actions include idle, forward/backward walking, left/right strafing, shooting, walking while firing, hit and death. Enemy actions follow their declared movement/attack/warning/recovery/death lists. The lab exposes every declared clip; combat chooses clips from simulation state. Enemy hit effects do not continually reset movement, and not every lab-only pose has a unique combat trigger yet.

The complete official catalogue still has 1,134 required frame slots. The remaining non-actor catalogue is not complete; the review game retains previous environment/effect prototypes. **Zero families have final owner approval.**

## Verification already recorded

GitHub Actions run `35156482619` rendered the real actors, checked the asset deliveries, imported the real actor atlases with Godot 4.7.2, and passed 74 gameplay plus 18 motion checks and the intentional failure control. Combat and Animation Lab smoke checks passed headlessly and with software OpenGL. Old scenery was explicitly replaced with fixtures only during CI, so the test does not prove the appearance of the complete scenery-equipped package.

Mac, mobile, controllers, audio listening, final aesthetics, exports and human gameplay balance still need testing. Local regenerated PNG bytes can differ from CI render bytes; each delivery records its own hashes. No cross-driver pixel identity is claimed.

## Review in Godot

In the complete conversation package, import the root `project.godot`, allow PNG import, and run the project. Use **Animation Lab / Six Actors** to inspect all clips and four views at normal/half speed, or **Deploy / Survival + Boss** to play. The lab is a native Godot screen, not a website or a new web game.

Keep the production approval gate: do not promote the candidate atlases to approved output or merge this branch solely because tests are green. The next review is human proportions, clothing, gait weight, limb joins, gun alignment and the desired gritty surface detail.
