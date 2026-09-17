# Locked-human firing correction

This branch continues the owner's request to repair firing presentation while preserving the exact human from `Alien_Survivor_Human_Review.zip`. It is not approval of the alternate procedural actor pack.

Locked atlas SHA-256: `e77d10fbeda8fa5ee3532e3e1b5618ce4f0e3084458af4c4745ed1f49ed9ba2c`.
Locked source package SHA-256: `3adf0acdb9d5c7ddf12b072e7cb98bc187227a920913682c92b293ed44d93af6`.

The correction targets muzzle coordinates, root-anchored short flashes, rear-view occlusion, stable feet/no whole-body recoil, and per-projectile visual attachment capture. Damage, targeting and firing cooldowns are unchanged. Four fixed gun views remain a limitation; this work does not silently quantize gameplay aim or redraw the approved body.

Status: implementation in progress. Source changes and verification results must be read before treating this as a tested build. The playable main/first-playable branches are not modified.
