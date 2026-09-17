# Art and assets

The current production authority is **[Official Asset Pack v1](../assets/pack_v1/README.md)**.

Read its [specification](../assets/pack_v1/SPEC.md), [complete inventory](../assets/pack_v1/pack.json), and [first production batch](../assets/pack_v1/BATCH_001.md). This replaces this document's older open-ended sprite-production proposal. Keep visual rules and frame counts there, not in parallel art bibles.

## Current direction

Flat, gritty, pre-rendered-looking 2.5D sprites. One camera, scale, lighting system and palette across the pack. Better articulated animation rather than unrelated generated stills. Steam-first gameplay remains 2D, with mobile adaptation later.

The owner requested that a coherent pack be established before further art integration. Existing gameplay prototypes and generated sheets are not automatically final assets. Preserve the working prototype until a specific complete replacement family is reviewed and approved.

## Current implementation status

The asset specification, inventory, first-batch brief, validator, tests and atlas/Godot-resource exporter exist on `assets/official-pack-v1`. New complete animation families have not yet been produced or approved as part of that setup.

The inventory names 91 asset entries and 1,134 planned frame slots. Batch 001 defines 212 base player/runner slots. These are production requirements, not completed artwork counts. Run the audit for actual delivery status.

Only owner-approved complete families can be exported through the production tool. Technical validation is separate from artistic review, source-rights confirmation, Godot import, gameplay testing and mobile performance.
