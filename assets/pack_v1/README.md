# Official Asset Pack v1

**Current work: the runner has 84 review-candidate frames and a working native Godot viewer. The exact conversation-delivered human is visually locked by the owner; the robot-like procedural draft is not that approved human. The whole pack is not finished or approved.**

Read `player_visual_lock.json`, then `SPEC.md`, `pack.json` and `BATCH_001.md`. The latest explicit human approval overrides the old armoured/visor character proposal. It does not approve firing, new player redraws, the runner or the complete animation catalogue.

## Current runner family

One current editable source and frame set, not independent generated sheets:

- `families/runner/frames/`: idle (4), move (6), attack (4), hit (2), death (5), each in e/s/w/n. Total **84 PNGs**, fixed 96x96 cells and pivot 48,78.
- `source/runner_family.py`: refinement of the original runner mesh with articulated pose functions and fixed camera/lighting. `source/render_motion.py` provides shared mesh/render support.
- `families/runner/source/`: current recipe, editable mesh/node-rig GLB and mouth sockets. The GLB contains its movement track; other action poses remain in the source script. It is not a skinned production armature.
- `families/runner/review_runtime/`: atlas, SpriteFrames and exact frame/pivot metadata for review. This is not an approved runtime export.
- `families/runner/delivery.json`: source/frame hashes; status `review`, owner approval unset.
- `art_reviews/runner_*.gif` at repository root: the five moving action previews.

Runner binaries were published at `b6203e225bb34b1a30efc5d0a13d85e1e4803506`. Its finish still needs artistic review against the detailed gritty target; structural completeness is not visual approval.

## Native runner review

Open `art_reviews/runner_lab/project.godot` at repository root in Godot 4.7.2 standard and Run. This is a separate asset viewer, not the survival game. It uses the actual current runner atlas and shows all four views at native and 2x scale, with clip selection, pause, half speed, frame scrubbing, pivot markers and light/dark backgrounds. Non-looping attacks and deaths hold their final frame.

The viewer's three runtime asset files are exact copies of `families/runner/review_runtime`, not another source master. Its verifier checks that equality before engine execution. Rerendering the source requires deliberately refreshing the review copy; drift is a failed check.

Verified code revision: `f0109fc70f0fa623daf4ff3255c9f883f3b6ef1a`.

Actual run: https://github.com/Dystx/Alien-Survivor/actions/runs/35175038064

Godot 4.7.2 imported the **actual runner PNG and SpriteFrames**, passed **45 viewer/resource/playback assertions**, and captured move/attack/death with software OpenGL. Unlike earlier gameplay fixture checks, this isolated viewer used no substitute artwork. The workflow artifact includes its tested project, engine log, hashes and three actual screenshots. This proves resource loading and the exercised presentation paths, not final aesthetic quality, Mac/mobile/controller performance, or gameplay integration.

## Preserve the approved human

`player_visual_lock.json` binds the approved 43-cell HumanReview appearance to exact hashes. Do not redraw, recolour, rescale or replace it, and do not treat another human model with more frame slots as approved.

The older procedural player files/previews still visible in this art branch are superseded experiments, **not** the locked body or approved production assets. The old automatic motion renderer is disabled so it cannot regenerate them as the chosen player. The actual approved human PNG package is still supplied through the conversation, not fully published in this official tree. That publication gap remains explicit.

The separate `fix/locked-human-firing` branch contains the firing correction around those exact human pixels. Its completed engine run `35172540277` passed 74 gameplay, 27 human and 64 firing checks with synthetic textures; consult its owning `firing_review/README.md` for that distinct validation scope. It does not modify the runner or grant firing approval.

## Full catalogue and checks

The catalogue has 91 named entries and 1,134 planned frame slots. Its first base player/runner batch plans 212 slots, with additional player aim coverage required before complete player export. Numbers are requirements, not finished artwork. No full family has final owner approval.

```sh
python3 -m pip install -r tools/requirements-artpack.txt
python3 -m unittest discover -s tests -p 'test_artpack*.py' -v
python3 tools/artpack.py audit
python3 tools/artpack.py check-family runner
```

A passing structural audit can still report `ART INCOMPLETE / NOT RELEASE-READY`. It can count old unapproved draft files; that is not approval of the rejected player's appearance. Current full-pack completion must not be inferred from a green CI badge or from one complete runner candidate.

After a complete family has actual owner approval and recorded source permission:

```sh
python3 tools/artpack.py export --asset runner --out art_build/pack_v1
```

The production exporter refuses incomplete or unapproved families and existing outputs. It creates PNG atlases, metadata, SpriteFrames and a sprite scene. Gameplay integration is a separate reviewed change. No command fabricates owner approval.

## Further production

Keep the runner's current source until its visual review is resolved; next work is the spitter family under the same camera/material/scale contract. Do not expand content or alter human art merely to populate more frame slots.

Use one current source/frame/delivery tree per family, with history in Git. No parallel final/rejected/archive master folders. Review real loops, native size, alpha, pivots, anatomy, facing, contact and attack timing. Checksums cannot establish artistic quality or source rights. Do not bundle font files, restricted stock sources, receipts, credentials or signing files.
