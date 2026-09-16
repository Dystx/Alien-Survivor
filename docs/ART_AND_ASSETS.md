# Art and asset plan

Prepared 2026-09-16. Status: production brief. No final art has been commissioned, generated, purchased, imported, or approved as part of this planning pass.

## 1. The visual contract

**Flat, detailed, gritty retro sprites with a fixed elevated viewpoint.** Not low-poly characters displayed in real-time 3D. Not clean vector art, oversized cartoon heads, modern glossy materials, or a neon-heavy survivors clone.

The frame should read like an old PC action game: textured industrial floor, small directional soldier, dense alien silhouettes, restrained contact shadows, blunt weapon flashes, and the aftermath of a fight accumulating on the ground. Modern quality comes from consistent animation, responsive feedback, readable UI, and careful composition.

Retro does not require extremely coarse pixel art. Preserve enough detail for creatures to feel organic and threatening, but judge every asset at its actual on-screen size rather than only in a large preview.

### Proposed visual rules

- Fixed elevated view with one approved camera angle for all actors and props.
- Muted concrete/metal environment; distinguishable creature values and accents; bright but bounded weapon effects.
- Player silhouette remains visible among runners and corpses.
- Contact shadows are painted/baked or inexpensive flat sprites.
- Floors have texture without competing with small projectiles or XP pickups.
- Blood is decorative; it cannot obscure hazard shapes or become a gameplay collision object.
- A muzzle flash may illuminate the impression of a shot without requiring a scene-wide dynamic light.
- No compulsory CRT distortion, scanlines, heavy bloom, chromatic aberration, or full-screen damage flash.
- Gore, shake, and flash intensity are adjustable independently.

## 2. Two valid production pipelines

### A. Directly painted/drawn sprites

An artist creates directional poses, animation frames, tiles, and effects directly in 2D. This offers precise control over the final flat image and can reproduce the intended dense retro rendering without 3D source work. The cost is maintaining consistent volume, lighting, and anatomy across directions and motion.

Choose this when a suitable sprite artist can demonstrate an affordable animated sample at the target size. Do not select an artist based on one attractive full-resolution illustration alone.

### B. Original or licensed 3D sources rendered into sprites — recommended initial test

Build or legitimately acquire a model, establish original creature design/materials, animate it, render from the approved camera and directions, then reduce and paint over the frames. Godot receives only the sprite atlases and metadata.

This is an authoring method, not a change to runtime 2D. Avoid the smooth, glossy appearance of unprocessed renders. Downsample deliberately, unify contrast and edges, clean silhouettes, and paint details that disappear at the actual game scale.

It is not guaranteed to be cheaper. Modeling, rigging, rendering, and cleanup all count. Commission one matched sample with each feasible method before buying the complete roster. Choose based on delivered animation quality, editable sources, repeatability, and actual quote—not on the word AI or 3D.

### AI assistance

Use generated concepts, colour exploration, or draft signage only when useful and permitted by the selected tools' terms. Do not assume independent generated frames form a coherent walk cycle or that a single concept image is a production sprite sheet. Generated material still requires originality/rights review and technical cleanup. Keep records of any shipped AI-generated material for store disclosures.

Do not upload extracted Alien Shooter artwork to an AI pipeline and treat the result as cleared production art. The project uses independent or properly licensed source assets.

## 3. Art approval sample: before the full catalogue

Build a small proof scene containing one floor patch, one original player, one original runner, a rifle shot, a death animation, a corpse, a blood mark, a pickup, and one simple prop.

The actor sample should demonstrate at least four movement directions initially, with the production target tested at eight. Compare two texture/filter settings and two plausible sprite sizes. View the scene on desktop and a physical phone with 50–100 repeated creatures, not only as an isolated animation viewer.

Approval questions: Does it look flat and retro? Can a player identify the live threats? Does the same body retain its shape across directions? Do the feet stay planted? Does the rifle muzzle line up? Does the art survive mobile size and bright ambient lighting? Is atlas memory within budget?

No full creature order until this sample passes.

## 4. Directional sprite specification

Starting convention: eight directions at 45-degree steps, all rendered/painted with the same elevation and lighting. Define atlas order once and validate it in an automated facing preview. Use bottom-center/ground-contact pivots, not changing image centers.

Initial visual-size candidates: small runner around 32–48 pixels high, player around 48–64, brute around 64–96 at the world reference resolution. These are art-test ranges, not a locked resolution contract.

Regular enemies need a movement cycle, relevant attack wind-up/action, hit indication, death cycle, and a corpse result. Idle may be a held pose or short cycle. Spitters and chargers require separate readable wind-ups, not just a faster walk animation.

For the player, independent movement and aim directions must be handled deliberately. Compare a layered lower-body/upper-body sprite rig against a smaller set of full-body aiming/strafe cycles. Layered sprites save some repetition but need rear/front weapon ordering and stable joints. The first art test selects the approach; do not let the implementation aim independently while the artwork always points forward.

Avoid mirroring asymmetrical guns, damage marks, or baked lighting without checking the result. A mirrored animation is not automatically equivalent to an authored opposite direction.

Suggested file convention: `<asset_id>_<action>_<direction>_<frame>.png` for source frames; runtime atlas names use asset ID and action group. Sidecar metadata records size, pivot, frame rectangle, duration, direction order, muzzle points, source revision, and rights record ID. Metadata contains no machine-specific absolute paths.

## 5. Content production list

| Category | First art sample | First-release ceiling |
|---|---|---|
| Player | One survivor and rifle pose set | Same appearance, three starting loadouts, weapon-facing support |
| Regular aliens | Runner | Runner, spitter, charger, armoured brute |
| Elites | One readable modifier test | Two reusable modifier treatments, not two new species |
| Boss | None | One brood organism with three attack patterns |
| Primary weapons | Rifle | Rifle, scattergun, flamethrower, arc emitter |
| Support objects | None | Seeker projectile, mine, defence drone |
| Environment | Floor, blocker, crate | One industrial tile set, three layouts |
| Interactive prop | None | One terminal with four states |
| Effects | Flash, hit, death, blood, pickup | Weapon effects, warnings, statuses, boss effects, selection feedback |
| UI | Health and simple result screen | Shared frame/theme, icons, upgrade cards, menus, credits |
| Audio | Shot, impact, hurt, death | Distinct weapons, threats, UI, ambience, music layers |

An initial environment list can be approximately 12 floor variants, 6 edge/wall pieces, 8–12 props, 3 infestation overlays, and the terminal states. Treat these as a starting bill of materials; reduce duplicates after building the first layout.

Weapon upgrades should primarily change effects, timing, and behavior. Avoid multiplying directional player animation sets for every numerical rank.

## 6. Asset sourcing

### Prototype

Use original simple placeholders or clearly reusable development assets. [Kenney's asset-page downloads are CC0](https://kenney.nl/support) and can supply placeholders, UI elements, and some effects. Their style is not automatically the final style for this project.

[Quaternius permits commercial use and modification of its CC0 models](https://quaternius.com/faq.html). Selected models/props can be raw material for a sprite-rendering test. Do not assume its existing monsters are the right finished aesthetic. Preserve the relevant licence supplied with each pack.

### Final production

Prioritize a consistent original creature family, player animation, weapon impact sounds, and one coherent environment set. A small commission with an approved sample is preferable to a dozen unrelated creature packs.

For purchased content, require confirmation of modification rights, distribution inside Windows/Android/iOS games, compatible source formats, included animation clips, and restrictions on publishing source files. Buying a asset does not mean receiving its rig or editable source. Check the individual listing before committing money.

[Sonniss GameAudioGDC](https://sonniss.com/gameaudiogdc/) is a candidate production sound source; use the applicable archive licence and retain it. Curate/edit sounds rather than importing a large archive into the game. No audio pack has been acquired by this plan.

### Public repository restriction

`Dystx/Alien-Survivor` was public on inspection. Put only original files cleared for publication or assets whose terms permit source redistribution into it. Keep restricted purchased art, raw sound libraries, contracts, and receipts in an access-controlled asset store. The public repo can keep references, import instructions, and compatible placeholders.

A private build step can stage properly licensed runtime assets. `.gitignore` and LFS are not access control; LFS in a public repository does not make a restricted asset private. If the owner later chooses a private production repository, that is a separate repository-setting decision.

Do not impose a blanket licence on the game's code/art. Record each third-party licence and decide the project's own licence separately.

## 7. Asset register and acceptance

Create a machine-readable asset register when the first external asset is used. Each entry records asset ID, creator, source page, applicable licence/version, acquisition date, proof location, modification permissions, runtime distribution permissions, public-source redistribution permission, attribution text, source checksum/revision, output paths, and review status.

Do not include private receipts or contract text in the public register. Reference their private record IDs. Required attribution belongs in credits and included licence files.

Technical acceptance checks: alpha edges, atlas padding, pivot consistency, world scale, direction order, looping, frame duration, muzzle alignment, texture import settings, audio peaks, and missing dependencies. Rights acceptance and visual acceptance are separate checks.

## 8. Runtime memory and export

Compressed file size is not texture memory. For example, a 2048 x 2048 uncompressed RGBA8 atlas uses `2048 * 2048 * 4 = 16,777,216` bytes, or 16 MiB, before mipmaps and engine overhead. A 4096 x 4096 atlas uses 64 MiB on the same basis. Platform texture compression can change this and must be measured in the actual export.

Keep atlases grouped by use rather than placing every creature, weapon, and UI element in one permanently loaded sheet. Avoid vast transparent margins. Use padding/extrusion appropriate to filtering so neighboring frames do not bleed. Prefer bounded atlas pages, initially no larger than 2048 square unless measurements justify larger pages on all target devices.

Eight directions multiply the frame count. For illustration, eight directions with twenty total frames per direction at 64 x 64 RGBA8 is 2.5 MiB of raw pixel data before packing overhead and mipmaps. Doubling each dimension makes it 10 MiB. Direction count, animation length, and frame size are production/performance decisions together.

Load only the selected arena and applicable runtime assets. Stream longer music where supported and tested; keep small repeated effects ready without retaining unused uncompressed libraries. Measure import results in release builds.

## 9. Audio direction

Prioritize readable weapon signatures and threat warnings. Layer a rifle's sharp onset, body, and restrained mechanical sound rather than merely increasing volume. Limit repeated voices so a horde does not become uncontrolled noise or hundreds of simultaneous sounds.

Separate master, weapons/effects, music, and UI buses. Threat cues should survive dense gunfire. Avoid one distinct looping sound per alien. Use bounded spatial emitters for representative nearby threats and controlled variation for impacts/deaths.

Begin with one menu/ambient bed, one combat loop or layered track, and one finale layer. More tracks are optional after the first complete run works.

## 10. Production order

Sample scene -> approve sprite method and camera -> player + runner -> spitter + effects -> first finished arena -> other two species -> modules and remaining weapons -> boss -> UI/store art -> remaining layouts and polish.

Do not create final Steam capsule art around an uncleared name or an unapproved creature design. Do not make a trailer that implies an art quality or enemy count the real build cannot deliver.
