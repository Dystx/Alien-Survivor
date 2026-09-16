#!/usr/bin/env python3
"""Temporary verification branch. Not the complete art-integrated deliverable.
Only this job's checkout is patched. main and feat/first-playable are unchanged.
"""
from pathlib import Path
import hashlib, re, shutil, subprocess, sys
root = Path(__file__).resolve().parents[1]
game = root / 'game'
engine = sys.argv[1]
source = (root / 'verification/finale.gd').read_text()
canonical = '\n'.join(line.rstrip() for line in source.splitlines() if line.strip() and not line.lstrip().startswith('#'))
print('FINALE_LOGIC_CANONICAL_SHA256=' + hashlib.sha256(canonical.encode()).hexdigest(), flush=True)
(game / 'scripts/simulation.gd').write_text(source)
(game / 'scripts/projection.gd').write_text('''extends RefCounted
const BASIS := Transform2D(Vector2(0.75, 0.375), Vector2(-0.75, 0.375), Vector2.ZERO)
static func project(point: Vector2) -> Vector2:
\treturn BASIS * point
static func unproject(point: Vector2) -> Vector2:
\treturn BASIS.affine_inverse() * point
static func input_basis() -> Transform2D:
\treturn BASIS.affine_inverse()
''')
test = game / 'tests/run_tests.gd'
s = test.read_text()
s = s.replace('sim.spawning_enabled = false', 'sim.spawning_enabled = false\n\tsim.finale_enabled = false', 1)
s = s.replace('\t_test_settings()\n', '\t_test_settings()\n\t_test_finale()\n\t_test_telegraphs()\n\t_test_hostile_sweeps_and_limits()\n\t_test_projection()\n', 1)
s += (root / 'verification/finale_cases.gd').read_text()
test.write_text(s)
main = game / 'scripts/main.gd'
s = main.read_text().replace('sim.time_limit = 3.0', 'sim.time_limit = 3.0\n\t\tsim.finale_enabled = false')
main.write_text(s)
commands = [([engine, '--headless', '--path', str(game), '--editor', '--import', '--quit'], 0, None), ([engine, '--headless', '--path', str(game), '--script', 'res://tests/run_tests.gd'], 0, 'ALIEN_SURVIVOR_TESTS:'), ([engine, '--headless', '--path', str(game), '--script', 'res://tests/run_tests.gd', '--', '--self-test-failure'], 1, 'intentional runner self-check')]
for cmd, code, marker in commands:
    print('RUN', ' '.join(cmd), flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    output = result.stdout + result.stderr
    print(output, flush=True)
    if result.returncode != code or re.search(r'SCRIPT ERROR:|Parse Error:|^ERROR:', output, re.M) or (marker and marker not in output):
        raise SystemExit('VERIFICATION FAILED')
print('FINALE_LOGIC_ENGINE_PASS. This job does NOT validate the new renderer, artwork, phone performance or a human-played run.', flush=True)
