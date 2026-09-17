# Locked-human firing correction

Firing correction source on `fix/locked-human-firing`. Its code is now engine-tested with explicit synthetic texture fixtures. This is still pending visual review, not approval of a new animation family or a finished game release.

## Exact approved human

Input: `Alien_Survivor_Human_Review.zip`, SHA-256 `3adf0acdb9d5c7ddf12b072e7cb98bc187227a920913682c92b293ed44d93af6`.

Locked human atlas: `e77d10fbeda8fa5ee3532e3e1b5618ce4f0e3084458af4c4745ed1f49ed9ba2c`.

All 43 cells, body appearance, scale, ground pivot and locomotion pixels remain unchanged. The different procedural human/robot models on other branches are not approved substitutes.

## Implemented

- Per-facing and per-hit-pose muzzle coordinates calibrated against the locked cells.
- Flash attached at its emission root, not centred over the barrel; the dark barrel fragment is excluded from the effect crop.
- Short 55ms flash follows movement, disappears on facing changes/death, and draws behind the body for the rear view.
- No whole-body recoil translation; feet remain at the original ground anchor.
- Per-projectile visual origin captured outside drawing, bounded cleanup, and no backwards initial tracer tail.
- Native Firing Attachment Review: standing/walking, turns, hit poses, pause, half speed and socket markers, using the gameplay presentation class.

Simulation, damage, targeting, cooldowns, input and balance are unchanged. Four fixed gun views remain a visual limitation. No free gameplay aiming is quantized to hide it. Authored shooting/strafe coverage and the rest of the production pack are not completed by this change.

## Apply safely

The correction is in `firing_presentation.gd`, `firing_review.gd`, `firing_tests.gd`, `firing.patch`, `apply.py` and `verify.py`.

Use the exact HumanReview input and a separate, nonexistent destination:

```sh
python3 firing_review/apply.py --source /path/to/AlienSurvivor-HumanReview --out /path/to/AlienSurvivor-FiringFix
```

The installer verifies the atlas and expected source hashes, rejects symlinks and existing/nested outputs, checks protected bytes and does not modify the input. Python and `patch` are required. This branch contains the correction source and test setup, not the complete human/scenery image package. The complete art-equipped source ZIP is supplied in the conversation.

## Validation now completed

Verified GitHub Actions run: https://github.com/Dystx/Alien-Survivor/actions/runs/35172540277

Tested commit: `9be8cc5942f5d74c0fca4cfb28ce342a0f2af6cc`; job `105047087099`.

Godot `4.7.2.stable.official.ed1daf0bf`, Ubuntu 24.04.5; software drawing used Compatibility OpenGL with Mesa llvmpipe under Xvfb.

- Project import / GDScript compilation passed.
- 74 gameplay/settings assertions passed.
- 27 human-animation assertions passed.
- 64 firing assertions passed.
- Intentional failing test correctly failed.
- Human, finale and firing scene checks passed headlessly; the firing review scene also ran successfully with software OpenGL.

**All textures in this engine job were explicit synthetic fixtures.** It proves code execution and drawing paths, not the appearance of the actual human/effect pixels, Mac/controller/touch behavior, audible sound, performance or an exported game.

Separate local checks verified the delivered FiringFix's seven relevant canonical GDScript hashes against that successful job. The locked atlas hash also matches. Canonicalization removes blank/full-line-comment lines and trailing whitespace, not code or indentation.

Earlier local image/package checks remain separate: 11 image/resource and 7 installer-safety checks passed; 155 protected source/art files and 92 original runtime images matched their baseline hashes; a clean zero-fuzz patch reproduced the delivered code. Python composition previews use actual sprites but are not Godot captures.

The earlier workflow-writing blocker is superseded by the recorded successful run above. It must not be mistaken for approval of the artwork. Open the actual source ZIP in the pinned editor and review **Firing Attachment Review** before accepting its visual result.

Main and the existing playable branches remain unchanged. Firing approval is pending; no new family or full-pack approval was granted.
