# Official Asset Pack v1

**Current artwork: runner 84 candidate frames; spitter 108 candidate frames. The owner's exact 43-cell HumanReview appearance is locked separately. No full pack or alien family has final owner approval.**

Read `player_visual_lock.json`, then `SPEC.md`, `pack.json` and `BATCH_001.md`. The human lock overrides older robot/visor proposals and does not authorize replacing the selected human with another procedural model.

## Current families

| Family | Current source | Coverage | Status |
| --- | --- | --- | --- |
| Selected human | Exact HumanReview ZIP/atlas hashes in `player_visual_lock.json` | 43 preserved cells | Appearance locked; firing and full action coverage are separate |
| Runner | `source/runner_family.py`, `families/runner/` | 84 frames, five actions, four views | Review candidate |
| Spitter | `source/spitter_family.py`, `families/spitter/` | 108 frames, seven actions, four views | Review candidate |

Individual PNGs, editable masters/recipes, source hashes, review atlas and previews belong to each canonical family. One current source per family; no independent per-frame image generations and no parallel final/archive/rejected masters.

Spitter asset commit: `3a4d3b6acce17cf45deb14ff282f5daaf7f25c37`. It has idle, move, wind-up, attack, recovery, hit and death in e/s/w/n; 128x128 cells and ground pivot 64,104. Glands inflate and the jaw moves; limbs and camera stay consistent. The GLB includes movement; every action remains editable in the Python pose source. The modeled surface finish still needs owner visual review.

The spitter render/publication workflow `35177027250` passed its 12 real-image/model tests and the existing contract tests. The separate `feat/spitter-animation` integration run `35177460586`, at `53dbe6218a29a3ca1de6b881ea31739e7df65cd7`, passed Godot import and 271 assertions (74 gameplay, 27 human, 64 firing, 48 runner, 58 spitter), scene checks and actual spitter viewer captures. Real runner/spitter atlases were used; human/scenery/effect images in CI game checks were explicitly synthetic fixtures. No Mac, performance, balance or artwork approval follows from these tests.

## Review and integration

The runner's standalone native viewer is at repository-root `art_reviews/runner_lab/project.godot`; its 45 actual-art playback checks and captures are recorded in run `35175038064` at `f0109fc70f0fa623daf4ff3255c9f883f3b6ef1a`.

The complete conversation-delivered Spitter Pass game exposes **Diagnostics → Spitter Animation Review** and **Spitter Test / Two Targets**. Integration source is on `feat/spitter-animation`; the official asset branch stores the spitter PNGs, source, metadata and review outputs, not a complete art-equipped game checkout. The approved human/scenery binary consolidation is still unfinished. Do not merge fixture staging as a production game.

Spitter gameplay animation reads existing warning/recovery timers and real displacement; it does not generate damage. Existing acid projectile/puddle effects remain prototypes. Mouth socket coordinates are recorded, but their full emission-to-projectile VFX attachment pass is not included. Normal gameplay balance, human pixels, firing source and runner source stay unchanged.

## Preserve the selected human

Do not redraw, recolour, rescale or replace the body identified by `player_visual_lock.json`. The procedural player frames still visible in this branch are superseded experiments, not the approved person. The obsolete player-rendering automation is disabled. Do not run it against the locked human.

The separate `fix/locked-human-firing` correction passed run `35172540277` with synthetic textures. Its visual approval remains pending. See that branch's owning `firing_review/README.md`; a green test is not permission to redesign the human.

## Contract and approval checks

The full catalogue remains 91 named entries / 1,134 required frame slots. Those are requirements, not completion figures. Audit counts may include old unapproved drafts; never treat that as approval of the rejected player's appearance.

```sh
python3 -m pip install -r tools/requirements-artpack.txt
python3 -m unittest discover -s tests -p 'test_artpack*.py' -v
python3 tools/artpack.py audit
python3 tools/artpack.py check-family runner
python3 tools/artpack.py check-family spitter
```

Only after a complete family has explicit owner approval and source-rights review may the approved-only exporter be used:

```sh
python3 tools/artpack.py export --asset spitter --out art_build/pack_v1
```

No command fabricates approval. Review native-size and half-speed movement, anatomy, alpha, pivots, seams and weapon/attack timing. Checksums cannot establish artistic quality or legal ownership. No fonts, restricted stock source, credentials or signing files are included.

Next bounded family is the charger; do not widen the catalogue or silently promote the runner/spitter finish to approved production. Preserve the current sources while visual review is pending.
