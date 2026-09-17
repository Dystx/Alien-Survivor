# Locked-human firing correction

The firing correction source is implemented on `fix/locked-human-firing`. This is a review patch, not an engine-verified release or a new approved asset family.

## Exact approved human

This work targets `Alien_Survivor_Human_Review.zip` with package SHA-256 `3adf0acdb9d5c7ddf12b072e7cb98bc187227a920913682c92b293ed44d93af6` and human atlas SHA-256 `e77d10fbeda8fa5ee3532e3e1b5618ce4f0e3084458af4c4745ed1f49ed9ba2c`. It does not promote the different procedural human/robot models on other branches. All 43 human cells, scale, ground pivot and locomotion pixels remain unchanged.

## Implemented

- Per-facing/per-hit-pose muzzle coordinates calibrated against the locked cells.
- Flash attached at its emission root rather than its centre, with the dark barrel fragment excluded from the effect crop.
- A short 55ms flash that follows the current muzzle while moving, disappears on direction changes/death, and draws behind the body for the rear view.
- Removal of whole-body recoil translation; feet stay at the original ground anchor.
- Per-projectile visual attachment captured once outside drawing, bounded lifecycle cleanup, and no tracer tail behind the barrel at spawn.
- A native Firing Attachment Review screen using the same presentation class as gameplay: standing/walking, turns, hit poses, pause, half speed and socket markers.

Simulation, damage, targeting, cooldowns, input and balance are unchanged. Four fixed gun views remain a visual limitation; free gameplay aiming is not quantized to hide it. This does not claim new authored shoot/strafe animations.

## Files

`firing_presentation.gd`, `firing_review.gd`, `firing_tests.gd`, `firing.patch`, `apply.py` and `verify.py`. The patch changes only the existing arena presentation, menu action and HUD button. `apply.py` reconstructs the scene and copies the new scripts into a fresh copy.

## Apply safely

Use the exact previously delivered HumanReview project as input and a new, separate output directory:

```sh
python3 firing_review/apply.py --source /path/to/AlienSurvivor-HumanReview --out /path/to/AlienSurvivor-FiringFix
```

The installer verifies the locked atlas and expected source hashes, rejects symlinks and existing/nested outputs, checks protected bytes and never modifies the input. Python and the `patch` command are required. A complete art-equipped source ZIP is also supplied in the project conversation. That ZIP includes the original human/scenery pixels; this branch does not publish the full artwork binaries.

## Validation actually performed

Eleven existing Python real-image/resource tests passed and seven local installer-safety tests passed. Static resource checks resolve 24 references, and all 92 existing runtime art checksums pass. All 155 protected source/art files match the input baseline. A zero-fuzz application on a clean extraction was successful and produced the same new GDScript code as the delivered package. These are file/image/installer checks, not a GDScript parser or runtime proof.

The new engine tests have NOT run. Godot was unavailable locally, and the attempted new CI workflow write was blocked. It was not retried through a different publishing route. The supplied verification runner is executable test source, not a passing CI result. Earlier engine results belong to the parent build, not these changed scripts. The additional local installer test file was also not committed after its write was blocked; its seven executed tests are supplied in the conversation package.

Before export, run Godot 4.7.2 import, the existing gameplay/human tests and `res://tests/firing_tests.gd`, then inspect the real Firing Attachment Review screen. The Python animated preview uses actual sprite pixels and the new attachment math but is not a Godot capture. Mac/controller/touch, sound, performance and exports are unverified.

Main and the existing playable branches remain unchanged. Firing approval is pending. The remaining alien, environment and effects families are not being represented as newly completed in this correction.
