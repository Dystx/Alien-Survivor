#!/usr/bin/env python3
"""Rebuild current candidate families with mesh-bound surface textures.
Build into a NEW folder first. Installation validates the old family contract,
keeps every camera/pose/socket/animation field, and never processes the player.
"""
from __future__ import annotations
import argparse, copy, hashlib, importlib, json, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import creature_surface

ROOT=Path(__file__).resolve().parents[3]
PACK=ROOT/'assets/pack_v1'
FAMILIES={'runner':('runner_family',84),'spitter':('spitter_family',108),'charger':('charger_family',124),
          'brute':('brute_family',112),'brood_warden':('warden_family',240)}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def preview(family:Path, meta:dict):
    out=family/'reviews';out.mkdir(exist_ok=True)
    # Same current reviews are replaced, no new archive of old artwork.
    for clip,c in meta['clips'].items():
        frames=[];cell=np.array(meta['cell']);W=int(cell[0]*4+40);H=int(cell[1]+56)
        for i in range(c['frames']):
            page=Image.new('RGB',(W,H),(25,30,32));draw=ImageDraw.Draw(page)
            draw.text((10,8),meta['asset_id'].upper()+' / '+clip+' / surface candidate',fill=(216,219,204))
            for j,d in enumerate(meta['directions']):
                p=family/f'frames/{clip}/{d}/{i:03d}.png';im=Image.open(p).convert('RGBA')
                page.paste(im,(j*(int(cell[0])+10)+5,27),im)
                draw.text((j*(int(cell[0])+10)+15,H-17),d.upper(),fill=(167,180,169))
            frames.append(page)
        hold=0 if c['loop'] else round(.6*c['fps'])
        frames += [frames[-1]]*hold
        frames[0].save(out/(clip+'.gif'),save_all=True,append_images=frames[1:],duration=round(1000/c['fps']),loop=0,disposal=2)
        frames[0].save(out/(clip+'_half.webp'),save_all=True,append_images=frames[1:],duration=round(2000/c['fps']),loop=0,lossless=True)


def install(name:str, incoming:Path, report:dict):
    module_name,count=FAMILIES[name]
    family=PACK/'families'/name
    delivery=json.loads((family/'delivery.json').read_text())
    if delivery.get('owner_approval') or delivery.get('status')=='approved':
        raise ValueError('Refusing to change an owner-approved family')
    old=json.loads((family/'review_runtime/animation_index.json').read_text())
    meta=json.loads((incoming/'runtime/animation_index.json').read_text())
    for key in ('cell','pivot','clips','directions'):
        if old[key]!=meta[key]:raise ValueError('Surface pass changed '+key)
    if len(meta['frames'])!=count:raise ValueError('Incomplete family')
    old_map={f['path']:f for f in old['frames']}; differences=[]
    for f in meta['frames']:
        before=old_map[f['path']]
        for key in ('clip','direction','frame','region','sockets','atlas'):
            if before.get(key)!=f.get(key):raise ValueError('Surface pass changed '+key+' '+f['path'])
        with Image.open(family/f['path']) as a,Image.open(incoming/f['path']) as b:
            aa=np.array(a);bb=np.array(b)
            # All actual silhouettes must remain the same: no shrinking, warping,
            # pasted detail off the body, invisible or clipped replacements.
            if not np.array_equal(aa[:,:,3],bb[:,:,3]):
                raise ValueError('Surface pass changed alpha footprint: '+name+'/'+f['path'])
            if np.array_equal(aa,bb):raise ValueError('No surface change: '+f['path'])
            differences.append(float(np.mean(np.abs(aa[:,:,:3].astype(float)-bb[:,:,:3])[aa[:,:,3]>128])))
    # All validation happens before overwriting this family's current frame set.
    for f in meta['frames']:shutil.copyfile(incoming/f['path'],family/f['path'])
    meta['surface_version']=creature_surface.VERSION
    source_dir=PACK/'source'
    for n in ('creature_surface.py','refine_creatures.py'):
        meta['source'][n]=sha(source_dir/n)
    runtime=family/'review_runtime'
    for p in (incoming/'runtime').iterdir():shutil.copyfile(p,runtime/p.name)
    (runtime/'animation_index.json').write_text(json.dumps(meta,indent=2)+'\n')
    source=family/'source'
    manifest=source/'manifest.json'
    manifest.write_text(json.dumps(meta,indent=2)+'\n')
    new_model=incoming/('runner_master.glb' if name=='runner' else 'master.glb')
    shutil.copyfile(new_model,source/'master.glb')
    recipe=incoming/'recipe.json'
    # Geometry recipes stay exactly as before; material authoring is separate.
    if name=='runner':
        shutil.copyfile(recipe,source/'rig.json')
    else:
        shutil.copyfile(recipe,source/'recipe.json')
    for item in delivery.get('sources',[]):item['sha256']=sha(PACK/item['path'])
    for path in [source_dir/'creature_surface.py',source_dir/'refine_creatures.py']:
        rel=path.relative_to(PACK).as_posix()
        delivery['sources']=[i for i in delivery['sources'] if i['path']!=rel]
        delivery['sources'].append({'path':rel,'sha256':sha(path),'provenance':'Original deterministic mesh-bound surface source. No stock image or human artwork input.'})
    delivery['frame_sha256']={str((family/f['path']).relative_to(PACK)):f['sha256'] for f in meta['frames']}
    delivery['surface_version']=creature_surface.VERSION
    delivery['owner_approval']=None;delivery['status']='review'
    (family/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
    rt=ROOT/'assets'/('warden_review' if name=='brood_warden' else name+'_review')
    if rt.is_dir():
        for p in runtime.iterdir():
            if p.is_file():shutil.copyfile(p,rt/p.name)
    lab=ROOT/'art_reviews/runner_lab/assets/runner_review'
    if name=='runner' and lab.is_dir():
        for p in runtime.iterdir():
            if p.is_file():shutil.copyfile(p,lab/p.name)
    preview(family,meta)
    if name=='runner' and (ROOT/'art_reviews').is_dir():
        for p in (ROOT/'art_reviews').glob('runner_*'):
            if p.is_file():p.unlink() # superseded non-master previews only
        for p in (family/'reviews').iterdir():
            if p.is_file():shutil.copyfile(p,ROOT/'art_reviews'/('runner_'+p.name))
    report[name]={'frames':count,'unchanged_alpha_frames':count,'unchanged_sockets':True,
        'mean_foreground_rgb_difference':round(sum(differences)/count,3),'owner_approval':None}
    print('INSTALLED',name,count,'frames; silhouettes and sockets preserved',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--install',action='store_true')
    parser.add_argument('--asset',choices=['all',*FAMILIES],default='all')
    args=parser.parse_args()
    names=list(FAMILIES) if args.asset=='all' else [args.asset]
    args.work.mkdir(exist_ok=True,parents=True)
    report={}
    for name in names:
        out=args.work/name
        if out.exists():raise ValueError('Use a fresh workspace')
        mod=importlib.import_module(FAMILIES[name][0]);mod.build(out,3)
        if args.install:install(name,out,report)
    (args.work/'surface_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
