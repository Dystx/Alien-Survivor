#!/usr/bin/env python3
"""Isolated verification, not a complete playable branch. Actual art is in the delivered ZIP.
Texture fixtures only validate script execution, never final visual quality.
"""
from pathlib import Path
import hashlib, os, re, shutil, subprocess, sys
root = Path(__file__).resolve().parents[1]
game = root / 'game'
engine = sys.argv[1]
subprocess.run(['git','apply','verification/ui.patch'],cwd=root,check=True)
for src,dst in [('finale.gd','simulation.gd'),('arena_view.gd','arena_view.gd'),('sprite_factory.gd','sprite_factory.gd')]:
    shutil.copyfile(root/'verification'/src,game/'scripts'/dst)
for name in ['main.gd','arena_view.gd']:
    file=game/'scripts'/name
    file.write_text(file.read_text().replace('Projection','IsoProjection'))
(game/'scripts/projection.gd').write_text('''extends RefCounted
const BASIS := Transform2D(Vector2(0.75, 0.375), Vector2(-0.75, 0.375), Vector2.ZERO)
static func project(point: Vector2) -> Vector2:
\treturn BASIS * point
static func unproject(point: Vector2) -> Vector2:
\treturn BASIS.affine_inverse() * point
static func input_basis() -> Transform2D:
\treturn BASIS.affine_inverse()
''')
test=game/'tests/run_tests.gd'
s=test.read_text().replace('sim.spawning_enabled = false','sim.spawning_enabled = false\n\tsim.finale_enabled = false',1)
s=s.replace('\t_test_settings()\n','\t_test_settings()\n\t_test_finale()\n\t_test_telegraphs()\n\t_test_hostile_sweeps_and_limits()\n\t_test_projection()\n',1)
s+=(root/'verification/finale_cases.gd').read_text()
test.write_text(s)
for name in ['simulation.gd','projection.gd','arena_view.gd','sprite_factory.gd','hud.gd','main.gd','input_router.gd']:
    source=(game/'scripts'/name).read_text()
    canonical='\n'.join(line.rstrip() for line in source.splitlines() if line.strip() and not line.lstrip().startswith('#'))
    print('CANONICAL_SHA256 '+name+' '+hashlib.sha256(canonical.encode()).hexdigest(),flush=True)
(game/'tests/render_smoke.gd').write_text('''extends SceneTree
var scene
var ticks: int = 0
func _initialize() -> void:
\t_setup.call_deferred()
func _setup() -> void:
\tscene = load("res://scenes/main.tscn").instantiate()
\troot.add_child(scene)
\tscene.sound.muted = true
func _process(_dt: float) -> bool:
\tif scene == null:
\t\treturn false
\tticks += 1
\tif ticks == 5:
\t\tscene._on_action("boss_test")
\t\tscene.sim.health = 10000.0
\tif ticks == 15:
\t\tfor kind: String in ["runner", "spitter", "charger", "brute"]:
\t\t\tvar enemy = scene.sim.add_enemy(scene.sim.player + Vector2(190, 70), 0.0, kind)
\t\t\tenemy.skill_cooldown = 0.0
\t\tscene.sim._add_hazard(scene.sim.player + Vector2(80,60), 28, "acid", 4.0, 6.0)
\tif ticks == 35:
\t\tscene.sim.boss.warning = 0.0
\t\tscene.sim.boss.health = scene.sim.boss.max_health * 0.4
\t\tscene.sim._arm_attack(scene.sim.boss, "pulse", Vector2.LEFT, 1.0)
\tif ticks == 55:
\t\tscene.sim._arm_attack(scene.sim.boss, "charge", Vector2.LEFT, 1.0)
\tif ticks == 75:
\t\tscene.sim._arm_attack(scene.sim.boss, "fan", Vector2.LEFT, 1.0)
\tif ticks == 95:
\t\tscene.sim.xp = scene.sim.xp_needed()
\tif ticks == 115:
\t\tif not scene.sim.offers.is_empty():
\t\t\tscene._on_upgrade(scene.sim.offers[0])
\tif ticks == 130:
\t\tscene._on_action("pause")
\tif ticks == 145:
\t\tscene._on_action("resume")
\t\tscene.sim.damage_enemy(scene.sim.boss, 100000.0)
\tif ticks == 165:
\t\tif scene.sim.result != "BROOD WARDEN ELIMINATED":
\t\t\tpush_error("Boss scene did not reach victory")
\t\t\tquit(1)
\t\t\treturn false
\t\tscene._on_action("start")
\tif ticks == 185:
\t\tif scene.sim.finale_started or scene.sim.boss != null:
\t\t\tpush_error("Scene restart retained boss state")
\t\t\tquit(1)
\t\t\treturn false
\t\tprint("FINALE_SCENE_FIXTURE_PASS")
\t\tquit(0)
\treturn false
''')
commands=[([engine,'--headless','--path',str(game),'--editor','--import','--quit'],0,None),([engine,'--headless','--path',str(game),'--script','res://tests/run_tests.gd'],0,'ALIEN_SURVIVOR_TESTS:'),([engine,'--headless','--path',str(game),'--script','res://tests/run_tests.gd','--','--self-test-failure'],1,'intentional runner self-check'),([engine,'--headless','--path',str(game),'--fixed-fps','60','--script','res://tests/render_smoke.gd','--','--ci-art-fixtures'],0,'FINALE_SCENE_FIXTURE_PASS')]
if shutil.which('xvfb-run'):
    commands.append((['xvfb-run','-a',engine,'--path',str(game),'--audio-driver','Dummy','--fixed-fps','60','--script','res://tests/render_smoke.gd','--','--ci-art-fixtures'],0,'FINALE_SCENE_FIXTURE_PASS'))
else:
    print('DRAW EXECUTION NOT RUN: xvfb-run missing',flush=True)
for cmd,code,marker in commands:
    print('RUN',' '.join(cmd),flush=True)
    env=dict(os.environ,LIBGL_ALWAYS_SOFTWARE='1')
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=180,env=env)
    output=result.stdout+result.stderr
    print(output,flush=True)
    if result.returncode!=code or re.search(r'SCRIPT ERROR:|Parse Error:|^ERROR:',output,re.M) or (marker and marker not in output):
        raise SystemExit('VERIFICATION FAILED')
print('FINALE_ENGINE_AND_FIXTURE_SCENE_PASS. Actual art import/appearance, physical controls, Mac/mobile and human-played balance are NOT established by this fixture test.',flush=True)
