#!/usr/bin/env python3
"""Tests actual spitter pixels and the same articulated source that renders them."""
import hashlib,json,struct,sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
import spitter_family as a
ROOT=Path(sys.argv[1]);sys.argv=sys.argv[:1]
META=json.loads((ROOT/'manifest.json').read_text())
class Checks(unittest.TestCase):
 def test_scope(self):
  self.assertEqual(len(META['frames']),108);self.assertEqual(len(list((ROOT/'frames').rglob('*.png'))),108)
  self.assertEqual(set(META['clips']),set(a.CLIPS))
 def test_pixels_and_alpha(self):
  for f in META['frames']:
   im=Image.open(ROOT/f['path']);self.assertEqual(im.size,a.CELL);self.assertEqual(im.mode,'RGBA')
   box=im.getchannel('A').getbbox();self.assertIsNotNone(box)
   self.assertTrue(box[0]>=2 and box[1]>=2 and box[2]<=126 and box[3]<=126)
   self.assertEqual(a.sha(ROOT/f['path']),f['sha256'])
 def test_atlas_matches_sources(self):
  atlas=Image.open(ROOT/'runtime/atlas.png')
  self.assertLessEqual(max(atlas.size),2048)
  for f in META['frames']:
   x,y,w,h=f['region'];self.assertEqual(atlas.crop((x,y,x+w,y+h)).tobytes(),Image.open(ROOT/f['path']).tobytes())
 def test_unique_motion_and_loop_ends(self):
  for clip,(n,_,loop) in a.CLIPS.items():
   for direction in a.DIRS:
    hashes=[]
    for i in range(n):
     im=Image.open(ROOT/f'frames/{clip}/{direction}/{i:03d}.png');im=im.crop(im.getchannel('A').getbbox())
     hashes.append(hashlib.sha256(im.convert('RGBa').tobytes()).hexdigest())
    self.assertGreaterEqual(len(set(hashes)),2 if clip=='idle' else n)
    if loop:self.assertNotEqual(hashes[0],hashes[-1])
 def test_genuine_views(self):
  for clip in a.CLIPS:self.assertEqual(len({a.sha(ROOT/f'frames/{clip}/{d}/000.png') for d in a.DIRS}),4)
 def test_source_geometry_is_stable(self):
  model=a.Spitter();vertices=[p['vertices'].copy() for p in model.parts]
  for clip in a.CLIPS:
   model.clip=clip
   for t in [0,.5,1]:
    pose=model.pose(t)
    for p,v in zip(model.parts,vertices):
     self.assertTrue(np.array_equal(p['vertices'],v));self.assertIn(p['bone'],pose)
 def test_loop_pose_closure(self):
  model=a.Spitter()
  for clip in ['idle','move']:
   model.clip=clip;start=model.pose(0);end=model.pose(1)
   for key in start:self.assertTrue(np.allclose(start[key],end[key],atol=1e-8))
 def test_windup_inflates_glands_not_feet(self):
  model=a.Spitter();model.clip='windup';start=model.pose(0);end=model.pose(1)
  self.assertGreater(np.linalg.det(end['sacs'][:3,:3]),np.linalg.det(start['sacs'][:3,:3])*1.20)
  for side in [-1,1]:self.assertTrue(np.allclose(start[f'fore_foot_{side}'],end[f'fore_foot_{side}']))
 def test_windup_to_release_is_continuous(self):
  model=a.Spitter();model.clip='windup';start=model.pose(1);model.clip='attack';end=model.pose(0)
  for key in start:self.assertTrue(np.allclose(start[key],end[key],atol=1e-8),key)
 def test_mouth_socket_bounds_and_motion(self):
  points=[]
  for f in META['frames']:
   p=f['sockets']['mouth'];self.assertTrue(0<=p[0]<128 and 0<=p[1]<128)
   if f['clip']=='windup' and f['direction']=='e':points.append(p)
  self.assertGreater(float(np.linalg.norm(np.array(points[0])-points[-1])),1.)
 def test_floor_settled_death(self):
  model=a.Spitter();model.clip='death'
  for t in np.linspace(0,1,5):
   bones=model.pose(t);minimum=100.
   for p in model.parts:
    m=bones[p['bone']]@p['matrix'];minimum=min(minimum,float((m[:3,:3]@p['vertices'].T+m[:3,3:4])[2].min()))
   self.assertAlmostEqual(minimum,.008,places=5)
 def test_editable_model_and_review_status(self):
  raw=(ROOT/'master.glb').read_bytes();self.assertEqual(raw[:4],b'glTF');self.assertEqual(struct.unpack_from('<I',raw,8)[0],len(raw))
  self.assertEqual(META['status'],'review');self.assertIsNone(META['owner_approval'])
if __name__=='__main__':unittest.main(verbosity=2)
