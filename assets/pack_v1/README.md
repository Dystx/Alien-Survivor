# Official Asset Pack v1

**All five enemy families now have first-pass animation candidates: runner 84, spitter 108, charger 124, brute 112, Brood Warden 240 — 668 frames total. The exact selected 43-cell HumanReview appearance remains locked. Structural coverage is not final art approval or a finished release.**

Read `player_visual_lock.json` first, then `SPEC.md`, `pack.json` and `BATCH_001.md`. The human lock overrides old robot/visor proposals. Do not regenerate, recolour, rescale or replace the selected person to accommodate weapon or animation defects.

## Current families

| Family | Current source | Coverage | Approval |
| --- | --- | --- | --- |
| Selected human | Exact HumanReview ZIP/atlas hashes in `player_visual_lock.json` | 43 preserved cells | Appearance locked; firing/full action coverage separate |
| Runner | `source/runner_family.py`, `families/runner/` | 84 frames, five actions, four views | Pending |
| Spitter | `source/spitter_family.py`, `families/spitter/` | 108 frames, seven actions, four views | Pending |
| Charger | `source/charger_family.py`, `families/charger/` | 124 frames, seven actions, four views | Pending |
| Brute | `source/brute_family.py`, `families/brute/` | 112 frames, seven actions, four views | Pending |
| Brood Warden | `source/warden_family.py`, `families/brood_warden/` | 240 frames, ten actions, four views | Pending |

Each family has individual RGBA PNGs, one editable mesh/pose source, recipe, source/frame hashes, review atlas and normal/half-speed previews. Shared rendering settings keep the camera/light/scale consistent. GLBs carry editable geometry and movement tracks; other action poses remain in the Python source. These are not ten-action skinned production armatures or independently generated still sheets.

## Latest delivery: Brood Warden

Actual asset commit **7087d5ed437ad3ddedaeadf5996d3344a7e122a3**. Publication run **35217222740** passed 15 real-image/model checks plus existing contract checks before committing the boss family only. Prior family and human-lock trees were preserved.

The master has a broad thorax, dorsal crown, four heavy limbs and two articulated secondary tendrils. Ten actions: idle, move, charge preparation, charge, acid attack, pulse attack, recovery, hit, phase transition, death. Fixed 256x256 cells and pivot 128,204; five 1820x1820 atlases respect the 2048 limit. No frame is resized independently.

Integration: draft **PR #8**, branch `feat/warden-animation`, final tested commit **5a9d18b50943e74a01df4de9a6c50cf574f55b01**.
Run https://github.com/Dystx/Alien-Survivor/actions/runs/35218624039 passed Godot 4.7.2 import/compilation and **489 assertions**: 74 gameplay, 27 human, 64 firing, 48 runner, 58 spitter, 64 charger, 59 brute, 95 boss. The intentional failure control and all scene checks passed. Warden combat/review ran headlessly and with software OpenGL; five actual-art captures cover charge, acid, phase, death and a native pulse view.

The boss presentation reads existing attack timers, locked aim and movement distance. It never causes damage. Warnings/dashes/releases take priority over hit and phase poses. The cosmetic phase display waits for a stationary non-attacking interval and can be deferred or interrupted; actual phase-two rules start immediately, without new invulnerability. Simulation victory settles immediately on death, while only the results panel waits for the 1.25-second fall. The living human stays alive; simultaneous death remains defeat. A deferred GUI-focus error exposed by rapid results/menu rebuilding was corrected without weakening the error checks.

The successful CI run used actual committed images for all five aliens. Human/scenery/effect textures in automated game checks were explicit fixtures, not the selected human's pixels. Fixtures are excluded from the complete conversation package. Actual Warden reviewer captures are engine images, not mockups. No full-scene Mac aesthetics, audio, physical inputs, mobile, performance, exported-build or final-art approval is implied.

The complete `Alien_Survivor_Warden_Pass.zip` is supplied in the project conversation. All 240 boss PNGs match the committed/tested files; 606 inherited protected image/model/core-script files are unchanged, including the human and existing controllers. All 26 corresponding runtime script hashes match the successful run. Import the ZIP's root `project.godot`, then **Diagnostics → Warden Animations** or **Boss Test**. Review all four views or each native direction, pause, half speed, frame scrub, replay and backgrounds. Existing preview loadout and normal combat balance are unchanged.

## Next priority: one real-art repository checkout

The asset branch contains actual current alien binaries and source. The integration branches still contain patches and verification setup; the conversation ZIP supplies the whole art-equipped game. The selected human/scenery binaries are not yet fully consolidated in a directly runnable repository game checkout. This is a concrete remaining task, not solved by another ZIP or another plan.

Next work should assemble the existing actual selected-human, scenery and five alien packs with tested gameplay in one reviewed, directly runnable checkout. Preserve the human's exact hashes. Do not include CI fixture pixels, silently merge a staging branch, substitute a different procedural human, or leave several competing current masters. Review the integration chain deliberately; do not change main without the owner's merge instruction.

After consolidation: visual refinement and approval of all alien candidates/firing, final attached mouth/pulse/acid effects, coherent environment/pickup/UI polish, remaining player action coverage without redesigning the locked body, and end-to-end real-art playtests. Then test desktop exports/Steam packaging. Mobile comes later. Do not add more monsters, maps or systems merely to inflate progress.

## Earlier evidence and timing distinctions

Runner asset `b6203e225bb34b1a30efc5d0a13d85e1e4803506`; standalone viewer `art_reviews/runner_lab/project.godot`; actual-art run `35175038064` passed 45 viewer checks and produced captures.

Spitter asset `3a4d3b6acce17cf45deb14ff282f5daaf7f25c37`; PR #5/run `35177460586`. Mouth sockets exist, but final attached acid emission remains pending.

Charger asset `271ea45aa42e497dc323e808aa8e6d07a906bac4`; PR #6/run `35212057317`. Existing simulation owns warning/dash/recovery and locked attack direction.

Brute asset `a9f2c3e851599ed6b4a6b5f78109c908d9636fdc`; PR #7/run `35214395321`. Continuous contact damage and 20% armour reduction remain unchanged. Its wind-up is reviewer-only, not a newly telegraphed slam or safe window. Contact gestures are cosmetic.

Human firing correction: `fix/locked-human-firing`; run `35172540277` verified its source with fixtures. Visual approval remains pending; see its owning `firing_review/README.md`.

## Authority and approval gates

The obsolete automatic player renderer remains disabled. Older procedural-player files still visible here are superseded experiments, not the approved person. The exact selected human lives in its identified conversation package, bound by `player_visual_lock.json`. More frame slots in a different model do not fulfill that lock.

The catalogue remains 91 entries / 1,134 planned frame slots. These are requirements, not completion percentages. Audits may count obsolete unapproved drafts; a green test is not artistic approval. Keep one current source/frame/delivery per family, with history in Git rather than parallel final/archive/rejected masters.

```sh
python3 -m pip install -r tools/requirements-artpack.txt
python3 -m unittest discover -s tests -p 'test_artpack*.py' -v
python3 tools/artpack.py audit
python3 tools/artpack.py check-family brood_warden
```

The production exporter requires complete families, explicit owner approval and source permission. No command fabricates approval. Hashes establish byte identity, not quality or legal ownership. No fonts, restricted stock source, credentials or signing files belong in the public pack. Never present a fixture-staging checkout as the complete real-art game.
