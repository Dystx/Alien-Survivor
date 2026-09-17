# Official Asset Pack v1

**Current regular-alien candidates: runner 84 frames, spitter 108, charger 124, brute 112 — 428 total. The owner's exact 43-cell HumanReview appearance is locked separately. Candidate coverage is not final art approval or a finished game release.**

Read `player_visual_lock.json` first, then `SPEC.md`, `pack.json` and `BATCH_001.md`. The selected human overrides the obsolete robot/visor proposals. Do not regenerate, recolour, rescale or replace that body to accommodate weapon or animation defects.

## Current families

| Family | Current source | Candidate coverage | Approval |
| --- | --- | --- | --- |
| Selected human | Exact HumanReview ZIP/atlas hashes in `player_visual_lock.json` | 43 preserved cells | Appearance locked; firing/full action coverage separate |
| Runner | `source/runner_family.py`, `families/runner/` | 84 frames, five actions, four views | Pending |
| Spitter | `source/spitter_family.py`, `families/spitter/` | 108 frames, seven actions, four views | Pending |
| Charger | `source/charger_family.py`, `families/charger/` | 124 frames, seven actions, four views | Pending |
| Brute | `source/brute_family.py`, `families/brute/` | 112 frames, seven actions, four views | Pending |

Each current family contains individual PNGs, editable mesh/pose source, recipe, source/frame hashes, review atlas and normal/half-speed previews. Shared renderer settings keep the camera/light/scale consistent. No unrelated image is silently promoted as a production frame. GLBs carry editable geometry and locomotion; other actions remain in each family's pose source.

## Latest delivery: brute

Asset commit **a9f2c3e851599ed6b4a6b5f78109c908d9636fdc**; publication run **35213874096** passed 13 real-image/model checks plus contract checks. The body has an independent broad thorax, heavy four-limb footprint and layered charcoal keratin shell. Fixed 160x160 cells, pivot 80,136. It is not just a larger runner.

Integration: draft **PR #7**, `feat/brute-animation`, tested commit **b602e5a2cc6a7a047fbe1a319b9cba3f20d0fc59**. Run https://github.com/Dystx/Alien-Survivor/actions/runs/35214395321 passed Godot 4.7.2 import/compilation and **394 assertions**: 74 gameplay, 27 human, 64 firing, 48 runner, 58 spitter, 64 charger, 59 brute. Negative control and all creature/firing/finale scene checks passed; brute combat/reviewer also executed with software OpenGL. Actual viewer captures show move, attack and death.

The four regular-alien atlases were real committed PNG files. Human/scenery/effect images in automated game checks were explicit fixtures, not the selected person's pixels. Fixtures are excluded from the complete conversation game package. No full-Mac-scene, sound, physical-input, phone, performance, exported-build or aesthetic approval is implied.

The complete `Alien_Survivor_Brute_Pass.zip` is supplied in the project conversation. It preserves 487 selected inherited image/model/core-script files, including the exact human and prior controllers; all 24 corresponding runtime GDScript canonical hashes match the successful engine run. All 112 brute PNGs match the committed/engine-tested images. Import its root `project.godot`, then **Diagnostics → Brute Animations** or **Two Brutes**. Extra target health is diagnostic-only.

The brute's existing continuous-contact damage and 20% armour reduction remain unchanged. Attack/recovery gestures are cosmetic. **Wind-up is reviewer-only**, not a newly telegraphed slam, safe contact window, stun or animation-driven damage event. Gait follows actual displacement; deaths hold their final pose with bounded cleanup.

## What remains

1. **Boss family:** replace earlier Warden still/prototype artwork with coherent movement, attack, transition and death animations; retain existing battle rules unless separately changed.
2. **Visual completion and review:** refine/approve all four alien candidates; accept or revise firing; resolve remaining player aiming/strafe/reverse/idle/death coverage without redesigning the locked human. More frame files are not automatically better animation.
3. **Environment, effects and UI:** unify floors/walls/props, infestation, pickups/icons and attack effects. Complete spitter mouth-to-projectile attachment and effect timing. Use the existing small game's needs, not new content for its own sake.
4. **Repository consolidation:** publish the exact selected human/scenery binaries and assemble one directly runnable real-art Godot checkout. Review/merge the integration chain deliberately; remove obsolete robot/current-source ambiguity and fixture staging from the runnable tree. This is still unfinished, not solved by another ZIP.
5. **Release pass:** end-to-end playtests with actual full-scene artwork, input/audio/menu polish, balance and performance testing, save/restart checks, and tested desktop exports/Steam packaging. Mobile comes later, not before the initial desktop release.

Next bounded art task is the boss; then consolidate the actual game checkout before expanding the catalogue. Do not add more monsters, maps, systems or planning layers to inflate progress.

## Earlier evidence

Runner asset `b6203e225bb34b1a30efc5d0a13d85e1e4803506`; standalone viewer `art_reviews/runner_lab/project.godot`; actual PNG/resource run `35175038064` passed 45 viewer checks and captured actual art.
Spitter asset `3a4d3b6acce17cf45deb14ff282f5daaf7f25c37`; integration PR #5/run `35177460586`. Mouth sockets exist, dedicated acid-emission attachment remains pending.
Charger asset `271ea45aa42e497dc323e808aa8e6d07a906bac4`; integration PR #6/run `35212057317` passed 335 assertions before the brute addition.
The selected-human firing correction is on `fix/locked-human-firing`; run `35172540277` verified its source using fixtures. Visual approval is pending; its owning `firing_review/README.md` records the exact scope.

## Authority, contract and checks

The obsolete player-rendering automation is disabled. Older procedural-player files still visible here are superseded experiments, not the approved person. The exact selected human still resides in its conversation-delivered project, bound by `player_visual_lock.json`; do not claim another procedural model's larger frame inventory fulfills that lock.

The official catalogue remains 91 entries / 1,134 planned frame slots. These are requirements, not completion percentages. Structural audits may count obsolete unapproved drafts; this is not artistic approval. Keep one current source/frame/delivery per family, with history in Git rather than parallel final/archive/rejected masters.

```sh
python3 -m pip install -r tools/requirements-artpack.txt
python3 -m unittest discover -s tests -p 'test_artpack*.py' -v
python3 tools/artpack.py audit
python3 tools/artpack.py check-family brute
```

The approved-only exporter remains gated on complete families, actual owner review and source permission. No command fabricates approval. Hashes establish byte identity, not quality or legal ownership. No fonts, restricted stock source, credentials or signing files belong in the public pack. Do not merge a fixture-staging branch as the complete art-equipped game.
