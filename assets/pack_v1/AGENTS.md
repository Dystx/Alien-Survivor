# Asset production instructions

The active owner request is a coherent full pack with better sprites and genuine animations, established before further gameplay integration. Read `SPEC.md`, `pack.json`, and `BATCH_001.md`. This art task supersedes older M0-first task ordering; it does not authorize rewriting the playable build.

- Treat the specification as a production baseline, not approval of unmade artwork. No family is approved until the owner has reviewed actual output.
- Use one current editable source and one current frame set per family. Keep history in Git. Do not add final-v2/final-final/rejected/archive folders or parallel master sheets.
- Follow exact frame dimensions, ground pivots, direction names/order and counts. Do not change anatomy, camera or lighting between frames. Do not repeat, shift, rotate or recolour a still and represent it as an articulated walk cycle.
- Independent image-generation outputs can be concept references, not complete animation clips. Produce real loops from a consistent rig or deliberately drawn frame source.
- Show native-size and half-speed animation previews, not only a contact sheet. Test player aim/strafe coverage before approving its direction budget. Do not silently change gameplay input to conceal sprite limitations.
- Every existing frame requires its declared name and hash. Player and weapon frames require muzzle sockets. Keep simulation attack timing independent from visual frame count.
- Run `python3 tools/artpack.py audit` and the asset-tool tests. An audit can pass while reporting missing artwork. Never call that pack completion.
- Runtime export requires complete, explicitly approved families. The whole-pack export requires every catalogue asset. Do not fabricate owner review fields to bypass this.
- Keep restricted source assets, purchase receipts, credentials, fonts and signing files out of this public tree. Record actual source/provenance and permissions; do not infer rights from an image being generated or freely downloadable.
- Existing prototype art remains in its current playable package until an approved replacement is integrated in a separate reviewed change. This branch must not break the working game while artwork is being produced.
