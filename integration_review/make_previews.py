#!/usr/bin/env python3
from pathlib import Path
import json,math,sys
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets/pack_v1/source'))
from complete_actors import CLIPS,SIZES,DIRS

def preview(pack,out):
 out.mkdir(parents=True,exist_ok=True)
 for k,clips in CLIPS.items():
  clip='walk' if k=='player' else 'move';n,fps,_=clips[clip];cell,pivot=SIZES[k]
  scale=2 if k!='brood_warden' else 1
  slotw=cell[0]*scale;sloth=cell[1]*scale
  frames=[]
  for i in range(n):
   im=Image.new('RGB',(slotw*4,sloth+76),(29,33,34));d=ImageDraw.Draw(im)
   d.text((16,12),f'{k.upper()} / {clip.upper()} / REVIEW CANDIDATE',(202,209,197))
   for j,di in enumerate(DIRS):
    raw=Image.open(pack/'families'/k/'frames'/clip/di/f'{i:03d}.png').convert('RGBA')
    raw=raw.resize((slotw,sloth),Image.Resampling.NEAREST)
    im.paste(raw,(j*slotw,40),raw);d.text((j*slotw+16,sloth+51),di.upper(),(172,188,179))
   frames.append(im)
  frames[0].save(out/f'{k}_{clip}.gif',save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,disposal=2)
  frames[0].save(out/f'{k}_{clip}.png')
 (out/'README.md').write_text('# Actual actor motion candidates\n\nThese GIFs play rendered frame files from the same masters used by the integration review. They are not approval records. The human has visible skin and clothing rather than a robot shell; surface finish and anatomy remain simpler than the illustrated concept. All actions can be inspected in the native Animation Lab.\n')
if __name__=='__main__':preview(ROOT/'assets/pack_v1',ROOT/'integration_review/reviews')
