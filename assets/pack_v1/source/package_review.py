#!/usr/bin/env python3
"""Pack generated actor CANDIDATES for a labelled integration review.
Not the approved-only production exporter. No approval records are manufactured.
"""
from pathlib import Path
import argparse, hashlib, json
from PIL import Image
from complete_actors import CLIPS,DIRS,SIZES

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def package(pack,out):
 out.mkdir(parents=True,exist_ok=True);index={'status':'review_only','release_approved':False,'families':{}}
 for kind,clips in CLIPS.items():
  folder=pack/'families'/kind
  cell,pivot=SIZES[kind];sockets=json.loads((folder/'source/sockets.json').read_text())
  target=out/kind;target.mkdir(parents=True,exist_ok=True)
  pages=[];page=Image.new('RGBA',(2048,2048));x=y=2;row=0;usedw=usedh=0
  metadata={'cell':cell,'pivot':pivot,'clips':{},'pages':[],'candidate':True}
  def flush():
   nonlocal page,x,y,row,usedw,usedh
   name=f'atlas_{len(pages):02d}.png';page.crop((0,0,max(4,usedw+2),max(4,usedh+2))).save(target/name)
   pages.append(name);metadata['pages'].append({'file':name,'sha256':sha(target/name)})
   page=Image.new('RGBA',(2048,2048));x=y=2;row=0;usedw=usedh=0
  for clip,(n,fps,loop) in clips.items():
   meta={'fps':fps,'loop':loop,'directions':{}}
   for d in DIRS:
    frames=[]
    for i in range(n):
     p=folder/'frames'/clip/d/f'{i:03d}.png'
     if not p.is_file():raise RuntimeError(f'Missing frame {p}')
     im=Image.open(p).convert('RGBA')
     if list(im.size)!=cell:raise RuntimeError(f'Cell mismatch {p}: {im.size} vs {cell}')
     box=im.getchannel('A').getbbox()
     if not box:raise RuntimeError(f'Empty {p}')
     if min(box[0],box[1],cell[0]-box[2],cell[1]-box[3])<2:raise RuntimeError(f'Border clipping {p}: {box}')
     trim=im.crop(box);w,h=trim.size
     if x+w+2>2048:x=2;y+=row+4;row=0
     if y+h+2>2048:flush()
     page.paste(trim,(x,y));row=max(row,h);usedw=max(usedw,x+w);usedh=max(usedh,y+h)
     sc=sockets.get(p.relative_to(pack).as_posix(),{})
     frames.append({'page':len(pages),'rect':[x,y,w,h],'offset':[box[0]-pivot[0],box[1]-pivot[1]],'muzzle':[sc.get('muzzle',[pivot[0],pivot[1]])[0]-pivot[0],sc.get('muzzle',[pivot[0],pivot[1]])[1]-pivot[1]],'source_sha256':sha(p)})
     x+=w+4
    meta['directions'][d]=frames
   metadata['clips'][clip]=meta
  flush();(target/'animations.json').write_text(json.dumps(metadata,separators=(',',':'))+'\n')
  index['families'][kind]={'manifest':f'{kind}/animations.json','sha256':sha(target/'animations.json'),'frames':sum(n*4 for n,_,_ in clips.values())}
  print('PACKED',kind,index['families'][kind]['frames'],'candidate frames')
 (out/'index.json').write_text(json.dumps(index,indent=2)+'\n')
 return index
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--pack',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--out',type=Path,required=True);a=p.parse_args();package(a.pack,a.out)
