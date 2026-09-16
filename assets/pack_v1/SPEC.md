# Alien Survivor — Official Asset Pack v1

Specification baseline 0.2.0 · 2026-09-16

**Specification established; final artwork is not approved or complete.** This document and `pack.json` define the one current pack. The game build and earlier generated sheets remain prototypes. A working image import is not evidence of good animation.

## 1. Appearance

Gritty, detailed, pre-rendered-looking 2.5D. The runtime stays 2D. No chunky pixel-art restyle, clean cartoon outlines, glossy modern 3D presentation, giant emissive outlines, or promotional text baked into sprites.

Muted concrete and graphite metal; olive cloth and exposed human skin; rust-red organic enemies; ivory structural ridges; acid green reserved for acid; blue-white reserved for electrical effects. The palette in `pack.json` contains material anchors, not a requirement to quantize all shading to sixteen colours.

Keep one camera, physical scale and light rig across the whole pack. Key light appears upper-left. Rotate the actor, not the lighting. Ground shadows are separate cosmetic elements. No painted floor behind actors, baked muzzle flash in a body frame, or neighboring object accidentally included in a crop.

## 2. Camera and scale

Use an orthographic **dimetric** camera: 30 degrees elevation and 45 degrees azimuth. The ground reference is a flush 96 x 48 pixel diamond. In authoring world units, project `(u, v)` to `(48u - 48v, 24u + 24v)`; vertical world height projects to approximately `-58.787754z` screen pixels. The derivation fixes density across differently sized frame canvases; do not zoom each actor independently to fill its box.

A floor tile contains only its flush top surface. Walls, slab lips and raised edges are separate objects. The validator rejects opaque floor pixels outside the diamond and largely empty floor surfaces. Adjacency still needs a visual seam test.

| Family | Cell | Ground pivot |
|---|---|---|
| Player | 160 x 160 | 80, 112 |
| Runner | 128 x 128 | 64, 80 |
| Spitter | 160 x 160 | 80, 108 |
| Charger | 160 x 160 | 80, 104 |
| Brute | 192 x 192 | 96, 136 |
| Brood Warden | 288 x 288 | 144, 204 |

These are canvas dimensions, not a command to stretch anatomy. Leave two transparent pixels at every actor/effect frame edge. Each family keeps its declared pivot for every action; use in-place locomotion with real limb movement, not whole-image sliding or bouncing. Floor and nine-slice UI pieces have their own edge rules.

## 3. Directions and animation

The production base is four **screen-facing** directions in this exact order: `e, s, w, n`. Screen X points right and screen Y points down. These labels are not the arena's world axes. Each direction needs genuinely authored views. Never substitute a front view for a rear view, rotate a whole actor bitmap to face another direction, or repeat/mirror frames and call it full coverage.

Player base clips: idle 4, walk 8, shoot 4, hit 2, death 6, and walk-fire 8 frames per direction. The complete player family also requires backward walk and left/right strafes, eight frames each per direction. Runner: idle 4, move 6, attack 4, hit 2, death 5 per direction. The exact spitter, charger, brute and boss action lists and frame counts live in `pack.json`.

**Four facings are a production starting point, not proof that free aiming looks acceptable.** Review movement against every aim quadrant, muzzle alignment, reverse motion, and strafes. Never quantize gameplay aiming merely to conceal inadequate art. If the player needs eight authored facings, revise the contract once before producing the remaining player directions; do not silently insert unrelated images. Player approval explicitly requires this review.

No duplicated terminal frame in looping clips. Idle may reuse a held pose within its specified minimum unique count; walking must contain distinct articulated motion. Duplicate-file detection is only a structural test: a recoloured still is not an acceptable animation even if its hash differs.

The listed FPS is reference playback. Attack wind-ups, shots and damage are simulation-owned; visual playback is retimed to those states. A five-frame wind-up does not authorize damage on an arbitrary animation-frame signal. Hit flashes must not restart locomotion every time a horde member takes damage.

## 4. Production method

Preferred route: one original or suitably licensed editable model/rig per family, repeatable camera/light render settings, then a consistent 2D cleanup pass. All frames in a clip come from that same source, not independent text-to-image requests. A directly painted sprite source is also acceptable if it passes the same anatomy, direction and loop review.

Image generation may explore a master concept. A generated contact sheet is a reference, not the production source or an animation. Do not declare a candidate approved because an assistant produced it. Do not include fonts, ripped Alien Shooter art, or marketplace source files whose terms prohibit public redistribution.

## 5. Full pack inventory

`pack.json` is the machine-readable inventory: **91 asset entries and 1,134 required frame slots**, including 892 actor frames. An entry may be a full actor family, a prop with several states/directions, an effect sequence, or one UI icon. These numbers describe planned production, not finished files.

Scope: one player, runner/spitter/charger/brute, one Brood Warden, twelve floor variants, six wall pieces, ten prop families, three infestation overlays, six blood decals, four weapon presentations, three support modules, fourteen effects, three pickups and twenty-four UI entries. No extra campaign assets or new gameplay systems are implied.

## 6. One current tree

```text
assets/pack_v1/
  SPEC.md
  pack.json
  BATCH_001.md
  families/<asset_id>/
    source/                 # editable source with public-use permission
    frames/<clip>/<dir>/000.png
    delivery.json           # source/frame hashes, reviews, approval
```

Keep only the current source and submission per family. Git history holds older versions. No approved/wip/final/rejected folder mazes and no parallel master atlases. Do not delete an existing playable project's prototype art until a replacement is approved and integrated deliberately.

## 7. Approval and delivery

Statuses are `draft`, `review`, and `approved`; an absent submission is `planned`. Approval requires the actual owner's review, an evidence reference, source rights, and hashes binding it to the reviewed bytes and specification. There is no auto-approve command.

Review anatomy/equipment continuity, direction coverage, normal/half-speed playback, silhouettes, alpha on dark and bright backgrounds, fixed pivots, terrain seams, and the player aim/strafe case. Validate the first complete family before widening production.

Tools reject wrong sizes/modes, invisible images, clipped borders, missing/extra frame IDs, fake duplicate motion, changed approved files, missing sources and incomplete approvals. They cannot decide whether a creature looks good, recognize every mirrored image, or verify legal ownership. The human review remains necessary.

`python tools/artpack.py audit` checks the contract and existing submissions. It explicitly reports missing production rather than treating an empty pack as finished. `check-family <id>` checks a complete submission. `export --asset <id> --out <new-folder>` exports only an approved complete family; omit `--asset` only when the whole pack is complete and approved.

Exports produce bounded PNG atlases, JSON frame/pivot metadata, Godot SpriteFrames resources and an AnimatedSprite2D scene. No source art or fonts are copied into runtime output. Exporting does not modify the game or prove engine import/performance. Run an actual Godot import and visual preview before gameplay integration.

## 8. Technical references

Godot supports both separate animation images and sprite sheets; SpriteFrames stores timing and animation data. Its AnimatedSprite2D offset provides the node/pivot alignment used by the exporter. Blender's orthographic camera supplies a repeatable asset view. These are capabilities, not validation of unrendered artwork.

- https://docs.godotengine.org/en/stable/tutorials/2d/2d_sprite_animation.html
- https://docs.godotengine.org/en/stable/classes/class_spriteframes.html
- https://docs.godotengine.org/en/stable/classes/class_animatedsprite2d.html
- https://docs.blender.org/manual/en/latest/render/cameras.html


## Active human-design revision 0.2.0

The owner selected a human rather than enclosed armour. The player has short hair, a visible face, exposed forearms, a fitted dark shirt, a light vest and olive trousers. The actor cells and pivots were enlarged once to contain death and attack bounds without changing physical scale; the table and pack.json are updated together. No per-frame stretching is permitted. All six families are review candidates, not owner-approved production. The separate integration preview is explicitly labelled as such; the production exporter still refuses unapproved art.
