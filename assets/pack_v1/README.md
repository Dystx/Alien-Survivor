# Official Asset Pack v1

**Current alien candidates: runner 84 frames, spitter 108, charger 124. The owner's selected 43-cell HumanReview appearance is locked separately. The full pack and alien artwork are not finally approved.**

Read `player_visual_lock.json` first, then `SPEC.md`, `pack.json` and `BATCH_001.md`. The exact human lock overrides older robot/visor proposals and does not authorize another procedural player model.

## Current families

| Family | Current source | Coverage | Status |
| --- | --- | --- | --- |
| Selected human | Exact HumanReview ZIP/atlas hashes in `player_visual_lock.json` | 43 preserved cells | Appearance locked; firing and full action coverage separate |
| Runner | `source/runner_family.py`, `families/runner/` | 84 frames, five actions, four views | Review candidate |
| Spitter | `source/spitter_family.py`, `families/spitter/` | 108 frames, seven actions, four views | Review candidate |
| Charger | `source/charger_family.py`, `families/charger/` | 124 frames, seven actions, four views | Review candidate |

Individual PNGs, editable master/recipe, source hashes, review atlas and previews belong to each canonical family. One current source per family, not unrelated per-frame image generations or parallel final/archive/rejected masters.

## Charger delivery

Actual asset commit **271ea45aa42e497dc323e808aa8e6d07a906bac4**. It contains idle, move, wind-up, charge, recovery, hit and death in e/s/w/n, fixed 128x128 cells and pivot 64,104. Forward-heavy thorax, ivory keratin wedge head, muted ember markings and no acid sacs. The wind-up plants all four feet; the charge has its own articulated gait; recovery settles back and directional death holds a corpse. The GLB includes the editable meshes and movement track; other actions remain in the pose source.

Publication workflow **35211400077** passed 14 real-image/model checks and the contract checks before committing the charger-only files. Selected human, runner, spitter and human lock tree were unchanged.

Integration is in draft **PR #6**, branch `feat/charger-animation`, tested commit **8a1366285cec82261cd6fd45af0a71fe8b4a4760**. Run https://github.com/Dystx/Alien-Survivor/actions/runs/35212057317 passed import/compilation and **335 assertions**: 74 gameplay, 27 human, 64 firing, 48 runner, 58 spitter and 64 charger. Negative control and all creature/firing/finale scene checks passed; charger combat/reviewer also ran with software OpenGL. Actual charger viewer captures were retrieved and inspected.

CI imported real charger, runner and spitter atlases. Human/scenery/effect textures in game checks were inherited explicit fixtures. They are not included in the complete conversation-delivered game. No Mac/mobile, sound, physical-input, performance, exported-build or final-art approval follows from the test run.

The full source game `Alien_Survivor_Charger_Pass.zip` is supplied in the conversation. All 124 packaged charger PNGs match the committed/engine-tested files. All 367 protected files from Spitter Pass, including the selected human pixels and prior actor/firing/simulation controllers, are unchanged. All 22 corresponding runtime GDScript hashes match the successful engine run.

Open the ZIP's root `project.godot`, then **Diagnostics → Charger Animations** or **Diagnostics → Two Chargers**. Creature diagnostic buttons now share rows rather than growing the menu vertically. Extra target health is diagnostic-only; normal-run damage, collision, targeting and timers are unchanged. The attack presentation uses the existing locked direction and warning/dash/recovery timers. Animation never authorizes damage.

## Earlier review work

Runner asset commit `b6203e225bb34b1a30efc5d0a13d85e1e4803506`; standalone viewer at repository-root `art_reviews/runner_lab/project.godot`. Run `35175038064` verified actual PNG loading, 45 viewer checks and captures.

Spitter asset commit `3a4d3b6acce17cf45deb14ff282f5daaf7f25c37`; seven actions and recorded mouth sockets. Integration PR #5 / run `35177460586` used real spitter and runner images. Its full mouth-to-projectile effects attachment remains unfinished; existing acid effects are prototypes.

The separate `fix/locked-human-firing` correction passed run `35172540277` with synthetic textures. Its visual approval is pending. See that branch's owning `firing_review/README.md` for the exact scope.

## Protect the selected human and source authority

Do not redraw, recolour, rescale or replace the body identified by `player_visual_lock.json`. Older procedural player frames still visible here are superseded experiments, not the approved person. The obsolete player-rendering automation is disabled. Do not run it against the locked human.

The actual approved human/scenery binary consolidation into a complete repository game checkout is still unfinished. This asset branch holds the current alien sources/frames and approval records; integration branches hold source patches and engine checks. The conversation ZIP supplies the complete art-equipped source game. Never present or merge a fixture-staging checkout as that complete game.

## Contract and approval checks

The full catalogue remains 91 named entries / 1,134 planned frame slots. These are requirements, not completion. Audits may count old unapproved drafts; that is not approval of the rejected player or the finished pack.

```sh
python3 -m pip install -r tools/requirements-artpack.txt
python3 -m unittest discover -s tests -p 'test_artpack*.py' -v
python3 tools/artpack.py audit
python3 tools/artpack.py check-family charger
```

Only after a complete family has explicit owner and source-rights approval may the approved-only exporter run:

```sh
python3 tools/artpack.py export --asset charger --out art_build/pack_v1
```

No command fabricates approval. Review native-size and half-speed motion, anatomy, alpha, pivots, seams and attack timing. Checksums cannot establish artistic quality or legal ownership. No fonts, restricted stock source, credentials or signing files belong in this pack.

**Next bounded family: brute.** Charger/runner/spitter finish and transition weight remain unapproved candidates; do not silently treat them as final production quality. Keep the selected human unchanged and do not widen the content catalogue.
