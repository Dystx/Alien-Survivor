# Runner native review

Import this directory's `project.godot` into the existing Godot 4.7.2 standard editor and press Run. This is an isolated asset viewer, not the survival game. The human is not loaded or modified.

Idle, move, attack, hit and death each have all four views. Use normal/half-speed playback, pause, frame scrubbing, background and pivot controls. Death and attacks hold their final frame until replayed. The artwork is a review candidate, not owner-approved production art.

The three files in `assets/runner_review` are an exact review copy of the current official runner family's `review_runtime` files at source commit b6203e225bb34b1a30efc5d0a13d85e1e4803506. They are not a second master. Authoring and individual frames remain under `assets/pack_v1/families/runner` and `assets/pack_v1/source/runner_family.py` at repository root.

`check_review.gd` tests actual resource loading and playback state. `capture_review.gd` records actual engine screenshots when run with a graphical renderer. Tests require execution; their presence is not a passing result. No game balance, simulation or human approval changes are included.
