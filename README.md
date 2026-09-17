# Alien Survivor

A Steam-first alien horde-survival roguelite with a flat, gritty, pre-rendered-looking 2.5D presentation and later Android/iOS adaptation. The runtime remains 2D.

## This branch: official asset production

`assets/official-pack-v1` establishes one coherent asset contract before more visual integration. It contains the **specification, complete inventory, first-batch brief, validation tests and approved-only atlas/Godot resource exporter**. It does not yet contain newly completed animation families or a replacement playable build.

Start at **[Official Asset Pack v1](assets/pack_v1/README.md)**, then read:

1. [Specification](assets/pack_v1/SPEC.md): camera, palette, density, pivots, directions, animation and review rules.
2. [Inventory](assets/pack_v1/pack.json): exact named assets and frame requirements.
3. [Batch 001](assets/pack_v1/BATCH_001.md): base player and runner animation families.

The current inventory contains 91 asset entries / 1,134 required frame slots. Batch 001 covers 212 player/runner base slots. These are planned production counts, not completed artwork. Audit output reports what is actually present and approved.

## Verify the production tools

```sh
python3 -m pip install -r tools/requirements-artpack.txt
python3 -m unittest discover -s tests -p 'test_artpack.py' -v
python3 tools/artpack.py audit
```

A green contract/tools check is not final-art approval. The exporter refuses missing or unapproved families. Source hashes and frame hashes bind approval to exact reviewed content. There is no automatic approval command.

No command in this branch modifies the gameplay project. No previous generated sheet is silently relabelled final. No font files, restricted stock assets or credentials are bundled.

## Gameplay and previous prototypes

The playable source work is on `feat/first-playable`. Later art/finale packages were delivered separately in the project conversation; `verify/finale-logic` is a verification branch, not the complete art-equipped release. This branch does not merge or overwrite those projects, and it does not change `main`.

Existing game context remains in [game design](docs/GAME_DESIGN.md), [technical plan](docs/TECHNICAL_PLAN.md) and the root [agent instructions](AGENTS.md). The old [M0 brief](prompts/FIRST_BUILD.md) describes prior implementation work, not the current art-production task. The companion production roadmap remains a conversation artifact; it is not assumed to be committed here.

Latest explicit owner decisions take precedence. Keep one current asset source and frame set per family, with history in Git rather than parallel approved/final/archive trees. Artwork becomes eligible for runtime only after a complete family passes technical checks and actual owner review.
