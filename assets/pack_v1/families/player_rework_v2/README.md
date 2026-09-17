# Player Rework v2 — source review

Status: **review source / not integrated / not owner-approved**.

This branch keeps the existing selected human intact while developing a stronger combat-ready replacement candidate. The current source is `assets/pack_v1/source/player_rework_v2.py`.

## Current source scope

- Same product role and visual language as the selected survivor: exposed human head, cropped dark hair, fabric shirt/vest, olive trousers, boots and a compact rifle.
- Eight authored camera views: `e, se, s, sw, w, nw, n, ne`.
- Initial clips: `ready` (4), `walk` (8) and `fire` (4) per direction.
- Rifle butt is placed at the upper-shoulder pocket and the trigger/support hands are solved against the same rifle rig.
- Muzzle, stock, trigger grip, support grip, shoulder and eye are explicit sockets.
- The current model intentionally does **not** claim finished hit, death, strafe or reverse coverage.

## Important boundaries

The selected HumanReview player remains the gameplay fallback and its locked pixels are not modified by this source. This source file is a new parametric character model, not a repaint or transformed copy of the selected PNG frames. Rendering it successfully does not approve the result or replace the player in the runnable game.

Before integration, review the actual rendered PNGs at native and enlarged size for face identity, shoulder/hand anatomy, rifle height, diagonal perspective, walking weight and muzzle alignment. Then connect it to the existing straight-shot tests without changing damage, targeting, collision or aim freedom.

## Next bounded step

Render the complete current source into a fresh candidate directory, record exact source/frame hashes, build a review atlas, and run the player-specific visual/trajectory checks. Do not add more actions until the ready/walk/fire foundation is accepted.
