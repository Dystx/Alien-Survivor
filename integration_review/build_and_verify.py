#!/usr/bin/env python3
"""Review integration, not approved production export.
Builds on the pinned finale candidate. Old scenery uses explicit CI fixtures;
new actor atlases are real imported PNGs, not fixtures. No Mac/device claim.
"""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'integration_review'
BASE='8f0c0e94d0654b4deaa1389ca0e04d91c2ee1c28'
TARGET=Path('/tmp/alien-human-finale')
HASHES={'main.gd':'07a9030346b89635a6d1f4225bb12e0f34f0c08e04d7df5f683e8bb394de8c5f','hud.gd':'dad583b1b513b89eee740416d81018a4a4c248f84a4f5ff3dec7a584ae28ca20','arena_view.gd':'d456f49089b9a296fc42d0f70a978558e049aeae3a024cfce6eb1575ff3fe57c','sprite_factory.gd':'23bdc60fbb93c47c46c54a0c674ff8dc1b838e056e42bf24b3d41dbd46445750'}
def run(cmd,expected=0,marker=None,cwd=None):
 print('RUN',' '.join(map(str,cmd)),flush=True)
 r=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=240,env=dict(os.environ,LIBGL_ALWAYS_SOFTWARE='1'))
 text=r.stdout+r.stderr;print(text,flush=True)
 if r.returncode!=expected or re.search(r'SCRIPT ERROR:|Parse Error:|^ERROR:',text,re.M) or marker and marker not in text:raise RuntimeError('CHECK FAILED')
 return text

def main():
 if TARGET.exists():raise RuntimeError('Refusing to overwrite existing test directory')
 TARGET.mkdir();run(['git','init','.'],cwd=TARGET)
 run(['git','remote','add','origin','https://github.com/Dystx/Alien-Survivor.git'],cwd=TARGET)
 run(['git','fetch','--depth=1','origin',BASE],cwd=TARGET);run(['git','checkout','--detach','FETCH_HEAD'],cwd=TARGET)
 run([sys.executable,str(TARGET/'tools/install_ci_godot.py'),'/tmp/human-review-godot'])
 engine='/tmp/human-review-godot/godot';game=TARGET/'game'
 # Existing setup builds the previously verified finale version before any patch.
 # Execute only its construction section; no previous test outcome is reused.
 source=(TARGET/'verification/run.py').read_text().split('commands=[',1)[0]
 oldargv=sys.argv;sys.argv=[str(TARGET/'verification/run.py'),engine]
 try:exec(compile(source,str(TARGET/'verification/run.py'),'exec'),{'__file__':str(TARGET/'verification/run.py'),'__name__':'__review_setup__'})
 finally:sys.argv=oldargv
 for name,expected in HASHES.items():
  path=game/'scripts'/name
  canonical='\n'.join(l.rstrip() for l in path.read_text().splitlines() if l.strip() and not l.lstrip().startswith('#'))+'\n'
  if hashlib.sha256(canonical.encode()).hexdigest()!=expected:raise RuntimeError(f'Baseline mismatch: {name}')
  path.write_text(canonical)
 run(['git','apply','--directory=game',str(HERE/'integration.patch')],cwd=TARGET)
 for folder in ['scripts','tests']:
  for path in (HERE/folder).glob('*.gd'):shutil.copyfile(path,game/folder/path.name)
 shutil.copytree(HERE/'assets/motion_review',game/'assets/motion_review')
 project=game/'project.godot'
 project.write_text(project.read_text().replace('config/name="Alien Survivor"','config/name="Alien Survivor — Human Animation Review"'))
 smoke=game/'tests/render_smoke.gd'
 smoke.write_text(smoke.read_text().replace('FINALE_SCENE_FIXTURE_PASS','HUMAN_COMBAT_SCENE_PASS'))
 (game/'tests/lab_smoke.gd').write_text('''extends SceneTree
var scene
var ticks: int = 0
var frozen_time: float = 0.0
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
\tif ticks == 4:
\t\tscene._on_action("start")
\tif ticks == 10:
\t\tscene._on_action("animations")
\t\tfrozen_time = scene.sim.elapsed
\tif ticks == 18:
\t\tif scene.sim.elapsed != frozen_time or scene.lab == null:
\t\t\tpush_error("Lab did not pause live combat")
\t\t\tquit(1)
\tif ticks >= 20 and ticks <= 200 and ticks % 3 == 0:
\t\tvar names: Array = scene.view.bank.families.keys()
\t\tvar family: String = names[(ticks / 3) % names.size()]
\t\tscene.lab.family = family
\t\tscene.lab._refresh_clips()
\t\tvar all_clips: Array = scene.view.bank.families[family].clips.keys()
\t\tscene.lab.clip = all_clips[(ticks / 9) % all_clips.size()]
\t\tscene.lab.direction = Vector2.from_angle(float((ticks / 3) % 4) * PI * 0.5)
\t\tscene.lab.clock = 0.0
\t\tscene.lab.bright = ticks % 2 == 0
\tif ticks == 210:
\t\tscene._close_lab()
\t\tscene._on_action("resume")
\t\tscene.sim.health = 0.0
\tif ticks == 230:
\t\tif scene.view.motion.player_clip != "death":
\t\t\tpush_error("Player death animation did not run")
\t\t\tquit(1)
\tif ticks == 285:
\t\tscene._on_action("start")
\tif ticks == 295:
\t\tif scene.view.motion.death_age >= 0.0 or scene.lab != null:
\t\t\tpush_error("Restart retained animation/lab state")
\t\t\tquit(1)
\t\tprint("HUMAN_LAB_SCENE_PASS")
\t\tquit(0)
\treturn false
''')
 logs=[]
 logs.append(run([engine,'--headless','--path',str(game),'--editor','--import','--quit']))
 logs.append(run([engine,'--headless','--path',str(game),'--script','res://tests/run_tests.gd'],marker='ALIEN_SURVIVOR_TESTS: 74 passed, 0 failed'))
 logs.append(run([engine,'--headless','--path',str(game),'--script','res://tests/motion_integration.gd'],marker='HUMAN_MOTION_TESTS: 18 passed, 0 failed'))
 logs.append(run([engine,'--headless','--path',str(game),'--script','res://tests/run_tests.gd','--','--self-test-failure'],expected=1,marker='intentional runner self-check'))
 for scene,marker in [('render_smoke.gd','HUMAN_COMBAT_SCENE_PASS'),('lab_smoke.gd','HUMAN_LAB_SCENE_PASS')]:
  logs.append(run([engine,'--headless','--path',str(game),'--fixed-fps','60','--script','res://tests/'+scene,'--','--ci-art-fixtures'],marker=marker))
  logs.append(run(['xvfb-run','-a',engine,'--path',str(game),'--audio-driver','Dummy','--fixed-fps','60','--script','res://tests/'+scene,'--','--ci-art-fixtures'],marker=marker))
 result=HERE/'verification';result.mkdir(exist_ok=True)
 (result/'engine.log').write_text('\n'.join(logs))
 hashes={p.name:hashlib.sha256('\n'.join(l.rstrip() for l in p.read_text().splitlines() if l.strip() and not l.lstrip().startswith('#')).encode()).hexdigest() for p in (game/'scripts').glob('*.gd')}
 (result/'tested_script_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
 (result/'README.md').write_text('# Human animation integration verification\n\nReal Godot 4.7.2 import and 74 gameplay + 18 motion checks passed. Negative control passed. Combat and lab smoke checks passed in headless and software OpenGL modes. New actor PNG atlases were real imported files; old environment/FX were explicit solid fixtures in CI. This does not establish the appearance of the complete delivered scenery, final art quality, audible sound, Mac/mobile, controller, exports or human-tested balance.\n')
 print('HUMAN_ANIMATION_ENGINE_PASS: REAL ACTOR PNGS; SCENERY FIXTURES; NO ART APPROVAL')
if __name__=='__main__':main()
