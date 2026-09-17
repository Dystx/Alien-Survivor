#!/usr/bin/env python3
"""Real spitter/runner pixels; inherited human/scenery are explicit CI fixtures.
No fixture game assets are included in the evidence artifact.
"""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'spitter_review';GAME=ROOT/'game';ENGINE=sys.argv[1]
ART='3a4d3b6acce17cf45deb14ff282f5daaf7f25c37'
parent=ROOT/'runner_review/verify.py'
exec(compile(parent.read_text().split('\ncommands=[',1)[0],str(parent),'exec'),{'__file__':str(parent),'__name__':'spitter_staging'})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(p):return '\n'.join(l.rstrip() for l in p.read_text().splitlines() if l.strip() and not l.lstrip().startswith('#'))+'\n'
protected=[GAME/'scripts'/n for n in ['human_animation.gd','firing_presentation.gd','runner_animation.gd','simulation.gd','input_router.gd','balance.gd']]
before={str(p):sha(p) for p in protected}
expected={'arena_view.gd':'982166537cceffaaa32aad298e7a094776edbdbc80bf001e9e262ea47d4c1142','main.gd':'39c710a3dd2b2b8c8a1a1bf960d7af67730f023f095dab6a8abfb443109b1849','hud.gd':'7e64c9dc850f8cc50eef1a8878e679aea1998b76549805c36cf6c3ff25c954ce'}
for name,digest in expected.items():
 p=GAME/'scripts'/name;s=canon(p)
 if hashlib.sha256(s.encode()).hexdigest()!=digest:raise ValueError('Unexpected source baseline '+name)
 p.write_text(s)
subprocess.run(['patch','-p1','--fuzz=0','--batch','-i',str(HERE/'integration.patch')],cwd=GAME,check=True)
for n in ['spitter_animation.gd','spitter_review.gd']:shutil.copyfile(HERE/n,GAME/'scripts'/n)
shutil.copyfile(HERE/'spitter_tests.gd',GAME/'tests/spitter_tests.gd')
(GAME/'scenes/spitter_review.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://scripts/spitter_review.gd" id="1"]\n[node name="SpitterReview" type="Control"]\nlayout_mode = 3\nanchors_preset = 15\nanchor_right = 1.0\nanchor_bottom = 1.0\nscript = ExtResource("1")\n')
subprocess.run(['git','fetch','--depth=1','origin',ART],cwd=ROOT,check=True)
artifact=ROOT/'spitter_evidence';artifact.mkdir()
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',ART,'--','assets/pack_v1/families/spitter'],cwd=ROOT,text=True).splitlines()
for rel in paths:
 relative=Path(rel).relative_to('assets/pack_v1/families/spitter')
 target=artifact/'spitter'/relative;target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(subprocess.check_output(['git','show',ART+':'+rel],cwd=ROOT))
runtime=GAME/'assets/spitter_review';shutil.copytree(artifact/'spitter/review_runtime',runtime)
if any(sha(Path(p))!=v for p,v in before.items()):raise ValueError('Protected human/firing/simulation source changed')
(GAME/'tests/spitter_scene.gd').write_text('''extends SceneTree
var scene
var review
var ticks: int = 0
var frozen: float = 0.0
func _initialize() -> void:
\tsetup.call_deferred()
func setup() -> void:
\tscene = load("res://scenes/main.tscn").instantiate()
\troot.add_child(scene)
\tcurrent_scene = scene
\tscene.sound.muted = true
func require(ok: bool, label: String) -> void:
\tif not ok:
\t\tpush_error(label)
\t\tquit(1)
func _process(_dt: float) -> bool:
\tticks += 1
\tif ticks == 5:
\t\tscene._on_action("spitter_test")
\t\trequire(scene.sim.enemies.size() == 2, "Test must spawn two clear spitter targets")
\tif ticks == 12:
\t\tvar enemy = scene.sim.enemies[0]
\t\tenemy.warning = 0.0
\t\tscene.sim._arm_attack(enemy, "spit", Vector2.DOWN, 0.65)
\tif ticks == 25:
\t\tvar enemy = scene.sim.enemies[0]
\t\trequire(scene.view.spitters.live[enemy.id].clip == "windup", "Combat warning pose missing")
\t\tscene._on_action("pause")
\t\tfrozen = scene.view.spitters.live[enemy.id].age
\tif ticks == 35:
\t\tvar enemy = scene.sim.enemies[0]
\t\trequire(scene.view.spitters.live[enemy.id].age == frozen, "Pause advanced spitter")
\t\tscene._on_action("resume")
\tif ticks == 70:
\t\tvar enemy = scene.sim.enemies[0]
\t\tscene.sim.events.clear()
\t\tscene.sim.damage_enemy(enemy, 10000.0)
\t\tscene.view.advance(0.016, false, scene.sim.events)
\tif ticks == 75:
\t\trequire(not scene.view.spitters.deaths.is_empty(), "Spitter fall missing")
\tif ticks == 115:
\t\tscene._on_action("spitter_review")
\t\tscene = null
\tif ticks == 125:
\t\treview = current_scene
\t\trequire(review.clip == "move", "Spitter reviewer missing")
\t\treview._action("Windup")
\tif ticks == 150: review._action("Attack")
\tif ticks == 165: review._action("Recovery")
\tif ticks == 180: review._action("Death")
\tif ticks == 205:
\t\treview._action("Pause")
\t\tfrozen = review.clock
\tif ticks == 220:
\t\trequire(review.clock == frozen, "Viewer pause failed")
\t\treview._action("Pause")
\t\treview._action("0.5x")
\tif ticks == 235: review._action("Return")
\tif ticks == 250:
\t\tscene = current_scene
\t\tscene._on_action("start")
\t\trequire(scene.view.spitters.live.is_empty() and scene.view.spitters.deaths.is_empty(), "Restart retained spitter states")
\t\tprint("SPITTER_SCENE_PASS")
\t\tquit(0)
\treturn false
''')
(GAME/'tests/capture_spitter.gd').write_text('''extends SceneTree
var scene
var ticks: int = 0
func _initialize() -> void:
\tsetup.call_deferred()
func setup() -> void:
\tscene = load("res://scenes/spitter_review.tscn").instantiate()
\troot.add_child(scene)
\tscene.set_process(false)
\tDirAccess.make_dir_recursive_absolute("res://captures")
func _process(_dt: float) -> bool:
\tif scene == null: return false
\tticks += 1
\tif ticks == 3:
\t\tscene._action("Windup")
\t\tscene.clock = 0.4
\t\tscene.queue_redraw()
\tif ticks == 8: capture("windup")
\tif ticks == 10:
\t\tscene._action("Attack")
\t\tscene.clock = 0.18
\t\tscene.queue_redraw()
\tif ticks == 15: capture("attack")
\tif ticks == 17:
\t\tscene._action("Death")
\t\tscene.clock = 0.45
\t\tscene.bright = true
\t\tscene.queue_redraw()
\tif ticks == 22: capture("death")
\tif ticks == 26:
\t\tprint("SPITTER_REAL_CAPTURE_PASS")
\t\tquit(0)
\treturn false
func capture(name: String) -> void:
\tvar im := root.get_texture().get_image()
\tif im == null or im.is_empty() or im.save_png("res://captures/spitter_" + name + ".png") != OK:
\t\tpush_error("Missing actual spitter capture")
\t\tquit(1)
''')
commands=[([ENGINE,'--headless','--path',str(GAME),'--editor','--import','--quit'],0,None)]
for file,marker in [('run_tests.gd','ALIEN_SURVIVOR_TESTS:'),('human_animation_tests.gd','HUMAN_ANIMATION_TESTS:'),('firing_tests.gd','FIRING_TESTS:'),('runner_tests.gd','RUNNER_ANIMATION_TESTS:'),('spitter_tests.gd','SPITTER_TESTS:')]:
 commands.append(([ENGINE,'--headless','--path',str(GAME),'--script','res://tests/'+file],0,marker))
commands.append(([ENGINE,'--headless','--path',str(GAME),'--script','res://tests/run_tests.gd','--','--self-test-failure'],1,'intentional runner self-check'))
for file,marker in [('render_smoke.gd','FINALE_SCENE_FIXTURE_PASS'),('firing_scene.gd','FIRING_SCENE_PASS'),('runner_scene.gd','RUNNER_SCENE_PASS'),('spitter_scene.gd','SPITTER_SCENE_PASS')]:
 cmd=[ENGINE,'--path',str(GAME),'--audio-driver','Dummy','--fixed-fps','60','--script','res://tests/'+file,'--','--ci-art-fixtures']
 commands.append(([ENGINE,'--headless']+cmd[1:],0,marker))
 if file=='spitter_scene.gd':commands.append((['xvfb-run','-a']+cmd,0,marker))
commands.append((['xvfb-run','-a',ENGINE,'--path',str(GAME),'--audio-driver','Dummy','--fixed-fps','60','--script','res://tests/capture_spitter.gd'],0,'SPITTER_REAL_CAPTURE_PASS'))
logs=[]
for cmd,code,marker in commands:
 print('RUN',' '.join(cmd),flush=True)
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=180,env=dict(os.environ,LIBGL_ALWAYS_SOFTWARE='1'))
 text=result.stdout+result.stderr;print(text,flush=True);logs.append(text)
 if result.returncode!=code or re.search(r'SCRIPT ERROR:|Parse Error:|^ERROR:',text,re.M) or marker and marker not in text:raise SystemExit('SPITTER VERIFICATION FAILED')
(artifact/'engine.log').write_text('\n'.join(logs))
(artifact/'tested_script_hashes.json').write_text(json.dumps({p.name:hashlib.sha256(canon(p).encode()).hexdigest() for p in (GAME/'scripts').glob('*.gd')},indent=2)+'\n')
shutil.copytree(GAME/'captures',artifact/'captures')
(artifact/'README.md').write_text('Spitter real-art evidence. Actual spitter and runner atlases imported. Human and legacy scenery in the game tests were explicit fixtures, never bundled here. Captures display only the actual spitter in its native viewer. No human or firing pixels changed; artwork approval remains pending.\n')
print('SPITTER_ENGINE_PASS: actual spitter and runner atlases; fixture human/scenery; no art approval')
