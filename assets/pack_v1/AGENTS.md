# Asset production instructions

## Current owner decision: preserve the human

Read `player_visual_lock.json` before changing player artwork or firing presentation. On 2026-09-17 the owner approved the current human asset and explicitly rejected the firing attachment. The selected visual baseline is the human shown in the delivered `Alien_Survivor_Human_Review.zip`, identified by exact package, atlas, source and frame-set hashes in that record. It is NOT automatic approval of an alternative procedural model or the earlier robotic draft.

Keep that human's head, face, clothing, vest, proportions, palette, scale, ground pivot, body pixels and existing walking baseline unchanged. Do not regenerate the player to fix gun alignment. Muzzle attachment, flash pivot/size, shot timing, bullet presentation and recoil are a separate `needs_revision` task. Those changes must not slide the feet, redesign the body or alter free gameplay aim to conceal four-view artwork limitations.

This is scoped visual approval, not a complete-animation-family release approval. Existing hit/death cells are preserved to avoid regressions, not certified as final animation coverage. Keep unfinished shooting, directional death, strafe/reverse and whole-pack approval separate. The old procedural renderers are not authorized to replace the selected human; do not run them against the locked player. Further body changes require another explicit owner decision.

The authoritative record is in this pack. The selected PNG bytes currently live in the identified conversation-delivered project; do not claim a verification-only branch or a different procedural actor contains those exact pixels without comparing them.

## Existing production rules

The active owner request is a coherent full pack with better sprites and genuine animations. Read `SPEC.md`, `pack.json`, and `BATCH_001.md` after the current owner decision above. This art task supersedes older M0-first task ordering; it does not authorize rewriting the playable build.

- Treat the specification as a production baseline, not approval of unmade artwork. Scope the owner's visual approval exactly; do not fill in unrelated approval fields.
- Use one current editable source and one current frame set per family. Keep history in Git. Do not add final-v2/final-final/rejected/archive folders or parallel master sheets.
- Follow exact frame dimensions, ground pivots, direction names/order and counts. Do not change anatomy, camera or lighting between frames. Do not repeat, shift, rotate or recolour a still and represent it as an articulated walk cycle.
- Independent image-generation outputs can be concept references, not complete animation clips. Produce real loops from a consistent rig or deliberately drawn frame source.
- Show native-size and half-speed animation previews, not only a contact sheet. Test player aim/strafe coverage before approving its direction budget. Do not silently change gameplay input to conceal sprite limitations.
- Every existing frame requires its declared name and hash. Player and weapon frames require muzzle sockets. Keep simulation attack timing independent from visual frame count.
- Run `python3 tools/artpack.py audit` and the asset-tool tests. An audit can pass while reporting missing artwork. Never call that pack completion.
- Runtime export requires complete, explicitly approved families. The whole-pack export requires every catalogue asset. Do not fabricate owner review fields to bypass this.
- Keep restricted source assets, purchase receipts, credentials, fonts and signing files out of this public tree. Record actual source/provenance and permissions; do not infer rights from an image being generated or freely downloadable.
- Existing prototype art remains in its current playable package until a replacement is integrated in a separate reviewed change. This branch must not break the working game while artwork is being produced.
