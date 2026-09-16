# Instructions for implementation agents

## Read first

Read `README.md`, `docs/GAME_DESIGN.md`, `docs/TECHNICAL_PLAN.md`, and `docs/ART_AND_ASSETS.md`. Read the current production plan when it is present. Then read the specific task brief. Inspect the actual branch and existing files before editing; planning text is not evidence of implemented code.

## Product boundaries

Alien Survivor is a small, Steam-first, flat-retro 2D alien survival roguelite with Android/iOS planned later. The latest explicit owner decisions take priority over older proposals.

Do not reintroduce the superseded browser-first, real-time-3D, or campaign design. No web stack, Electron wrapper, required account, multiplayer, remote backend, or monetization SDK in the initial work.

Use original or appropriately licensed assets. Do not extract, repaint, or AI-transform Alien Shooter assets into shipped art. A reference image is not an asset licence.

## Technical baseline

Use Godot 4.7.2 stable, standard build, typed GDScript, Compatibility renderer, and matching export templates. Do not silently change the engine version. If the pinned version cannot be installed, report that blocker and separate static review from real engine validation.

Input produces movement/aim/action intent. Gameplay owns state. UI and audiovisual effects display it. Platform services remain outside combat. Offer shared control options; do not introduce different enemy counts or balance for mobile.

Begin with a readable implementation and measured profiling. No custom ECS, native extension, or MultiMesh rewrite without a demonstrated bottleneck and a correctness test. Cosmetic optimizations must not remove damaging threats or alter random gameplay outcomes.

## Scope discipline

Implement only the assigned milestone. M0 does not include all weapons, upgrades, a boss, a shop, Steam integration, or finished art. Avoid empty stubs for future systems and speculative abstraction layers.

Create a feature branch for code changes. Preserve concurrent work. Do not force-push, change repository visibility, rewrite history, purchase assets, submit store pages, enable telemetry, or publish signed releases without explicit owner authorization.

The repository is public unless a current read establishes otherwise. Do not commit restricted asset sources, SDK material, credentials, signing files, receipts, personal device IDs, or local save data. LFS does not make a file private. Do not choose a blanket open-source licence for the owner's work.

## Validation and evidence

Use real import and test commands once the project exists. A missing tool or test runner is a blocker, not a passing test. Headless results do not establish graphical, controller, touch, audio, or phone performance quality.

Keep data definitions separate from mutable run state. Validate IDs, references, ranks, prerequisite chains, pool resets, cooldowns, and save versions. Ensure pause/results/restart do not duplicate rewards or retain old run state.

Never claim a build is mobile-ready, balanced, performant, or Steam Deck Verified without appropriate evidence. State hardware, build type, engine version, scenario, and what was actually measured. Placeholders must be labelled as placeholders.

## Delivery format

Report the implemented change, relevant paths, actual checks and results, manual test steps, measured versus unmeasured claims, remaining blockers, and the next bounded task. Update the document owning any changed decision. Keep one current plan per subject; do not add parallel archives or conflicting summaries.

For M0, start with `prompts/FIRST_BUILD.md`.
