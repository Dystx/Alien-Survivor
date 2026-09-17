#!/usr/bin/env python3
"""Real brute/charger/spitter/runner images; inherited human/scenery are CI fixtures.
No fixture artwork is exported into the evidence or the delivered project.
"""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'brute_review';GAME=ROOT/'game';ENGINE=sys.argv[1]
ART='a9f2c3e851599ed6b4a6b5f78109c908d9636fdc'
parent=ROOT/'charger_review/verify.py'
exec(compile(parent.read_text().split('\ncommands=[',1)[0],str(parent),'exec'),{'__file__':str(parent),'__name__':'brute_staging'})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(p):return '\n'.join(l.rstrip() for l in p.read_text().splitlines() if l.strip() and not l.lstrip().startswith('#'))+'\n'
protected=[GAME/'scripts'/n for n in ['human_animation.gd','firing_presentation.gd','runner_animation.gd','spitter_animation.gd','charger_animation.gd','simulation.gd','input_router.gd','balance.gd']]
before={str(p):sha(p) for p in protected}
expected={'main.gd':'3dc141d88fc8a494e22a68bd024b74e22e39b7e4e9c7a929f2c414a995c332e1','hud.gd':'7bf4968e1019a2c274f41365b1c64ae975d55116a45bd3879504f662b1ab99d0','arena_view.gd':'2552725382ad3700d306f0d8acb5f792b7ede857b4612105a6339dc38b4b37b2'}
for name,digest in expected.items():
 p=GAME/'scripts'/name;s=canon(p)
 if hashlib.sha256(s.encode()).hexdigest()!=digest:raise ValueError('Unexpected charger baseline '+name)
 p.write_text(s)
subprocess.run(['patch','-p1','--fuzz=0','--batch','-i',str(HERE/'integration.patch')],cwd=GAME,check=True)
for n in ['brute_animation.gd','brute_review.gd']:shutil.copyfile(HERE/n,GAME/'scripts'/n)
shutil.copyfile(HERE/'brute_tests.gd',GAME/'tests/brute_tests.gd')
(GAME/'scenes/brute_review.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://scripts/brute_review.gd" id="1"]\n[node name="BruteReview" type="Control"]\nlayout_mode = 3\nanchors_preset = 15\nanchor_right = 1.0\nanchor_bottom = 1.0\nscript = ExtResource("1")\n')
subprocess.run(['git','fetch','--depth=1','origin',ART],cwd=ROOT,check=True)
evidence=ROOT/'brute_evidence';evidence.mkdir()
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',ART,'--','assets/pack_v1/families/brute'],cwd=ROOT,text=True).splitlines()
for rel in paths:
 target=evidence/'brute'/Path(rel).relative_to('assets/pack_v1/families/brute');target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(subprocess.check_output(['git','show',ART+':'+rel],cwd=ROOT))
for name in ['brute_family.py','check_brute.py','render_motion.py']:
 (evidence/'brute/source'/name).write_bytes(subprocess.check_output(['git','show',ART+':assets/pack_v1/source/'+name],cwd=ROOT))
shutil.copytree(evidence/'brute/review_runtime',GAME/'assets/brute_review')
if any(sha(Path(p))!=v for p,v in before.items()):raise ValueError('Protected source changed')
(GAME/'tests/brute_scene.gd').write_text('''extends SceneTree
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
\t\tscene._on_action("brute_test")
\t\trequire(scene.sim.enemies.size() == 2, "Two clear diagnostic brutes must spawn")
\tif ticks == 12:
\t\tvar enemy = scene.sim.enemies[0]
\t\tenemy.warning = 0.0
\t\tenemy.position = scene.sim.player + Vector2(20,0)
\tif ticks == 20:
\t\trequire(not scene.view.brutes.live.is_empty(), "Live brute presentation missing")
\t\tscene._on_action("pause")
\t\tvar enemy = scene.sim.enemies[0]
\t\tfrozen = scene.view.brutes.live[enemy.id].idle_age
\tif ticks == 32:
\t\tvar enemy = scene.sim.enemies[0]
\t\trequire(scene.view.brutes.live[enemy.id].idle_age == frozen, "Pause advanced brute")
\t\tscene._on_action("resume")
\tif ticks == 65:
\t\tvar enemy = scene.sim.enemies[0]
\t\tscene.sim.events.clear()
\t\tscene.sim.damage_enemy(enemy,10000.0)
\t\tscene.view.advance(0.016,false,scene.sim.events)
\tif ticks == 70:
\t\trequire(not scene.view.brutes.deaths.is_empty(), "Brute fall missing")
\tif ticks == 125:
\t\trequire(float(scene.view.brutes.deaths[0].age) == 0.75, "Brute corpse must hold final pose")
\t\tscene._on_action("brute_review")
\t\tscene = null
\tif ticks == 135:
\t\treview = current_scene
\t\trequire(review.clip == "move", "Brute review did not open")
\t\treview.play_clip("windup")
\tif ticks == 155: review.play_clip("attack")
\tif ticks == 175: review.play_clip("recovery")
\tif ticks == 190: review.play_clip("death")
\tif ticks == 245:
\t\trequire(review.slider.value == 5, "Six-frame death must hold final pose")
\t\treview._action("Pause")
\t\tfrozen = review.clock
\tif ticks == 255:
\t\trequire(review.clock == frozen, "Viewer pause failed")
\t\treview._scrub(2.0)
\t\trequire(review.paused and is_equal_approx(review.clock,0.25), "Frame scrubbing failed")
\t\treview._action("0.5x")
\t\treview._action("Background")
\tif ticks == 265: review._action("Return")
\tif ticks == 280:
\t\tscene = current_scene
\t\tscene._on_action("start")
\t\trequire(scene.view.brutes.live.is_empty() and scene.view.brutes.deaths.is_empty(), "Restart retained brute states")
\t\trequire(not scene.view.human.dead, "Restart retained dead human")
\t\tprint("BRUTE_SCENE_PASS")
\t\tquit(0)
\treturn false
''')
(GAME/'tests/capture_brute.gd').write_text('''extends SceneTree
var scene
var ticks: int = 0
func _initialize() -> void:
\tsetup.call_deferred()
func setup() -> void:
\tscene = load("res://scenes/brute_review.tscn").instantiate()
\troot.add_child(scene)
\tscene.set_process(false)
\tDirAccess.make_dir_recursive_absolute("res://captures")
func _process(_dt: float) -> bool:
\tif scene == null: return false
\tticks += 1
\tif ticks == 3: pose("move",2)
\tif ticks == 8: capture("move")
\tif ticks == 10: pose("attack",1)
\tif ticks == 15: capture("attack")
\tif ticks == 17:
\t\tpose("death",5)
\t\tscene.bright = true
\t\tscene.queue_redraw()
\tif ticks == 22: capture("death")
\tif ticks == 26:
\t\tprint("BRUTE_REAL_CAPTURE_PASS")
\t\tquit(0)
\treturn false
func pose(clip: String, frame: int) -> void:
\tscene.play_clip(clip)
\tscene._scrub(frame)
\tscene._process(0.0)
func capture(name: String) -> void:
\tvar im := root.get_texture().get_image()
\tif im == null or im.is_empty() or im.save_png("res://captures/brute_"+name+".png") != OK:
\t\tpush_error("Actual capture missing")
\t\tquit(1)
''')
commands=[([ENGINE,'--headless','--path',str(GAME),'--editor','--import','--quit'],0,None)]
for file,marker in [('run_tests.gd','ALIEN_SURVIVOR_TESTS:'),('human_animation_tests.gd','HUMAN_ANIMATION_TESTS:'),('firing_tests.gd','FIRING_TESTS:'),('runner_tests.gd','RUNNER_ANIMATION_TESTS:'),('spitter_tests.gd','SPITTER_TESTS:'),('charger_tests.gd','CHARGER_TESTS:'),('brute_tests.gd','BRUTE_TESTS:')]:
 commands.append(([ENGINE,'--headless','--path',str(GAME),'--script','res://tests/'+file],0,marker))
commands.append(([ENGINE,'--headless','--path',str(GAME),'--script','res://tests/run_tests.gd','--','--self-test-failure'],1,'intentional runner self-check'))
for file,marker in [('render_smoke.gd','FINALE_SCENE_FIXTURE_PASS'),('firing_scene.gd','FIRING_SCENE_PASS'),('runner_scene.gd','RUNNER_SCENE_PASS'),('spitter_scene.gd','SPITTER_SCENE_PASS'),('charger_scene.gd','CHARGER_SCENE_PASS'),('brute_scene.gd','BRUTE_SCENE_PASS')]:
 cmd=[ENGINE,'--path',str(GAME),'--audio-driver','Dummy','--fixed-fps','60','--script','res://tests/'+file,'--','--ci-art-fixtures']
 commands.append(([ENGINE,'--headless']+cmd[1:],0,marker))
 if file=='brute_scene.gd':commands.append((['xvfb-run','-a']+cmd,0,marker))
commands.append((['xvfb-run','-a',ENGINE,'--path',str(GAME),'--audio-driver','Dummy','--fixed-fps','60','--script','res://tests/capture_brute.gd'],0,'BRUTE_REAL_CAPTURE_PASS'))
logs=[]
for cmd,code,marker in commands:
 print('RUN',' '.join(cmd),flush=True)
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=180,env=dict(os.environ,LIBGL_ALWAYS_SOFTWARE='1'))
 text=result.stdout+result.stderr;print(text,flush=True);logs.append(text)
 if result.returncode!=code or re.search(r'SCRIPT ERROR:|Parse Error:|^ERROR:',text,re.M) or marker and marker not in text:raise SystemExit('BRUTE VERIFICATION FAILED')
(evidence/'engine.log').write_text('\n'.join(logs))
(evidence/'tested_script_hashes.json').write_text(json.dumps({p.name:hashlib.sha256(canon(p).encode()).hexdigest() for p in (GAME/'scripts').glob('*.gd')},indent=2)+'\n')
shutil.copytree(GAME/'captures',evidence/'captures')
for n in ['brute_scene.gd','capture_brute.gd']:shutil.copyfile(GAME/'tests'/n,evidence/n)
(evidence/'README.md').write_text('Actual brute/charger/runner/spitter images imported. Human/scenery in automated game checks are explicit fixtures, excluded from this artifact. Captures display only real brute pixels. Contact damage and armour are unchanged; the windup clip is review-only. No art, Mac, export, sound, controller or performance approval.\n')
print('BRUTE_ENGINE_PASS: actual four alien atlases; fixture human/scenery; no art approval')
