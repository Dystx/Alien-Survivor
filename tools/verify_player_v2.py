#!/usr/bin/env python3
"""Stage and test the player v2 candidate with actual pixels, then package it.
No runtime game files or original player frames are overwritten.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil,subprocess,sys,zipfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
FAMILY=ROOT/'assets/pack_v1/families/player_rework_v2'
AUTHOR=ROOT/'assets/pack_v1/source'

def run(cmd, marker=None, timeout=180):
 result=subprocess.run([str(x) for x in cmd],cwd=ROOT,capture_output=True,text=True,timeout=timeout,
                       env=dict(os.environ,LIBGL_ALWAYS_SOFTWARE='1'))
 text=result.stdout+result.stderr
 print('RUN '+' '.join(map(str,cmd)),flush=True);print(text,flush=True)
 if result.returncode or re.search(r'SCRIPT ERROR:|Parse Error:|^ERROR:',text,re.M) or (marker and marker not in text):
  raise RuntimeError('Player v2 verification failed')
 return text

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--candidate',type=Path,required=True)
 parser.add_argument('--engine',type=Path,required=True)
 args=parser.parse_args();incoming=args.candidate.resolve();engine=args.engine.resolve()
 if (FAMILY/'frames/ready').exists():
  raise ValueError('Existing published candidate must be reconciled deliberately')
 meta=json.loads((incoming/'manifest.json').read_text())
 if len(meta['frames'])!=128 or meta['asset_id']!='player_rework_v2':
  raise ValueError('Unexpected render scope')
 logs=[run([sys.executable,AUTHOR/'check_player_v2.py',incoming])]
 for d in ['frames','runtime','source']:
  shutil.copytree(incoming/d,FAMILY/d,dirs_exist_ok=True)
 shutil.copy2(incoming/'manifest.json',FAMILY/'manifest.json')
 logs.append(run([engine,'--version'],'4.7.2.stable'))
 logs.append(run([engine,'--headless','--path',FAMILY,'--editor','--import','--quit']))
 logs.append(run([engine,'--headless','--path',FAMILY,'--script','res://check_lab.gd'],
                 'PLAYER_V2_LAB_TESTS: 62 passed, 0 failed'))
 logs.append(run(['xvfb-run','-a',engine,'--path',FAMILY,'--audio-driver','Dummy',
                  '--fixed-fps','60','--script','res://capture_lab.gd'],'PLAYER_V2_CAPTURE_PASS'))
 logs.append(run([sys.executable,'-c',"import runpy; d=runpy.run_path('tests/test_player_rework_v2_source.py'); fs=[v for k,v in d.items() if k.startswith('test_')]; assert len(fs)==4; [f() for f in fs]; print('PLAYER_V2_SOURCE_CHECKS: 4 passed')"],'PLAYER_V2_SOURCE_CHECKS: 4 passed'))
 logs.append(run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_artpack*.py','-v']))
 reviews=FAMILY/'reviews';reviews.mkdir(exist_ok=True)
 for name in ['ready','fire_sockets']:
  shutil.copy2(FAMILY/'captures'/f'{name}.png',reviews/f'{name}_engine.png')
 images=[Image.open(FAMILY/'captures'/f'walk_{i:02d}.png').convert('RGB') for i in range(8)]
 images[0].save(reviews/'walk_half.gif',save_all=True,append_images=images[1:],duration=167,loop=0)
 delivery={'status':'review','owner_approval':None,'frame_count':128,'directions':8,
  'clips':meta['clips'],'source_sha256':meta['source_sha256'],'renderer_sha256':meta['renderer_sha256'],
  'source_revision':os.environ.get('GITHUB_SHA','local'),
  'tests':{'actual_pixel_model_tests':15,'actual_godot_viewer_checks':62,'captured_frames':10},
  'not_established':['Owner identity/visual approval','Final painted finish','Complete gameplay integration',
                     'Hit/death/strafe/reverse/walk-fire coverage','Mac/mobile input, audio or performance'],
  'source_model':'source/master.glb stores named geometry and a walk track; other poses are in the shared authoring Python.',
  'previous_character':'Original approved player and running game are unchanged.'}
 (FAMILY/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
 status_path=FAMILY/'source_status.json'
 status=json.loads(status_path.read_text())
 status.update(status='rendered_review_candidate',delivery_record='delivery.json',frame_count=128)
 status['notes']=['Current execution evidence and approval state are in delivery.json.','This first rendered batch is not integrated into the survival game and is not owner-approved.']
 status_path.write_text(json.dumps(status,indent=2)+'\n')
 evidence=FAMILY/'verification';evidence.mkdir(exist_ok=True)
 (evidence/'engine.log').write_text('\n'.join(logs))
 (evidence/'result.json').write_text(json.dumps(delivery,indent=2)+'\n')
 out=ROOT/'player_v2_artifact';out.mkdir(exist_ok=True)
 archive=out/'Alien_Survivor_Player_Rework_v2.zip'
 exclude={'.godot','__pycache__','.git'}
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(FAMILY.rglob('*')):
   if p.is_file() and not exclude.intersection(p.relative_to(FAMILY).parts) and p.suffix not in {'.uid','.import'}:
    z.write(p,'PlayerReworkV2/'+p.relative_to(FAMILY).as_posix())
  for name in ['player_rework_v2.py','check_player_v2.py','render_motion.py','requirements.txt']:
   z.write(AUTHOR/name,'PlayerReworkV2/authoring/'+name)
  z.writestr('PlayerReworkV2/authoring/.gdignore','')
 print('PLAYER_V2_READY_TO_COMMIT: actual 128 frames and tested reviewer, no art approval')
if __name__=='__main__':main()
