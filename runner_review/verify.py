#!/usr/bin/env python3
"""Test the runner with real committed runner art and explicit legacy-art fixtures.
This stages an isolated checkout; it does not install placeholders into a release.
"""
from pathlib import Path
import hashlib,os,re,shutil,subprocess,sys
root=Path(__file__).resolve().parents[1]
game=root/'game';here=root/'runner_review';engine=sys.argv[1]
ART='b6203e225bb34b1a30efc5d0a13d85e1e4803506'
previous=root/'firing_review/verify.py'
staging=previous.read_text().split('commands=[',1)[0]
exec(compile(staging,str(previous),'exec'),{'__file__':str(previous),'__name__':'runner_staging'})
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(s):return '\n'.join(l.rstrip() for l in s.splitlines() if l.strip() and not l.lstrip().startswith('#'))
protected=[game/'scripts'/n for n in ['human_animation.gd','firing_presentation.gd','simulation.gd','input_router.gd','balance.gd']]+[game/'assets/human_survivor/human_atlas.png']
before={str(p):digest(p) for p in protected}
expected={'main.gd':'2f507b1d07b376e066b134930ed0d1e4a59f5fb556fc9ed4be3923ae63dfdd1c','arena_view.gd':'5455d685c053bfa617cc7fa654264768af34d94bc92559d1285edb82119c0f63','hud.gd':'5103b812aee7e043b341af7fe55432c0ff48375533756bdc4b684282f84f3762'}
for name,value in expected.items():
 p=game/'scripts'/name;s=canonical(p.read_text())
 if hashlib.sha256(s.encode()).hexdigest()!=value:raise ValueError('Firing baseline changed: '+name)
 p.write_text(s+'\n')
subprocess.run(['patch','-p1','--batch','--fuzz=0','-i',str(here/'integration.patch')],cwd=game,check=True)
for name in ['runner_animation.gd','runner_review.gd']:shutil.copyfile(here/name,game/'scripts'/name)
shutil.copyfile(here/'runner_tests.gd',game/'tests/runner_tests.gd')
subprocess.run(['git','fetch','--no-tags','--depth=1','origin',ART],cwd=root,check=True)
assets=game/'assets/runner_review';assets.mkdir(parents=True,exist_ok=True)
for filename in ['atlas.png','sprite_frames.tres','animation_index.json']:
 raw=subprocess.check_output(['git','show',ART+':assets/pack_v1/families/runner/review_runtime/'+filename],cwd=root)
 (assets/filename).write_bytes(raw)
print('REAL_RUNNER_ATLAS_SHA256',digest(assets/'atlas.png'),flush=True)
print('Runner images are real. Locked-human/scenery images in CI remain explicit synthetic fixtures.',flush=True)
(game/'scenes/runner_review.tscn').write_text('''[gd_scene load_steps=2 format=3]
[ext_resource type="Script" path="res://scripts/runner_review.gd" id="1"]
[node name="RunnerReview" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
script = ExtResource("1")
''')
if any(digest(Path(p))!=sha for p,sha in before.items()):raise ValueError('Protected human/firing/simulation changed')
(game/'tests/runner_scene.gd').write_text('''extends SceneTree
var scene
var review
var ticks: int = 0
var frozen: float = 0.0
func _initialize() -> void:
\t_setup.call_deferred()
func _setup() -> void:
\tscene = load("res://scenes/main.tscn").instantiate()
\troot.add_child(scene)
\tcurrent_scene = scene
\tscene.sound.muted = true
func require(ok: bool, message: String) -> void:
\tif not ok:
\t\tpush_error(message)
\t\tquit(1)
func _process(_dt: float) -> bool:
\tticks += 1
\tif ticks == 5:
\t\tscene._on_action("start")
\t\tscene.sim.spawning_enabled = false
\t\tfor i in range(4):
\t\t\tvar enemy = scene.sim.add_enemy(scene.sim.player + Vector2(90+i*18, 30))
\t\t\tenemy.health = 300.0
\tif ticks == 35:
\t\trequire(not scene.view.runners.live.is_empty(), "Live runner states missing")
\t\tvar enemy = scene.sim.enemies[0]
\t\tscene.sim.damage_enemy(enemy, 10000.0)
\t\tscene.view.advance(0.016, false, scene.sim.events)
\tif ticks == 45:
\t\trequire(not scene.view.runners.deaths.is_empty(), "Runner death did not enter the view")
\t\tscene._on_action("pause")
\t\tfrozen = float(scene.view.runners.deaths[0].age)
\tif ticks == 60:
\t\trequire(float(scene.view.runners.deaths[0].age) == frozen, "Pause advanced runner death")
\t\tscene._on_action("resume")
\tif ticks == 85:
\t\tscene._on_action("runner_review")
\t\tscene = null
\tif ticks == 95:
\t\treview = current_scene
\t\trequire(review != null and review.clip == "move", "Runner review failed to open")
\t\treview._action("Idle")
\tif ticks == 110: review._action("Attack")
\tif ticks == 135: review._action("Hit")
\tif ticks == 145: review._action("Death")
\tif ticks == 185:
\t\treview._action("Pause")
\t\tfrozen = review.clock
\tif ticks == 195:
\t\trequire(review.clock == frozen, "Runner review pause failed")
\t\treview._action("Pause")
\t\treview._action("0.5x")
\t\treview._action("Background")
\tif ticks == 210:
\t\treview._action("Return")
\t\treview = null
\tif ticks == 220:
\t\tscene = current_scene
\t\tscene._on_action("start")
\t\trequire(scene.view.runners.live.is_empty() and scene.view.runners.deaths.is_empty(), "Restart retained runner states")
\t\tprint("RUNNER_SCENE_PASS")
\t\tquit(0)
\treturn false
''')
for name in ['main.gd','arena_view.gd','hud.gd','runner_animation.gd','runner_review.gd']:
 print('RUNNER_CANONICAL_SHA256',name,hashlib.sha256(canonical((game/'scripts'/name).read_text()).encode()).hexdigest(),flush=True)
commands=[([engine,'--headless','--path',str(game),'--editor','--import','--quit'],0,None)]
for file,marker in [('run_tests.gd','ALIEN_SURVIVOR_TESTS:'),('human_animation_tests.gd','HUMAN_ANIMATION_TESTS:'),('firing_tests.gd','FIRING_TESTS:'),('runner_tests.gd','RUNNER_ANIMATION_TESTS:')]:
 commands.append(([engine,'--headless','--path',str(game),'--script','res://tests/'+file],0,marker))
commands.append(([engine,'--headless','--path',str(game),'--script','res://tests/run_tests.gd','--','--self-test-failure'],1,'intentional runner self-check'))
for scene,marker in [('render_smoke.gd','FINALE_SCENE_FIXTURE_PASS'),('firing_scene.gd','FIRING_SCENE_PASS'),('runner_scene.gd','RUNNER_SCENE_PASS')]:
 cmd=[engine,'--path',str(game),'--audio-driver','Dummy','--fixed-fps','60','--script','res://tests/'+scene,'--','--ci-art-fixtures']
 commands.append(([engine,'--headless']+cmd[1:],0,marker))
 if scene=='runner_scene.gd':commands.append((['xvfb-run','-a']+cmd,0,marker))
for cmd,code,marker in commands:
 print('RUN',' '.join(cmd),flush=True)
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=180,env=dict(os.environ,LIBGL_ALWAYS_SOFTWARE='1'))
 text=result.stdout+result.stderr;print(text,flush=True)
 if result.returncode!=code or re.search(r'SCRIPT ERROR:|Parse Error:|^ERROR:',text,re.M) or (marker and marker not in text):raise SystemExit('RUNNER VERIFICATION FAILED')
print('RUNNER_ENGINE_PASS: real runner PNGs, fixture human/scenery. No owner approval, Mac/mobile, export or balance claim.')
