# First articulated motion source

This is original source geometry for **draft** player and runner locomotion, not a final art approval or an installed game upgrade.

The player has 104 named mesh parts; the runner has 82. Each is assembled once. Inverse-kinematic limb targets articulate those same parts over a gait cycle. The camera and lights stay fixed while the model turns to E/S/W/N. No frames are drawn by recolouring, translating, mirroring or rotating a character bitmap. No earlier generated sheet or commercial game asset is used as geometry or texture input.

## Editable files

`../families/<id>/source/rig.json` supplies the palette, physical scale and gait parameters. `render_motion.py` supplies the named geometry and kinematic source; shared code is intentionally stored once. The generated `master.glb` contains the meshes, articulated transform nodes and a baked walk/move animation. It is an editable interchange model, **not a skinned humanoid armature**. The procedural source remains authoritative for repeat rendering; changes made only to the interchange GLB are not read back by this renderer. Blender import/editing has not been interactively tested.

The GLB uses standard Y-up through its root transform. Authoring source coordinates use X-right/Y-forward/Z-up; the specification's ground coordinates are u=source X, v=-source Y. Pixels per world unit, camera elevation, transparent cell, and pivot follow the existing pack contract. The GLB's last animation key closes its interpolation loop; the exported PNG sequence deliberately excludes that repeated endpoint.

## Rebuild on a machine with the dependencies installed

```sh
python3 -m pip install -r assets/pack_v1/source/requirements.txt
python3 assets/pack_v1/source/render_motion.py
python3 assets/pack_v1/source/record_motion.py
python3 assets/pack_v1/source/test_motion.py
python3 tools/artpack.py audit
```

Rendering uses VTK offscreen OpenGL and fixed material vertex colours, not a runtime 3D engine. Software OpenGL worked in the authoring container. Cross-driver pixel-perfect equivalence is not promised; the delivery hashes bind each actual render. The script refuses to overwrite an approved family's files.

## What this draft does not solve

These are the first walk/move loops only. The remaining base actions, player strafe/reverse aiming coverage, full art polish and human approval are still outstanding. Art quality, anatomy, foot sliding, aiming and the four-direction budget require visual review. We do not count these as approved runtime sprites or silently replace the existing game.
