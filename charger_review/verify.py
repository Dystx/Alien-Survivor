#!/usr/bin/env python3
"""Real charger/runner/spitter images. Inherited human/scenery are CI fixtures.
Staging never becomes the delivered game. Artifact excludes all fixture pixels.
"""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'charger_review';GAME=ROOT/'game';ENGINE=sys.argv[1]
ART='271ea45aa42e497dc323e808aa8e6d07a906bac4'
parent=ROOT/'spitter_review/verify.py'
exec(compile(parent.read_text().split('\ncommands=[',1)[0],str(parent),'exec'),{'__file__':str(parent),'__name__':'charger_staging'})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(p):return '\n'.join(l.rstrip() for l in p.read_text().splitlines() if l.strip() and not l.lstrip().startswith('#'))+'\n'
protected=[GAME/'scripts'/n for n in ['human_animation.gd','firing_presentation.gd','runner_animation.gd','spitter_animation.gd','simulation.gd','input_router.gd','balance.gd']]
before={str(p):sha(p) for p in protected}
expected={'arena_view.gd':'99287f8833d48c5c811f20a1f50b27b2ec104fc233aaa2a928cf5106cff6bf2c','main.gd':'8227a225b80e2fa2450660ea58fea8ae9f9a5861593739abaeacb0df014c60c1','hud.gd':'e58657a9028bc38c0478850a14f5f50860c8819a9acfd27e27674f4fec7d470e'}
for name,digest in expected.items():
 p=GAME/'scripts'/name;s=canon(p)
 if hashlib.sha256(s.encode()).hexdigest()!=digest:raise ValueError('Unexpected spitter baseline '+name)
 p.write_text(s)
subprocess.run(['patch','-p1','--fuzz=0','--batch','-i',str(HERE/'integration.patch')],cwd=GAME,check=True)
for n in ['charger_animation.gd','charger_review.gd']:shutil.copyfile(HERE/n,GAME/'scripts'/n)
shutil.copyfile(HERE/'charger_tests.gd',GAME/'tests/charger_tests.gd')
(GAME/'scenes/charger_review.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://scripts/charger_review.gd" id="1"]\n[node name="ChargerReview" type="Control"]\nlayout_mode = 3\nanchors_preset = 15\nanchor_right = 1.0\nanchor_bottom = 1.0\nscript = ExtResource("1")\n')
subprocess.run(['git','fetch','--depth=1','origin',ART],cwd=ROOT,check=True)
evidence=ROOT/'charger_evidence';evidence.mkdir()
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',ART,'--','assets/pack_v1/families/charger'],cwd=ROOT,text=True).splitlines()
for rel in paths:
 target=evidence/'charger'/Path(rel).relative_to('assets/pack_v1/families/charger');target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(subprocess.check_output(['git','show',ART+':'+rel],cwd=ROOT))
for name in ['charger_family.py','check_charger.py','render_motion.py']:
 (evidence/'charger/source'/name).write_bytes(subprocess.check_output(['git','show',ART+':assets/pack_v1/source/'+name],cwd=ROOT))
shutil.copytree(evidence/'charger/review_runtime',GAME/'assets/charger_review')
if any(sha(Path(p))!=v for p,v in before.items()):raise ValueError('Protected source changed')
(GAME/'tests/charger_scene.gd').write_text('''extends SceneTree
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
\t\tscene._on_action("charger_test")
\t\trequire(scene.sim.enemies.size() == 2, "Two diagnostic chargers must spawn clear")
\tif ticks == 12:
\t\tvar enemy = scene.sim.enemies[0]
\t\tenemy.warning = 0.0
\t\tscene.sim._arm_attack(enemy,"charge",Vector2.DOWN,0.75)
\tif ticks == 25:
\t\tvar enemy = scene.sim.enemies[0]
\t\trequire(scene.view.chargers.live[enemy.id].clip == "windup", "Charger warning missing")
\t\tscene._on_action("pause")
\t\tfrozen = scene.view.chargers.live[enemy.id].age
\tif ticks == 35:
\t\tvar enemy = scene.sim.enemies[0]
\t\trequire(scene.view.chargers.live[enemy.id].age == frozen,"Pause advanced charger")
\t\tscene._on_action("resume")
\tif ticks == 72:
\t\tvar enemy = scene.sim.enemies[0]
\t\trequire(scene.view.chargers.live[enemy.id].clip == "charge","Charger's existing dash did not select charge art")
\tif ticks == 88:
\t\tvar enemy = scene.sim.enemies[0]
\t\tscene.sim.events.clear()
\t\tscene.sim.damage_enemy(enemy,10000.0)
\t\tscene.view.advance(0.016,false,scene.sim.events)
\tif ticks == 93:
\t\trequire(not scene.view.chargers.deaths.is_empty(),"Charger fall missing")
\tif ticks == 115:
\t\tscene._on_action("charger_review")
\t\tscene = null
\tif ticks == 125:
\t\treview = current_scene
\t\trequire(review.clip == "move","Charger review did not open")
\t\treview.play_clip("windup")
\tif ticks == 145: review.play_clip("charge")
\tif ticks == 165: review.play_clip("recovery")
\tif ticks == 178: review.play_clip("death")
\tif ticks == 215:
\t\trequire(review.slider.value == 4,"Death must hold last frame")
\t\treview._action("Pause")
\t\tfrozen = review.clock
\tif ticks == 230:
\t\trequire(review.clock == frozen,"Review pause failed")
\t\treview._scrub(2.0)
\t\trequire(review.paused and is_equal_approx(review.clock,0.2),"Exact frame scrub failed")
\t\treview._action("0.5x")
\t\treview._action("Background")
\tif ticks == 240: review._action("Return")
\tif ticks == 255:
\t\tscene = current_scene
\t\tscene._on_action("start")
\t\trequire(scene.view.chargers.live.is_empty() and scene.view.chargers.deaths.is_empty(),"Restart retained chargers")
\t\trequire(not scene.view.human.dead,"Restart changed locked human state")
\t\tprint("CHARGER_SCENE_PASS")
\t\tquit(0)
\treturn false
''')
(GAME/'tests/capture_charger.gd').write_text('''extends SceneTree
var scene
var ticks: int = 0
func _initialize() -> void:
\tsetup.call_deferred()
func setup() -> void:
\tscene = load("res://scenes/charger_review.tscn").instantiate()
\troot.add_child(scene)
\tscene.set_process(false)
\tDirAccess.make_dir_recursive_absolute("res://captures")
func _process(_dt: float) -> bool:
\tif scene == null: return false
\tticks += 1
\tif ticks == 3: pose("windup",3)
\tif ticks == 8: capture("windup")
\tif ticks == 10: pose("charge",2)
\tif ticks == 15: capture("charge")
\tif ticks == 17:
\t\tpose("death",4)
\t\tscene.bright = true
\t\tscene.queue_redraw()
\tif ticks == 22: capture("death")
\tif ticks == 26:
\t\tprint("CHARGER_REAL_CAPTURE_PASS")
\t\tquit(0)
\treturn false
func pose(clip: String, frame: int) -> void:
\tscene.play_clip(clip)
\tscene._scrub(frame)
\tscene._process(0.0)
func capture(name: String) -> void:
\tvar im := root.get_texture().get_image()
\tif im == null or im.is_empty() or im.save_png("res://captures/charger_"+name+".png") != OK:
\t\tpush_error("Actual capture missing")
\t\tquit(1)
''')
commands=[([ENGINE,'--headless','--path',str(GAME),'--editor','--import','--quit'],0,None)]
for file,marker in [('run_tests.gd','ALIEN_SURVIVOR_TESTS:'),('human_animation_tests.gd','HUMAN_ANIMATION_TESTS:'),('firing_tests.gd','FIRING_TESTS:'),('runner_tests.gd','RUNNER_ANIMATION_TESTS:'),('spitter_tests.gd','SPITTER_TESTS:'),('charger_tests.gd','CHARGER_TESTS:')]:
 commands.append(([ENGINE,'--headless','--path',str(GAME),'--script','res://tests/'+file],0,marker))
commands.append(([ENGINE,'--headless','--path',str(GAME),'--script','res://tests/run_tests.gd','--','--self-test-failure'],1,'intentional runner self-check'))
for file,marker in [('render_smoke.gd','FINALE_SCENE_FIXTURE_PASS'),('firing_scene.gd','FIRING_SCENE_PASS'),('runner_scene.gd','RUNNER_SCENE_PASS'),('spitter_scene.gd','SPITTER_SCENE_PASS'),('charger_scene.gd','CHARGER_SCENE_PASS')]:
 cmd=[ENGINE,'--path',str(GAME),'--audio-driver','Dummy','--fixed-fps','60','--script','res://tests/'+file,'--','--ci-art-fixtures']
 commands.append(([ENGINE,'--headless']+cmd[1:],0,marker))
 if file=='charger_scene.gd':commands.append((['xvfb-run','-a']+cmd,0,marker))
commands.append((['xvfb-run','-a',ENGINE,'--path',str(GAME),'--audio-driver','Dummy','--fixed-fps','60','--script','res://tests/capture_charger.gd'],0,'CHARGER_REAL_CAPTURE_PASS'))
logs=[]
for cmd,code,marker in commands:
 print('RUN',' '.join(cmd),flush=True)
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=180,env=dict(os.environ,LIBGL_ALWAYS_SOFTWARE='1'))
 text=result.stdout+result.stderr;print(text,flush=True);logs.append(text)
 if result.returncode!=code or re.search(r'SCRIPT ERROR:|Parse Error:|^ERROR:',text,re.M) or marker and marker not in text:raise SystemExit('CHARGER VERIFICATION FAILED')
(evidence/'engine.log').write_text('\n'.join(logs))
(evidence/'tested_script_hashes.json').write_text(json.dumps({p.name:hashlib.sha256(canon(p).encode()).hexdigest() for p in (GAME/'scripts').glob('*.gd')},indent=2)+'\n')
shutil.copytree(GAME/'captures',evidence/'captures')
for n in ['charger_scene.gd','capture_charger.gd']:shutil.copyfile(GAME/'tests'/n,evidence/n)
(evidence/'README.md').write_text('Actual charger/runner/spitter images in Godot. Inherited human/scenery used explicit CI fixtures, excluded from this artifact. Captures show the real charger viewer only. No Mac, exported-build, performance or art approval is implied.\n')
print('CHARGER_ENGINE_PASS: real charger/runner/spitter PNGs; fixture human/scenery; no art approval')
