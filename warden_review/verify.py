#!/usr/bin/env python3
"""Real five alien atlases; inherited human/scenery/effect textures are CI fixtures.
Evidence excludes fixture images. Existing simulation and human are protected.
"""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'warden_review';GAME=ROOT/'game';ENGINE=sys.argv[1]
ART='7087d5ed437ad3ddedaeadf5996d3344a7e122a3'
parent=ROOT/'brute_review/verify.py'
exec(compile(parent.read_text().split('\ncommands=[',1)[0],str(parent),'exec'),{'__file__':str(parent),'__name__':'warden_staging'})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(p):return '\n'.join(l.rstrip() for l in p.read_text().splitlines() if l.strip() and not l.lstrip().startswith('#'))+'\n'
protected=[GAME/'scripts'/n for n in ['human_animation.gd','firing_presentation.gd','runner_animation.gd','spitter_animation.gd','charger_animation.gd','brute_animation.gd','simulation.gd','input_router.gd','balance.gd']]
before={str(p):sha(p) for p in protected}
expected={'arena_view.gd':'1a95516a658798cef6911d7210ad8234fb55dd472c1ef2609be1ceae5adb7c14','main.gd':'ecfa18d247fa2593dc32d89a0a0e652fa1f8a643a1edcb2e0e5829bf16a94ecf','hud.gd':'065fee61efa9a5112b4d544d4246113f67b86e847a1214ca33247fcff61eb0a3'}
for name,digest in expected.items():
 p=GAME/'scripts'/name;s=canon(p)
 if hashlib.sha256(s.encode()).hexdigest()!=digest:raise ValueError('Unexpected Brute Pass baseline '+name)
 p.write_text(s)
subprocess.run(['patch','-p1','--fuzz=0','--batch','-i',str(HERE/'integration.patch')],cwd=GAME,check=True)
for n in ['warden_animation.gd','warden_review.gd']:shutil.copyfile(HERE/n,GAME/'scripts'/n)
for n in ['warden_tests.gd','warden_scene.gd','capture_warden.gd']:shutil.copyfile(HERE/n,GAME/'tests'/n)
(GAME/'scenes/warden_review.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://scripts/warden_review.gd" id="1"]\n[node name="WardenReview" type="Control"]\nlayout_mode = 3\nanchors_preset = 15\nanchor_right = 1.0\nanchor_bottom = 1.0\nscript = ExtResource("1")\n')
subprocess.run(['git','fetch','--depth=1','origin',ART],cwd=ROOT,check=True)
evidence=ROOT/'warden_evidence';evidence.mkdir()
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',ART,'--','assets/pack_v1/families/brood_warden'],cwd=ROOT,text=True).splitlines()
for rel in paths:
 target=evidence/'brood_warden'/Path(rel).relative_to('assets/pack_v1/families/brood_warden');target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(subprocess.check_output(['git','show',ART+':'+rel],cwd=ROOT))
for n in ['warden_family.py','check_warden.py','render_motion.py']:
 (evidence/'brood_warden/source'/n).write_bytes(subprocess.check_output(['git','show',ART+':assets/pack_v1/source/'+n],cwd=ROOT))
shutil.copytree(evidence/'brood_warden/review_runtime',GAME/'assets/warden_review')
if any(sha(Path(p))!=v for p,v in before.items()):raise ValueError('Protected source changed')
commands=[([ENGINE,'--headless','--path',str(GAME),'--editor','--import','--quit'],0,None)]
for file,marker in [('run_tests.gd','ALIEN_SURVIVOR_TESTS:'),('human_animation_tests.gd','HUMAN_ANIMATION_TESTS:'),('firing_tests.gd','FIRING_TESTS:'),('runner_tests.gd','RUNNER_ANIMATION_TESTS:'),('spitter_tests.gd','SPITTER_TESTS:'),('charger_tests.gd','CHARGER_TESTS:'),('brute_tests.gd','BRUTE_TESTS:'),('warden_tests.gd','WARDEN_TESTS:')]:
 commands.append(([ENGINE,'--headless','--path',str(GAME),'--script','res://tests/'+file],0,marker))
commands.append(([ENGINE,'--headless','--path',str(GAME),'--script','res://tests/run_tests.gd','--','--self-test-failure'],1,'intentional runner self-check'))
for file,marker in [('render_smoke.gd','FINALE_SCENE_FIXTURE_PASS'),('firing_scene.gd','FIRING_SCENE_PASS'),('runner_scene.gd','RUNNER_SCENE_PASS'),('spitter_scene.gd','SPITTER_SCENE_PASS'),('charger_scene.gd','CHARGER_SCENE_PASS'),('brute_scene.gd','BRUTE_SCENE_PASS'),('warden_scene.gd','WARDEN_SCENE_PASS')]:
 cmd=[ENGINE,'--path',str(GAME),'--audio-driver','Dummy','--fixed-fps','60','--script','res://tests/'+file,'--','--ci-art-fixtures']
 commands.append(([ENGINE,'--headless']+cmd[1:],0,marker))
 if file=='warden_scene.gd':commands.append((['xvfb-run','-a']+cmd,0,marker))
commands.append((['xvfb-run','-a',ENGINE,'--path',str(GAME),'--audio-driver','Dummy','--fixed-fps','60','--script','res://tests/capture_warden.gd'],0,'WARDEN_REAL_CAPTURE_PASS'))
logs=[]
for cmd,code,marker in commands:
 print('RUN',' '.join(cmd),flush=True)
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=180,env=dict(os.environ,LIBGL_ALWAYS_SOFTWARE='1'))
 text=result.stdout+result.stderr;print(text,flush=True);logs.append(text)
 if result.returncode!=code or re.search(r'SCRIPT ERROR:|Parse Error:|^ERROR:',text,re.M) or marker and marker not in text:raise SystemExit('WARDEN VERIFICATION FAILED')
(evidence/'engine.log').write_text('\n'.join(logs))
(evidence/'tested_script_hashes.json').write_text(json.dumps({p.name:hashlib.sha256(canon(p).encode()).hexdigest() for p in (GAME/'scripts').glob('*.gd')},indent=2)+'\n')
shutil.copytree(GAME/'captures',evidence/'captures')
for n in ['warden_scene.gd','capture_warden.gd']:shutil.copyfile(GAME/'tests'/n,evidence/n)
(evidence/'README.md').write_text('Actual five alien atlases imported in Godot. Human/scenery/effect pixels in game tests were CI fixtures, excluded from this artifact. Captures show real Warden art only. No Mac, mobile, performance, exported-build or final-art approval.\n')
print('WARDEN_ENGINE_PASS: real Warden and four regular alien atlases; fixture human/scenery; no art approval')
