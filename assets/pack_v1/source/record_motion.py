#!/usr/bin/env python3
"""Record actual rendered bytes and make motion previews. Never grant approval."""
from pathlib import Path
import hashlib, json, argparse, shutil
import numpy as np
from PIL import Image,ImageDraw
PACK=Path(__file__).resolve().parents[1]

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def run(pack, spec_hash=None):
    if (pack/'pack.json').is_file():spec_hash=digest(pack/'pack.json')
    if not spec_hash or len(spec_hash)!=64:raise ValueError('Official pack.json or verified --spec-sha256 is required')
    for name,clip,N,cell,pivot in [('player','walk',8,128,(64,110)),('runner','move',6,96,(48,78))]:
        folder=pack/'families'/name;metadata=folder/'delivery.json'
        if metadata.exists() and json.loads(metadata.read_text()).get('status')=='approved':raise ValueError('Never rewrite an approved delivery')
        frames=sorted((folder/'frames').rglob('*.png'))
        expected={folder/'frames'/clip/d/f'{i:03d}.png' for d in ['e','s','w','n'] for i in range(N)}
        if set(frames)!=expected:raise ValueError(f'{name}: incomplete/extra draft clip files')
        for path in frames:
            im=Image.open(path);a=np.array(im)[:,:,3]
            if im.mode!='RGBA' or im.size!=(cell,cell) or a.max()<128:raise ValueError(f'Bad sprite: {path}')
            if max(a[:2].max(),a[-2:].max(),a[:,:2].max(),a[:,-2:].max()):raise ValueError(f'Clipped border: {path}')
        sources=[pack/'source'/f for f in ['render_motion.py','record_motion.py','requirements.txt','README.md']]+[folder/'source'/f for f in ['rig.json','master.glb','sockets.json']]
        doc={'asset_id':name,'status':'review','spec_sha256':spec_hash,'sources':[{'path':p.relative_to(pack).as_posix(),'sha256':digest(p),'provenance':'Original procedural mesh and articulated node-rig source authored in the Alien Survivor project conversation. No stock/ripped assets or earlier image sheets used as source. Approval/rights review pending.'} for p in sources], 'frame_sha256':{p.relative_to(pack).as_posix():digest(p) for p in frames},'sockets':json.loads((folder/'source/sockets.json').read_text()),'review':{k:False for k in ['style','motion','alpha_edges','pivot_and_scale','direction_coverage','source_rights','aim_and_strafe']},'public_source_permission':False,'owner_approval':None,'delivery_scope':f'{N} articulated {clip} frames per direction, four directions; incomplete family, NOT approved for runtime','remaining':['remaining base actions','full family validation and owner review']+(['reverse and strafe/aim coverage'] if name=='player' else []),'technical_notes':['fixed cell/pivot and protected borders checked','genuine model-rotation views; not mirrored','image/rig checks do not constitute aesthetic approval']}
        metadata.write_text(json.dumps(doc,indent=2)+'\n')
        review=pack.parents[1]/'art_reviews';review.mkdir(exist_ok=True)
        ims=[]
        for index in range(N):
            out=Image.new('RGB',(1120,535),(29,34,37));draw=ImageDraw.Draw(out)
            draw.text((16,12),f'{name.upper()} / {clip.upper()} / REVIEW DRAFT - NOT APPROVED',fill=(209,213,200))
            draw.text((16,34),'Native size',fill=(156,169,163))
            draw.text((16,195),'2x nearest-neighbour inspection',fill=(156,169,163))
            for k,d in enumerate(['e','s','w','n']):
                sprite=Image.open(folder/'frames'/clip/d/f'{index:03d}.png')
                cx=140+280*k
                out.paste(sprite,(cx-cell//2,56),sprite)
                large=sprite.resize((cell*2,cell*2),Image.Resampling.NEAREST)
                out.paste(large,(cx-cell,228),large)
                for x,y in [(cx-cell//2+pivot[0],56+pivot[1]),(cx-cell+2*pivot[0],228+2*pivot[1])]:
                    draw.line((x-3,y,x+3,y),fill=(102,157,143));draw.line((x,y-3,x,y+3),fill=(102,157,143))
                draw.text((cx-40,506),d.upper()+'   frame %02d'%index,fill=(175,183,177))
            ims.append(out)
        durations=[round((i+1)*1000/12)-round(i*1000/12) for i in range(N)]
        ims[0].save(review/f'{name}_{clip}.webp',save_all=True,append_images=ims[1:],duration=durations,loop=0,lossless=True)
        # GIF companion for markdown/GitHub; GIF timing is quantized to 10 ms.
        ims[0].save(review/f'{name}_{clip}.gif',save_all=True,append_images=ims[1:],duration=durations,loop=0,disposal=2)
        ims[0].save(review/f'{name}_{clip}_poster.png')
        ims[0].save(review/f'{name}_{clip}_half_speed.webp',save_all=True,append_images=ims[1:],duration=[2*d for d in durations],loop=0,lossless=True)
        print(f'{name}: {len(frames)} frames recorded, review only')
    (pack.parents[1]/'art_reviews/README.md').write_text('# First motion drafts\n\n32 player walk frames + 24 runner move frames; four genuine views. These are incomplete, unapproved families. Inspect native-size motion and half-speed WEBP loops before approving anything. The GIFs are quick previews with 10 ms timing granularity. Source PNG timing is 12 FPS. Ground-pivot cells are not cropped; enlarged previews are presentation only.\n\nThe editable source and GLBs are under families/*/source. All other clips and all other families remain outstanding. Runtime export remains approval-gated.\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pack',type=Path,default=PACK);p.add_argument('--spec-sha256');a=p.parse_args();run(a.pack,a.spec_sha256)
