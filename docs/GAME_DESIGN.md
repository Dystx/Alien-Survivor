# Game design

Prepared 2026-09-16. Status: recommended design for implementation and playtesting. The owner's established constraints are listed in the root README. Specific mechanics and values below remain revisable when evidence or a new owner decision warrants it.

## 1. The game in one sentence

**Cut paths through an alien infestation, assemble a destructive weapon build, and deliberately trigger dangerous facility overloads for better upgrades.**

Alien Survivor is a single-player survival action roguelite. Its presentation is flat, gritty, retro, and sprite-based. Its modern qualities are responsiveness, clarity, build choices, accessibility, reliable saving, and stable performance—not real-time 3D spectacle.

The player fantasy is turning a vulnerable facility survivor into a walking containment failure. Enemies should die with readable impact and satisfying sound. The late run should feel dramatically stronger than the opening without making every build look or play identically.

Do not build an Alien Shooter remake, an eight-mission campaign, an open world, or a web application.

## 2. Reference games and positioning

These are references and adjacent products, not evidence of an unoccupied market:

| Reference | Relevant documented territory | Our proposed interpretation |
|---|---|---|
| Alien Shooter | Isometric alien combat and facility-clearing reference | Flat industrial presentation, enemy readability, impact, corpse-covered floors |
| Vampire Survivors | Time survival with minimal input and roguelite progression | Short runs, frequent choices, combinations that change a run |
| Crimsonland | Top-down alien/monster shooting, weapons, perks, survival modes | The closest warning that alien hordes plus upgrades are not novel by themselves |
| 20 Minutes Till Dawn | Survival roguelite with weapon/build choices | Gun identity should survive the transition into a survivors-style game |

Sources checked 2026-09-16: [Sigma Team](https://www.sigma-team.com/alien-shooter/), [poncle's game page](https://poncle.itch.io/vampire-survivors), [Crimsonland on Steam](https://store.steampowered.com/app/262830/Crimsonland/), [20 Minutes Till Dawn on Steam](https://store.steampowered.com/app/1966900/20_Minutes_Till_Dawn/).

The proposed distinction is the combination of detailed old-PC sprite presentation, controllable gunfire, and optional overload encounters. None of these is claimed to be unprecedented. Validate the combination with players rather than advertising novelty as fact.

`Alien Survivor` is a working project name. A similar Steam title, [Venox: The Alien Survivors](https://store.steampowered.com/app/2361260/Venox_The_Alien_Survivors/), already has a listing. This is a naming/discoverability flag, not a legal clearance result. Check the final name separately before paid branding or a store announcement.

## 3. Core loop

Choose loadout -> enter arena -> kill aliens -> collect XP -> choose upgrades -> decide whether to activate an overload terminal -> survive escalating encounters -> defeat the final boss or die -> receive unlock progress -> replay with a different build.

### Standard run

- Survival phase: 15 minutes of simulation time. Upgrade selection and pause menus do not advance it.
- At 15:00, enter the finale. Spawn the boss with a clear warning and switch to a controlled reinforcement schedule instead of endlessly escalating regular spawns.
- Win when the finale boss is defeated while the player is alive. Existing ordinary enemies do not block victory.
- Target total duration: approximately 15–18 minutes, depending on the boss fight. This is a tuning target, not a fixed timeout.
- Death ends the run. Bank only the results/unlock progress defined for failure.
- No endless mode or second run length in the first release.
- The demo uses a shortened 10-minute survival phase followed by a reduced finale.

### Escalation draft

| Run segment | Intended pressure |
|---|---|
| 0–2 minutes | Establish movement, targeting, damage feedback, first upgrades |
| 2–5 minutes | Introduce ranged threats and the first optional overload |
| 5–9 minutes | Mix enemy roles; first elite; support modules begin to matter |
| 9–12 minutes | Pressure from more than one direction; recognisable build identity |
| 12–15 minutes | Strong combinations, final elite, sustained but readable pressure |
| Finale | Boss mechanics plus limited reinforcements; no further uncontrolled escalation |

Tune this after observing real runs. Do not compensate for a boring fight solely by inflating health.

## 4. Controls: one ruleset, several ways to play

Recommended baseline: **automatic fire, automatic target selection, and optional manual aiming**. All these modes must be available on PC, controller, and mobile. Defaults may differ after usability tests, but damage, cooldowns, enemy count, and upgrade rules must not.

| Action | Keyboard/mouse | Controller | Touch |
|---|---|---|---|
| Move | WASD, rebindable | Left stick | Adjustable left virtual stick |
| Automatic targeting | Default when not overridden | Default when right stick is idle | Default when no aim gesture is active |
| Aim override | Hold primary mouse button toward pointer | Deflect right stick | Right-side drag/stick |
| Fire | Automatic cooldown-driven firing | Same | Same |
| Dash, when introduced | Rebindable button | Face/shoulder button | Optional-position large button |
| Pause | Escape | Menu button | Pause button/back handling |
| Choose upgrade | Pointer or focus navigation | Focus navigation | Large touch cards |

Manual aiming overrides direction, not fire rate. Never make repeated clicking bypass cooldowns. Pause/upgrade screens consume input so selecting a card cannot also fire or dash.

An optional manual-trigger mode can be added after the core loop is stable. It is not required for the first prototype. There is no ammunition scavenging or mandatory reload button: weapons manage their own cadence, magazines, or heat. Dash is a short repositioning tool; it is deferred until basic movement is enjoyable and must not become required to compensate for unfair spawns.

Alternative considered: mandatory twin-stick shooting. Retain only as an optional control mode unless testing demonstrates a compelling reason to change the baseline. A mobile-only auto-aim ruleset is rejected.

## 5. Weapon and build structure

Carry **one primary weapon plus up to two support modules**. Choose the primary before entering; do not add an inventory, mid-run weapon swapping, or loot rarity tiers in this version.

### Four primary weapons

| ID | Identity | Distinctive late-run direction |
|---|---|---|
| `rifle` | Accurate sustained ballistic fire | Pierce and ricochet corridors |
| `scattergun` | Short-range cone and stagger | Dense fragment bursts and space-making |
| `flamethrower` | Cone damage over time | Burning patches and controlled on-death spread |
| `arc_emitter` | Conductive single-target strike with limited chains | Reliable crowd chains, weak isolated-target efficiency |

The prototype starts only with `rifle`. Do not implement the other three in the first coding task.

### Three support modules

| ID | Role | Limitation |
|---|---|---|
| `seeker_rockets` | Periodic priority-target burst | Long cooldown and bounded splash radius |
| `proximity_mines` | Reward movement and path planning | Bounded active mine count and arming delay |
| `defence_drone` | Supplemental automatic fire | Fixed firing budget; one drone per module slot |

These modules do not require three extra visible guns on the player's directional sprite. Their own small sprites/effects carry the presentation.

### Level-up offers

Offer three distinct valid choices. Choices come from upgrading equipped weapons, gaining a support module into a free slot, or adding/ranking a passive. Pause simulation while choosing. Show the numerical change and relevant interaction in plain language.

Do not offer full-slot equipment, already-capped ranks, inaccessible prerequisites, or duplicate choices. When the available pool becomes small, use documented fallback upgrades rather than generating invalid cards. Introduce limited rerolls only after the ordinary offer system works.

Twelve passive families are the content ceiling for the first release: damage, firing speed, critical chance, critical effect, projectile travel, impact/pierce, area size, effect duration, status potency, movement, durability, and collection radius. Each family may have up to three meaningful ranks. These are twelve design families, not thirty-six distinct mechanics.

Give each primary one authored breakthrough, earned through a clear upgrade condition and a special reward. Four breakthroughs total. Exact formulas, caps, eligibility, and side effects belong in data and tests; the descriptions here are design intent.

### Three build tests

1. Rifle + ricochet/pierce + rockets: create firing lanes, keep a safe distance, burst elites.
2. Flamethrower + duration/status + mines: pull enemies across persistent zones without permanent screen-covering fire.
3. Arc emitter + chain-focused breakthrough + drone: exploit groups while retaining a weakness against isolated brutes.

These examples are acceptance scenarios: they must produce observably different decisions, not just different projectile colours.

## 6. Signature event: overload terminals

One reusable terminal prop appears at up to three authored sockets. At scheduled windows, an unused terminal becomes available. The player may ignore it or deliberately activate it with a short, clearly telegraphed proximity interaction.

Activation triggers a roughly 30-second local swarm surge. Survive it to obtain one special upgrade selection. Leaving the immediate area is allowed; this is not a mission objective or a mandatory stationary defence sequence. Activation cannot happen accidentally when simply collecting XP nearby.

Each socket can be used once. No extra permanent currency is introduced. The terminal has inactive, available, running, and spent states. Use one clear risk/reward explanation.

This mechanic is a hypothesis. If tests show that it adds confusion or encourages dull waiting, simplify or cut it rather than building more content around it.

## 7. Enemy roster

| Family | Gameplay problem | Visual contract |
|---|---|---|
| Runner | Baseline swarm pressure | Small, low, sharply readable body |
| Spitter | Forces route changes through slow projectiles | Recognisable sac/head shape and wind-up |
| Charger | Punishes standing in a straight line | Long silhouette and explicit charge direction |
| Armoured brute | Occupies space and absorbs frontal pressure | Broad, heavy shape; obvious movement rhythm |

Two elite modifiers reuse those families: a faster/aggressive mutation and an armoured/area-denial mutation. They need more than colour alone: silhouette attachment, icon, scale within limits, and attack warning. They are not counted as two additional species.

One finale boss: an original brood organism with three readable attack patterns and a limited reinforcement ability. Its first version should use the same damage and status systems as ordinary enemies, with explicit exceptions rather than unrelated boss-only combat code.

No off-screen instant attacks. Spawns must respect navigable space, a player safety distance, and warning rules. Avoid trapping the player against solid geometry with unavoidable damage. Off-screen enemies must still obey world obstacles and gameplay rules.

## 8. Arena and replayability

One industrial research-facility biome; three authored layouts built from the same tile/prop set. Start with an open processing hall: a broad outer movement route, a few interior blockers, and clear connections between zones. No overlapping floors, narrow mandatory corridors, or tall walls hiding enemies.

Use seeded schedules, weighted enemy composition, elite timing, overload rewards, and upgrade offers for variation. Author safe layouts first. Do not make a procedural map generator before three hand-tested layouts demonstrate useful variation.

Random seeds support repeatable diagnostics, not a promise of identical floating-point simulation on different platforms. No competitive leaderboard is planned.

## 9. Progression and economy

Two concepts only: XP for in-run choices, and between-run research progress for unlocks. Avoid a shop full of currencies.

Unlock weapons, starting loadouts, and optional challenge tiers. The initial three loadouts reuse one player appearance and alter starting equipment or a small, understandable trait. They are not three separately animated characters.

Prefer horizontal options over mandatory permanent damage/health grinding. The first clear must be achievable without purchasing permanent stat power. A loss should still provide useful progression but not create an incentive to repeatedly die immediately.

Run state resets after a completed or failed run; unlock state persists. Resume support restores a suspended run, not an in-game purchase or extra life. No ads, consumable revives, loot boxes, or paid power in the proposed Steam version.

## 10. Presentation, UI, and accessibility

Screens: title, loadout, gameplay HUD, paused run, three-choice upgrade screen, result summary, unlock screen, settings, and credits/licences. No account page.

HUD: health, XP/level, run phase/time, primary/module indicators, and nearby event direction when relevant. Keep large damage-number clouds off by default. Menus use live text and scale independently from low-resolution world art.

Provide remapping, controller focus, adjustable touch zones, text scale, readable contrast, separate audio levels, reduced flashing, optional shake, a gore slider, and colour-independent threat distinctions. Do not require hover to understand an upgrade. Layout text for localization from the beginning; initial content authoring is English, with other languages added through reviewed translation rather than embedded sprite text.

## 11. First-release ceiling and exclusions

Ceiling: 1 player appearance / 3 loadouts / 4 primaries / 3 modules / 12 passive families / 4 breakthroughs / 4 regular alien families / 2 elite modifiers / 1 boss / 1 biome / 3 layouts / 1 standard run format.

Excluded: campaign, multiplayer, online ranking, accounts, crafting, procedural world generation, free camera, runtime 3D, user-generated content, service backend, mobile advertising, paid power, and additional modes before the standard run is proven.

This is a ceiling, not an obligation to ship content that fails quality gates. A smaller excellent launch is preferable to completing a checklist of weak additions.
