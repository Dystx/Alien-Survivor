# Alien Survivor

A Steam-first, flat-retro alien horde survival roguelite, designed for a later Android/iOS release from the same Godot project.

**Status: pre-production. This repository currently contains planning documents, not a playable game.** No gameplay, exports, benchmarks, final artwork, or store integrations have been implemented or verified.

## Direction

Capture the readable, gritty, sprite-based feeling of classic isometric alien shooters, with the short runs, escalating hordes, and build combinations of a survivors-style roguelite. Create an independent game using original or appropriately licensed assets.

The game is genuinely 2D at runtime. Optional 3D modeling is an asset-production tool for rendering flat sprites, not a change to the visual direction.

## Read in this order

1. [Game design](docs/GAME_DESIGN.md): experience, controls, runs, weapons, enemies, progression, scope, and competing games.
2. [Technical plan](docs/TECHNICAL_PLAN.md): engine, architecture, rendering, performance, saves, mobile, testing, and proposed project layout.
3. [Art and asset plan](docs/ART_AND_ASSETS.md): the flat-retro art contract, production alternatives, asset list, licensing, and memory budgets.
4. [Production plan](docs/PRODUCTION_PLAN.md): milestones, acceptance gates, delivery backlog, costs, release preparation, and open decisions.
5. [Agent instructions](AGENTS.md): boundaries and implementation workflow.
6. [First implementation brief](prompts/FIRST_BUILD.md): the next bounded coding task.

## User-established constraints

- Alien-shooter horde combat with survivors-style replayability, rather than an authored campaign.
- Flat, retro sprite presentation, not a modern real-time 3D look.
- Steam first; mobile later, with mobile-friendly foundations from the beginning.
- Small content catalogue. Systems and combinations must earn replayability.
- Repository: `Dystx/Alien-Survivor`.

## Recommended implementation baseline

- Godot 4.7.2 stable, standard build, with matching export templates.
- Typed GDScript and Godot's Compatibility renderer.
- One shared gameplay implementation, platform-specific input and service adapters.
- Windows first, Steam Deck testing, Android tests during the prototype, early iOS feasibility check when Mac/device access is available.
- Landscape presentation; automatic fire with optional manual aim, available across platforms.
- Local/offline play. No account, server, advertising SDK, multiplayer, or cloud backend required to start.

These are implementation recommendations, not a claim that every new design detail has been individually approved by the project owner. Numbers, costs, and performance budgets in the documents are planning targets, not measurements or commitments.

## First-release content ceiling

One player appearance with three loadouts; four primary guns; three support modules; twelve passive upgrade families; four weapon breakthroughs; four regular alien families; two elite modifiers; one boss; one industrial biome with three tested layouts.

One primary gun plus up to two support modules can be equipped in a run. Do not silently turn this into a six-weapon-per-character game or a campaign.

## Current next step

Implement **M0: bootable combat prototype** from `prompts/FIRST_BUILD.md`. Start with one player, one gun, one enemy, one small arena, restart, instrumentation, and a basic touch-input path. All visuals may be explicitly marked original placeholders.

## Repository handling

This repository was public when inspected on 2026-09-16. Do not commit marketplace source assets, signing keys, passwords, purchase receipts, personal device identifiers, or restricted SDK files. A licence to distribute an asset inside a game is not necessarily permission to publish its source files in a public repository.

No open-source licence for the project's own code or art has been selected. Preserve third-party licence notices separately; do not automatically apply an MIT licence to the entire project.

## Plan authority

The latest explicit owner decisions take precedence. Keep one current version of each planning document, and update the owning document when a decision changes. Do not create parallel master plans or reintroduce the superseded browser/3D/campaign plan. Git history supplies version history.

Prepared: 2026-09-16.
