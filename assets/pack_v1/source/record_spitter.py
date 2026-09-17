#!/usr/bin/env python3
"""Record spitter-only draft output. No approval or writes to other families."""
from pathlib import Path
import hashlib,json,shutil,sys
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];PACK=ROOT/'assets/pack_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 incoming=Path(sys.argv[1]);meta=json.loads((incoming/'manifest.json').read_text())
 if meta.get('asset_id')!='spitter' or len(meta.get('frames',[]))!=108 or meta.get('status')!='review':raise ValueError('Unexpected candidate')
 family=PACK/'families/spitter'
 if family.exists():raise ValueError('Existing spitter family; reconcile rather than overwrite')
 family.mkdir(parents=True)
 for f in meta['frames']:
  rel=Path(f['path'])
  if rel.is_absolute() or '..' in rel.parts or rel.parts[0]!='frames':raise ValueError('Unsafe path')
  source=incoming/rel
  if sha(source)!=f['sha256']:raise ValueError('Frame changed')
  target=family/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
 source=family/'source';source.mkdir()
 for name in ['master.glb','recipe.json','manifest.json']:shutil.copyfile(incoming/name,source/name)
 shutil.copytree(incoming/'runtime',family/'review_runtime')
 sources=[PACK/'source'/n for n in ['spitter_family.py','runner_family.py','render_motion.py']]+[source/'master.glb',source/'recipe.json']
 delivery={'asset_id':'spitter','status':'review','spec_sha256':sha(PACK/'pack.json'),
 'sources':[{'path':p.relative_to(PACK).as_posix(),'sha256':sha(p),'provenance':'Original Alien Survivor mesh/pose source. Shared four-limbed lineage. No purchased, ripped or independently generated image frames. Owner rights/style review pending.'} for p in sources],
 'frame_sha256':{(family/f['path']).relative_to(PACK).as_posix():f['sha256'] for f in meta['frames']},
 'sockets':{(family/f['path']).relative_to(PACK).as_posix():f['sockets'] for f in meta['frames']},
 'review':{},'public_source_permission':False,'owner_approval':None,
 'known_limits':['Procedural model finish remains a review candidate, not final artwork approval.','GLB contains the locomotion track; all seven clips remain editable in spitter_family.py.','Simulation owns projectile creation and timing; frame playback never causes damage.']}
 (family/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
 review=family/'reviews';review.mkdir()
 for clip,c in meta['clips'].items():
  pages=[]
  for i in range(c['frames']):
   page=Image.new('RGB',(1024,432),(24,31,33));draw=ImageDraw.Draw(page)
   draw.text((18,12),'SPITTER / '+clip.upper()+' / REVIEW CANDIDATE',fill=(220,223,205))
   for j,d in enumerate(meta['directions']):
    im=Image.open(family/'frames'/clip/d/f'{i:03d}.png').convert('RGBA')
    page.paste(im,(j*256+64,35),im);large=im.resize((256,256),Image.Resampling.NEAREST);page.paste(large,(j*256,170),large)
    draw.text((j*256+110,160),d.upper(),fill=(191,202,181))
   pages.append(page)
  if not c['loop']:pages += [pages[-1]]*max(1,round(c['fps']*.5))
  pages[0].save(review/(clip+'.gif'),save_all=True,append_images=pages[1:],duration=round(1000/c['fps']),loop=0,disposal=2)
  pages[0].save(review/(clip+'_half.webp'),save_all=True,append_images=pages[1:],duration=round(2000/c['fps']),loop=0,lossless=True)
 print('SPITTER_REVIEW_RECORDED: 108 actual frames; human/runner unchanged; no approval')
if __name__=='__main__':main()
