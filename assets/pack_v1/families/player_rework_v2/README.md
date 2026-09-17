# Player Rework v2 — first modeled motion draft

The owner authorized a stronger whole-character rebuild, not another rifle cutout. The original selected human remains the current game's fallback. This new candidate is not visually approved.

## What is implemented

One parametric human master with short dark hair, visible face, fabric shirt, tactical vest, cargo trousers and boots. Rifle stock/shoulder and both hand grips share one kinematic setup. The rifle is mounted at shoulder height; recoil moves the upper body while both feet remain planted. All eight views rotate actual geometry with a fixed camera and lights.

128 RGBA frames: ready 4 × 8, walk 8 × 8, fire/recoil 4 × 8. Fixed 128 × 128 cells and pivot (64,110). Every frame records muzzle, stock, shoulder, eye and hand-grip sockets. Atlas and individual frames share exact pixels.

This is newly modeled geometry, not a repaint of the old sprites or eight angle labels on the same cutout. **Facial likeness, surface finish and animation weight still need visual review.** The model is smoother and leaner than the original detailed sprite; those differences are visible rather than called final.

## Review

Open this directory's `project.godot` in Godot 4.7.2 and run. Select Ready/Walk/Fire. Pause, half speed, exact frame scrubbing, background and socket markers are available. Native-size views appear on the left; the selected direction appears at 3× on the right.

This is an isolated actor viewer, **not an updated survival game**. Existing game input, straight projectiles, damage, enemy logic and original player files are not changed or tested by this viewer.

## Source

`assets/pack_v1/source/player_rework_v2.py` is the one current shape/pose source. It uses the existing `render_motion.py` camera and mesh export library. This directory's `source/master.glb` contains editable rigid meshes/node transforms and its walk animation. Ready/fire source remains in Python; this is not a skinned production armature.

The readonly image/model checker is `assets/pack_v1/source/check_player_v2.py`. `tools/verify_player_v2.py` stages a fresh render, verifies actual PNGs, imports them into Godot, runs viewer checks, captures the actual viewport, and builds a standalone ZIP. Source scripts are included in that ZIP for offline rebuilds, but are not a second repository master.

## Boundaries and next steps

This first batch does not contain hit/death, strafing, reverse walking or independent moving recoil. It does not change the full v1 release inventory or bypass its approval gates. Once posture, likeness and finish are acceptable, expand this same master rather than swap unrelated images.

The original baseline hashes in `player_visual_lock.json` remain the fallback identity record. Its newer authorization permits this candidate to differ; original pixels are not overwritten. No new owner-art approval, main-branch merge, exported executable or store submission is implied.
