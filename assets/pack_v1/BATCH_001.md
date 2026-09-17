# Batch 001 — Player and runner

**Status: specified; artwork production and owner approval are pending.** No generated still from earlier messages is promoted to approved animation by this brief.

## Objective

Prove one coherent visual system through two complete base animation families, using the camera, lighting, palette, scale and file contracts in `SPEC.md` and `pack.json`. Do not build another promotional atlas or modify gameplay in this task.

## Exact first delivery

Every action is delivered in screen-facing `e, s, w, n` order. Individual RGBA PNG frames retain the same family cell and ground pivot.

| Family | Actions per direction | Total base frame slots |
|---|---|---:|
| Player | idle 4; walk 8; shoot 4; hit 2; death 6; walk_fire 8 | 128 |
| Runner | idle 4; move 6; attack 4; hit 2; death 5 | 84 |
| **Batch total** | Two families, four directions | **212** |

The player's additional backward-walk and left/right-strafe cycles add another 96 frames to its complete final family. They are required before player runtime export, but should be authored only after the base locomotion/aiming treatment passes review. The full player family therefore contains 224 frames, not 128. Batch completion is not full-pack completion.

## Work sequence

1. Establish the two editable masters, not independent per-frame image generations. Player: graphite armour, amber visor, compact rifle, practical proportions. Runner: rust-red four-limbed body, low silhouette, long foreclaws, ivory dorsal ridge. Keep models/layers and their camera/lighting settings available as editable sources.
2. Produce the player's eight-frame east-facing walk and the runner's six-frame east-facing move. Deliver actual normal-speed and half-speed loop previews. A static contact sheet is supplemental, not sufficient. Check foot planting, limb motion and silhouette stability before extending directions.
3. Produce all four genuine views from those masters, then the remaining base actions. No mirrored shortcuts masquerading as unique views. Do not rescale individual frames. Do not duplicate a still, move it up/down, and call that walking.
4. Inspect shoot and walk-fire at gameplay scale. Record the muzzle position for each player/weapon frame in delivery metadata. It must stay attached to the gun, not a guessed fixed offset shared by all facings. Compare aim and movement quadrants; leave player approval pending if four directions cannot represent free aiming adequately. Do not alter gameplay aiming to fit the art.
5. Prepare `delivery.json`, including actual file hashes, editable source/provenance records, technical review and status `review`. Run the checks and record remaining visual issues in the delivery review, not in parallel archive documents.
6. Present the real loops, four-direction previews and shared player/runner scale comparison to the owner. Only explicit owner approval may populate `owner_approval`. Never mark the family approved in anticipation of a reply.

## File contract

```text
families/player/source/...
families/player/frames/walk/e/000.png
families/player/frames/walk/e/001.png
...
families/player/delivery.json
families/runner/source/...
families/runner/frames/move/e/000.png
...
families/runner/delivery.json
```

Frame numbers are zero-based and three-digit. Raw frames must not be cropped independently. The source is one current editable master per family with any required texture dependencies. Do not publish restricted marketplace files in this public repository.

A delivery record uses these fields:

```json
{
  "asset_id": "runner",
  "status": "review",
  "spec_sha256": "ACTUAL_SHA256_OF_pack.json",
  "sources": [
    {
      "path": "families/runner/source/runner.blend",
      "sha256": "ACTUAL_SOURCE_SHA256",
      "provenance": "ACTUAL_CREATOR_AND_SOURCE_RIGHTS_RECORD"
    }
  ],
  "frame_sha256": {
    "families/runner/frames/move/e/000.png": "ACTUAL_FRAME_SHA256"
  },
  "sockets": {},
  "review": {
    "style": false,
    "motion": false,
    "alpha_edges": false,
    "pivot_and_scale": false,
    "direction_coverage": false,
    "source_rights": false
  },
  "public_source_permission": false,
  "owner_approval": null
}
```

The example is documentation, not a valid delivery. List every actual frame and source dependency; replace placeholder hash strings with computed hashes. For the player and weapons, `sockets` maps each frame path to an object containing its `muzzle: [x, y]`. Player approval additionally requires `review.aim_and_strafe`.

## Acceptance

Check readable silhouettes at native size, stable armour/anatomy/weapon design between frames, no chopped weapons or limbs, genuine rear views, clean alpha over dark/light/checker backgrounds, fixed ground pivots, smoothly repeating locomotion, and deaths that do not look like darkened standing creatures. Inspect death-to-corpse continuity without demanding a second unrelated corpse image.

The technical checker detects structural failures and unchanged duplicate pixels. It cannot judge acting, anatomy or tasteful shading; passing it is not final art approval.

## Subsequent batches

After this style/locomotion proof: complete player aim coverage and the spitter/charger/brute families; produce the environment/effects/UI under the same contract; then build the Brood Warden and its attack cycles. The full inventory is already in `pack.json`. Do not add assets merely to fill a sheet.
