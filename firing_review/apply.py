#!/usr/bin/env python3
"""Apply the firing patch to an exact HumanReview copy; never edit the input.
No download, account access, engine execution or artwork approval is performed.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ATLAS = 'assets/human_survivor/human_atlas.png'
ATLAS_HASH = 'e77d10fbeda8fa5ee3532e3e1b5618ce4f0e3084458af4c4745ed1f49ed9ba2c'
BASE = {
    'arena_view.gd': '643b97ed56543b7faab3a7d077500d3afcb503f721d3c783896e2bd100ac5695',
    'main.gd': 'e97cbe06a5411c1df25b882ef841460bf79bad70fe099fe804ed4ff98bf6d5d7',
    'hud.gd': '3c697bc31176bb36b19e7b05d95b226fda55d8b9a2084ffcf1142b2c43046b26',
}
SCENE = '''[gd_scene load_steps=2 format=3]
[ext_resource type="Script" path="res://scripts/firing_review.gd" id="1"]
[node name="FiringReview" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
script = ExtResource("1")
'''

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical(path: Path) -> str:
    return '\n'.join(line.rstrip() for line in path.read_text().splitlines()
                     if line.strip() and not line.lstrip().startswith('#')) + '\n'

def preflight(source: Path, destination: Path) -> None:
    if destination.exists():
        raise ValueError('Destination already exists; no files were changed.')
    if destination == source or source in destination.parents:
        raise ValueError('Destination must be separate from the input project.')
    if not (source / 'project.godot').is_file():
        raise ValueError('Select the folder containing the original project.godot.')
    if any(path.is_symlink() for path in source.rglob('*')):
        raise ValueError('Source contains a symlink; use a freshly extracted project.')
    if sha(source / ATLAS) != ATLAS_HASH:
        raise ValueError('Wrong human atlas. The locked body must not be replaced.')
    for name, expected in BASE.items():
        if hashlib.sha256(canonical(source / 'scripts' / name).encode()).hexdigest() != expected:
            raise ValueError('Source was modified or is another build: ' + name)

def apply(source: Path, destination: Path) -> Path:
    source, destination = source.resolve(), destination.resolve()
    preflight(source, destination)
    patch = shutil.which('patch')
    if not patch:
        raise RuntimeError('The patch command is missing; use the complete review ZIP.')
    for name in ['firing.patch', 'firing_presentation.gd', 'firing_review.gd', 'firing_tests.gd']:
        if not (HERE / name).is_file():
            raise FileNotFoundError(HERE / name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    protected = {p.relative_to(source): sha(p) for folder in ['assets', 'art']
                 for p in (source / folder).rglob('*') if p.is_file()}
    protected.update({Path('scripts') / n: sha(source / 'scripts' / n)
                      for n in ['simulation.gd', 'balance.gd', 'human_animation.gd', 'input_router.gd']})
    with tempfile.TemporaryDirectory(prefix='alien-firing-', dir=destination.parent) as tmp:
        work = Path(tmp) / 'project'
        shutil.copytree(source, work, ignore=shutil.ignore_patterns('.godot', '.git', '__pycache__'))
        for name in BASE:
            (work / 'scripts' / name).write_text(canonical(work / 'scripts' / name))
        subprocess.run([patch, '-p1', '--batch', '--fuzz=0', '-i', str(HERE / 'firing.patch')],
                       cwd=work, check=True, capture_output=True, text=True, timeout=30)
        for name in ['firing_presentation.gd', 'firing_review.gd']:
            shutil.copyfile(HERE / name, work / 'scripts' / name)
        shutil.copyfile(HERE / 'firing_tests.gd', work / 'tests' / 'firing_tests.gd')
        (work / 'scenes' / 'firing_review.tscn').write_text(SCENE)
        project = work / 'project.godot'
        project.write_text(project.read_text().replace('Alien Survivor — Human Review',
                                                       'Alien Survivor — Locked Human Firing'))
        for relative, expected in protected.items():
            if sha(work / relative) != expected:
                raise RuntimeError('Protected input changed: ' + str(relative))
        # Old test evidence is not current evidence for these changed scripts.
        (work / 'tests' / 'verified_source_hashes.json').unlink(missing_ok=True)
        (work / 'VALIDATION.md').write_text(
            '# Firing correction validation\n\n'
            'Exact locked human, all original art, simulation, input and balance preserved. '
            'Patch application and hashes checked; these are not GDScript compilation.\n\n'
            'New engine tests have NOT run in this preparation environment. The workflow '
            'write was blocked and no local Godot binary was available. Run the included '
            'firing_tests.gd as well as the existing gameplay and human tests in Godot 4.7.2. '
            'Earlier passing engine reports apply to the parent build, not this revision.\n')
        (work / 'README.md').write_text(
            '# Alien Survivor — locked human firing correction\n\n'
            'Open project.godot with the existing pinned Godot 4.7.2. Run the project '
            'and select FIRING ATTACHMENT REVIEW. The human body is unchanged; the muzzle '
            'root, flash lifetime, recoil and projectile visual origins were revised. '
            'This is source for review, not a validated executable or an approved full pack. '
            'Read VALIDATION.md.\n')
        (work / 'READ_ME_FIRST.txt').write_text(
            'Import this folder/project.godot. There is no extra game folder.\n'
            'Use a separate copy; keep your previously working build.\n'
            'New engine checks are pending. Choose FIRING ATTACHMENT REVIEW from the menu.\n')
        manifest = [sha(p) + '  ' + p.relative_to(work).as_posix()
                    for p in sorted(work.rglob('*')) if p.is_file() and p.name != 'PACKAGE_SHA256.txt']
        (work / 'PACKAGE_SHA256.txt').write_text('\n'.join(manifest) + '\n')
        if destination.exists():
            raise ValueError('Destination appeared during preparation; refusing replacement.')
        work.rename(destination)
    return destination

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        print('FIRING SOURCE PREPARED:', apply(args.source, args.out))
        print('ENGINE EXECUTION: NOT RUN. ARTWORK APPROVAL: NOT GRANTED.')
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        parser.exit(1, 'No input files changed. ' + str(exc) + '\n')
