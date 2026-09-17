#!/usr/bin/env python3
"""Install one validated runner candidate in its existing source family.
Only the runner family and its current runner previews are touched.
"""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[3]
PACK=ROOT/'assets/pack_v1'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 incoming=Path(sys.argv[1]).resolve()
 meta=json.loads((incoming/'manifest.json').read_text())
 if meta.get('asset_id')!='runner' or len(meta.get('frames',[]))!=84 or meta.get('status')!='review':raise ValueError('Unexpected runner candidate')
 family=PACK/'families/runner'
 sources=family/'source';sources.mkdir(parents=True,exist_ok=True)
 frames=family/'frames';frames.mkdir(exist_ok=True)
 expected=set()
 for frame in meta['frames']:
  relative=Path(frame['path'])
  if relative.is_absolute() or '..' in relative.parts or relative.parts[0]!='frames':raise ValueError('Unsafe frame path')
  source=incoming/relative
  if digest(source)!=frame['sha256']:raise ValueError('Changed candidate frame')
  target=family/relative;target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(source,target);expected.add(target.resolve())
 for old in frames.rglob('*.png'):
  if old.resolve() not in expected:raise ValueError('Unexpected old runner frame; reconcile before publishing')
 shutil.copyfile(incoming/'runner_master.glb',sources/'master.glb')
 shutil.copyfile(incoming/'recipe.json',sources/'rig.json')
 (sources/'sockets.json').write_text(json.dumps({f['path']:f['sockets'] for f in meta['frames']},indent=2)+'\n')
 runtime=family/'review_runtime';runtime.mkdir(exist_ok=True)
 for file in (incoming/'runtime').iterdir():shutil.copyfile(file,runtime/file.name)
 review=ROOT/'art_reviews'
 review.mkdir(exist_ok=True)
 # Previous runner-only previews are superseded; the player is never touched.
 for old in review.glob('runner_*'):
  if old.is_file():old.unlink()
 for file in (incoming/'reviews').iterdir():shutil.copyfile(file,review/file.name)
 source_paths=[PACK/'source/runner_family.py',PACK/'source/render_motion.py',sources/'rig.json',sources/'master.glb',sources/'sockets.json']
 delivery={'asset_id':'runner','status':'review','spec_sha256':digest(PACK/'pack.json'),
  'sources':[{'path':p.relative_to(PACK).as_posix(),'sha256':digest(p),'provenance':'Original project runner mesh and articulated pose source. No previous image sheets, stock art or human sprites used. Owner review pending.'} for p in source_paths],
  'frame_sha256':{p.relative_to(PACK).as_posix():digest(p) for p in sorted(expected)},
  'sockets':{},'review':{'style':False,'motion':False,'alpha_edges':False,'pivot_and_scale':False,'direction_coverage':False,'source_rights':False},
  'public_source_permission':False,'owner_approval':None,
  'technical_checks':'84 real RGBA cells checked; same mesh, genuine views, loop closure, articulated strike and floor-settled death. Technical checks are not owner approval.',
  'known_limits':['Procedurally modeled review candidate, not final painted/sculpted production quality.','GLB supplies the editable mesh and movement track; other action poses remain in runner_family.py.','Attack visuals do not change the existing continuous contact-damage simulation.']}
 (family/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
 print('RUNNER_REVIEW_RECORDED: 84 frames, no owner approval, human untouched')
if __name__=='__main__':main()
