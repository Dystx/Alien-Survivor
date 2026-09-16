# Official Asset Pack v1

**Current artwork: 56 actual locomotion PNG frames, two editable articulated masters, and moving reviews. These are review drafts, not approved runtime families.** The specification, catalogue, validator and approved-only exporter remain the authority.

Read [SPEC.md](SPEC.md), [pack.json](pack.json), then [BATCH_001.md](BATCH_001.md).

The previous generated sheets and prototype ZIP artwork are not the final pack. They are not automatically approved, copied into this tree, or counted as completed frames. The playable project remains unchanged.

## First real motion delivery

- Player: `families/player/frames/walk/{e,s,w,n}/` — 8 frames per direction, 32 total, 128x128 cells, pivot 64,110.
- Runner: `families/runner/frames/move/{e,s,w,n}/` — 6 frames per direction, 24 total, 96x96 cells, pivot 48,78.
- Editable source: family `source/rig.json` plus shared [source/render_motion.py](source/render_motion.py). Each family includes a generated `source/master.glb` with meshes and articulated transform animation, not a skinned armature.
- [Player moving GIF](../../art_reviews/player_walk.gif) and [runner moving GIF](../../art_reviews/runner_move.gif).
- Offline review pages: `art_reviews/player_walk.html` and `art_reviews/runner_move.html` at repository root. Open a local copy in a browser; GitHub displays HTML source rather than executing it.
- [Source and rebuild notes](source/README.md).

The character models are constructed once and genuinely articulated; lighting/camera stay fixed across actual model rotations. These are initial geometry-based motion studies. Armour, creature anatomy/surface detail, weight, foot contact and the four-direction aiming compromise need visual review before final art lock. No approval was fabricated, and no game integration was performed.

The actual first render passed 12 motion/mesh checks plus the 36 existing asset-tool tests in workflow run 35150051887. The official audit reported **56 present / 1,134 required; 0 approved families**. Rendered files were committed at `83a0fff9c8421ccebc938f525330e35078dbbab5`. Passing these checks does not establish final animation quality, Godot runtime behavior, Blender editing or mobile performance.

## Scope

91 named asset entries / 1,134 required frame slots. Six character families: player, runner, spitter, charger, brute and Brood Warden. One industrial biome, props, four weapon presentations, three support modules, combat effects and UI.

Batch 001 is the player's complete base actions plus runner: **212 frame slots**. Player aiming/strafe coverage is an additional production requirement before that family can enter runtime. Actual present/approved counts come from the audit, not this planning total.

## Local checks

Python 3.10+ and Pillow are used for image checks and atlas packing. Dependency version tested for this tool is in `tools/requirements-artpack.txt`.

```sh
python3 -m pip install -r tools/requirements-artpack.txt
python3 -m unittest discover -s tests -p 'test_artpack*.py' -v
python3 tools/artpack.py audit
```

A successful audit means the contract and existing deliveries are structurally valid. It can still print **ART INCOMPLETE / NOT RELEASE-READY**. A valid incomplete catalogue is not a completed art pack.

After a complete family is delivered:

```sh
python3 tools/artpack.py check-family runner
```

After that exact family has real owner approval and recorded source permission:

```sh
python3 tools/artpack.py export --asset runner --out art_build/pack_v1
```

With no `--asset`, the exporter requires the entire catalogue. It refuses incomplete/unapproved production and refuses to overwrite an existing family output. Source and runtime folders stay separate. No command fabricates approval.

## Runtime handoff

The exporter creates `atlas_*.png`, `atlas.json`, `sprite_frames.tres` and `sprite.tscn` per family. Resource paths expect those exports beneath `game/assets/pack_v1/<asset_id>/` in the game repository. Copying/integrating them is a separate reviewed task, not an automatic side effect.

PNG pixels and frame regions can be tested with Python. Godot resource import, intended animation playback, actual art quality, touch visibility and hardware performance require their own tests. This setup does not claim those production checks have already passed.

## Source and approval records

Use one current `families/<id>/source/` and `frames/` tree, with `delivery.json` as shown in Batch 001. Keep version history in Git rather than parallel final/archive/rejected folders. Approval binds the owner evidence, spec hash, source hashes and frame hashes. Hashes detect changes; they do not prove animation quality or legal ownership.

No font files, paid stock assets, signing files or credentials belong in this initial package.

## Motion review before approval

After producing all directions of one actual clip and its current draft delivery record, generate an offline review page:

```sh
python3 tools/preview_artpack.py --asset runner --clip move --out art_build/reviews/runner_move.html
python3 tools/preview_artpack.py --asset player --clip walk --out art_build/reviews/player_walk.html
```

Open the HTML in a browser. All frame images are embedded; no server, external JavaScript, game project, or online account is required. The viewer provides normal/half-speed playback, pause/step/scrub, direction selection, 1x-4x scale, light/dark/checker backgrounds, the declared ground pivot and muzzle socket when recorded.

The helper reuses the existing contract/delivery validator and does not change the inventory, dimensions, direction rules or source/approval format. A partial family may be reviewed, but the requested clip must contain every declared frame in every declared direction. Missing artwork produces a blocked result, not fabricated frames.

Additional checks reject translated copies of a still presented as a motion cycle, repeated/translated loop endpoints, and the same footage relabelled as different directions. These checks do not detect every kind of false motion or decide visual quality. Inspect foot planting, body/weapon continuity, rear views and loop joins yourself.

A review page is **not** approval or a runtime export. It never modifies the source tree or live game. Use a new output filename for each review; the helper refuses to overwrite an existing page.
