#!/usr/bin/env python3
"""Checks actual brute pixels, mesh and pose invariants; not art approval."""
import hashlib,json,struct,sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
import brute_family as a
ROOT=Path(sys.argv[1]);sys.argv=sys.argv[:1]
META=json.loads((ROOT/'manifest.json').read_text())
class Checks(unittest.TestCase):
 def test_scope(self):
  self.assertEqual(len(META['frames']),112);self.assertEqual(len(list((ROOT/'frames').rglob('*.png'))),112)
  self.assertEqual(set(META['clips']),set(a.CLIPS))
 def test_frame_hashes_alpha_and_bounds(self):
  for f in META['frames']:
   im=Image.open(ROOT/f['path']);self.assertEqual(im.size,a.CELL);self.assertEqual(im.mode,'RGBA')
   box=im.getchannel('A').getbbox();self.assertIsNotNone(box);self.assertTrue(min(box[:2])>=2 and max(box[2:])<=158)
   self.assertEqual(a.sha(ROOT/f['path']),f['sha256'])
 def test_atlas_pixel_equality(self):
  atlas=Image.open(ROOT/'runtime/atlas.png');self.assertLessEqual(max(atlas.size),2048)
  for f in META['frames']:
   x,y,w,h=f['region'];self.assertEqual(atlas.crop((x,y,x+w,y+h)).tobytes(),Image.open(ROOT/f['path']).tobytes())
 def test_motion_is_not_translated_stills(self):
  for clip,(n,_,loop) in a.CLIPS.items():
   for d in a.DIRS:
    hashes=[]
    for i in range(n):
     im=Image.open(ROOT/f'frames/{clip}/{d}/{i:03d}.png');im=im.crop(im.getchannel('A').getbbox())
     hashes.append(hashlib.sha256(im.convert('RGBa').tobytes()).hexdigest())
    self.assertGreaterEqual(len(set(hashes)),2 if clip=='idle' else n)
    if loop:self.assertNotEqual(hashes[0],hashes[-1])
 def test_four_real_views(self):
  for clip in a.CLIPS:self.assertEqual(len({a.sha(ROOT/f'frames/{clip}/{d}/000.png') for d in a.DIRS}),4)
 def test_static_geometry(self):
  m=a.Brute();vertices=[p['vertices'].copy() for p in m.parts]
  for clip in a.CLIPS:
   m.clip=clip
   for t in np.linspace(0,1,5):
    bones=m.pose(t)
    for p,v in zip(m.parts,vertices):self.assertTrue(np.array_equal(p['vertices'],v));self.assertIn(p['bone'],bones)
 def test_loop_pose_closure(self):
  m=a.Brute()
  for clip in ['idle','move']:
   m.clip=clip;start=m.pose(0);end=m.pose(1)
   for k in start:self.assertTrue(np.allclose(start[k],end[k],atol=1e-8),k)
 def test_planted_windup_feet(self):
  m=a.Brute();m.clip='windup';start=m.pose(0);end=m.pose(1)
  for side in [-1,1]:
   for kind in ['hind','fore']:self.assertTrue(np.allclose(start[f'{kind}_foot_{side}'],end[f'{kind}_foot_{side}']))
 def test_transition_continuity(self):
  m=a.Brute()
  for c1,c2 in [('windup','attack'),('attack','recovery'),('recovery','idle')]:
   m.clip=c1;x=m.pose(1);m.clip=c2;y=m.pose(0)
   for key in x:self.assertTrue(np.allclose(x[key],y[key],atol=1e-8),c1+' / '+key)
 def test_fixed_limb_lengths(self):
  m=a.Brute()
  for clip in a.CLIPS:
   m.clip=clip
   for t in np.linspace(0,1,9):
    bones=m.pose(t)
    for kind,length in [('hind',.28),('fore',.32)]:
     for side in [-1,1]:
      for segment in ['upper','lower']:self.assertAlmostEqual(np.linalg.norm(bones[f'{kind}_{segment}_{side}'][:3,2]),length,places=6)
 def test_grounded_death(self):
  m=a.Brute();m.clip='death'
  for t in np.linspace(0,1,6):
   bones=m.pose(t);minimum=100.
   for p in m.parts:
    mat=bones[p['bone']]@p['matrix'];minimum=min(minimum,float((mat[:3,:3]@p['vertices'].T+mat[:3,3:4])[2].min()))
   self.assertAlmostEqual(minimum,.008,places=5)
 def test_specific_body_and_socket(self):
  m=a.Brute();names={p['name'] for p in m.parts}
  self.assertIn('wide_thorax',names);self.assertEqual(len([n for n in names if n.startswith('carapace_') and not n.startswith('carapace_edge')]),10)
  self.assertFalse(any('gland' in n or 'wedge' in n for n in names))
  for f in META['frames']:
   x,y=f['sockets']['impact'];self.assertTrue(0<=x<160 and 0<=y<160)
 def test_editable_model_and_no_approval(self):
  raw=(ROOT/'master.glb').read_bytes();self.assertEqual(raw[:4],b'glTF');self.assertEqual(struct.unpack_from('<I',raw,8)[0],len(raw))
  self.assertEqual(META['status'],'review');self.assertIsNone(META['owner_approval'])
if __name__=='__main__':unittest.main(verbosity=2)
