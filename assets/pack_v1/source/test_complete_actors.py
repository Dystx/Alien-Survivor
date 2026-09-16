#!/usr/bin/env python3
"""Tests real emitted candidates; does not assert artistic approval."""
from pathlib import Path
import hashlib,json,struct,unittest
import numpy as np
from PIL import Image
import complete_actors as a
PACK=Path(__file__).resolve().parents[1]
class ActorChecks(unittest.TestCase):
 def test_complete_inventory(self):
  counts={}
  for k,clips in a.CLIPS.items():
   counts[k]=sum(n*4 for n,_,_ in clips.values())
   expected={f'{c}/{d}/{i:03d}.png' for c,(n,_,_) in clips.items() for d in a.DIRS for i in range(n)}
   self.assertEqual({p.relative_to(PACK/'families'/k/'frames').as_posix() for p in (PACK/'families'/k/'frames').rglob('*.png')},expected)
  self.assertEqual(sum(counts.values()),892)
 def test_human_not_robot(self):
  m=a.build('player');names={p['name'] for p in m.parts}
  self.assertTrue({'neck','head','nose_tip','short_hair','shirt','vest_front','forearm_1_forearm'}<=names)
  self.assertFalse(any(any(bad in n for bad in ['helmet','visor','respirator','cuirass']) for n in names))
 def test_fixed_canvases_and_safe_alpha(self):
  for k in a.CLIPS:
   cell,pivot=a.SIZES[k]
   for p in (PACK/'families'/k/'frames').rglob('*.png'):
    with Image.open(p) as im:
     self.assertEqual(im.mode,'RGBA');self.assertEqual(list(im.size),cell)
     box=im.getchannel('A').getbbox();self.assertIsNotNone(box)
     self.assertGreaterEqual(min(box[0],box[1],cell[0]-box[2],cell[1]-box[3]),2,str(p))
 def test_real_frames_not_translated_stills(self):
  for k,clips in a.CLIPS.items():
   for c,(n,_,loop) in clips.items():
    for d in a.DIRS:
     hashes=[]
     for p in sorted((PACK/'families'/k/'frames'/c/d).glob('*.png')):
      with Image.open(p) as source:
       im=source.convert('RGBa');box=im.getchannel('a').getbbox();im=im.crop(box)
       hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
     self.assertGreaterEqual(len(set(hashes)),2 if c=='idle' else n,f'{k}/{c}/{d}')
     if loop:self.assertNotEqual(hashes[0],hashes[-1])
 def test_directions_are_different_views(self):
  for k in a.CLIPS:
   c='walk' if k=='player' else 'move'
   h=[hashlib.sha256((PACK/'families'/k/'frames'/c/d/'000.png').read_bytes()).hexdigest() for d in a.DIRS]
   self.assertEqual(len(set(h)),4)
 def test_gait_rig_loop_closes(self):
  for k,clips in a.CLIPS.items():
   r=a.recipe(k)
   for clip,(_,_,loop) in clips.items():
    if not loop:continue
    start=a.pose(r,0,clip);end=a.pose(r,1,clip)
    for name in start:self.assertTrue(np.allclose(start[name],end[name],atol=1e-8),f'{k}/{clip}/{name}')
 def test_sockets_present_and_inside_player(self):
  sockets=json.loads((PACK/'families/player/source/sockets.json').read_text())
  self.assertEqual(len(sockets),224)
  w,h=a.SIZES['player'][0]
  for entry in sockets.values():
   x,y=entry['muzzle'];self.assertTrue(np.isfinite([x,y]).all());self.assertTrue(0<=x<w and 0<=y<h)
 def test_models_are_real_glb_files(self):
  for k in a.CLIPS:
   data=(PACK/'families'/k/'source/master.glb').read_bytes();magic,version,length=struct.unpack_from('<4sII',data)
   self.assertEqual((magic,version,length),(b'glTF',2,len(data)))
   size,kind=struct.unpack_from('<I4s',data,12);self.assertEqual(kind,b'JSON');obj=json.loads(data[20:20+size]);self.assertGreater(len(obj['meshes']),50);self.assertTrue(obj['animations'])
 def test_no_approval_invented(self):
  for k in a.CLIPS:
   p=PACK/'families'/k/'delivery.json'
   self.assertTrue(p.is_file(),str(p))
   d=json.loads(p.read_text());self.assertEqual(d['status'],'review');self.assertIsNone(d['owner_approval'])
if __name__=='__main__':unittest.main(verbosity=2)
