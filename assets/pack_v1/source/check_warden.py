#!/usr/bin/env python3
"""Check actual Warden pixels and articulated source, not final art approval."""
import hashlib,json,struct,sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
import warden_family as a
ROOT=Path(sys.argv[1]);sys.argv=sys.argv[:1]
META=json.loads((ROOT/'manifest.json').read_text())
class Checks(unittest.TestCase):
 def test_scope(self):
  self.assertEqual(len(META['frames']),240);self.assertEqual(len(list((ROOT/'frames').rglob('*.png'))),240)
  self.assertEqual(set(META['clips']),set(a.CLIPS))
 def test_alpha_cells_hashes(self):
  for f in META['frames']:
   im=Image.open(ROOT/f['path']);self.assertEqual(im.size,a.CELL);self.assertEqual(im.mode,'RGBA')
   box=im.getchannel('A').getbbox();self.assertIsNotNone(box);self.assertTrue(min(box[:2])>=2 and max(box[2:])<=254)
   self.assertEqual(a.sha(ROOT/f['path']),f['sha256'])
 def test_atlas_regions_and_gutters(self):
  atlases={p.name:Image.open(p) for p in (ROOT/'runtime').glob('atlas_*.png')};self.assertEqual(len(atlases),5)
  for im in atlases.values():self.assertLessEqual(max(im.size),2048)
  for f in META['frames']:
   x,y,w,h=f['region'];im=atlases[f['atlas']]
   self.assertEqual(im.crop((x,y,x+w,y+h)).tobytes(),Image.open(ROOT/f['path']).tobytes())
   self.assertIsNone(im.crop((x-2,y-2,x,y+h+2)).getchannel('A').getbbox())
 def test_not_translated_stills(self):
  for clip,(count,_,loop) in a.CLIPS.items():
   for d in a.DIRS:
    hashes=[]
    for i in range(count):
     im=Image.open(ROOT/f'frames/{clip}/{d}/{i:03d}.png');im=im.crop(im.getchannel('A').getbbox())
     hashes.append(hashlib.sha256(im.convert('RGBa').tobytes()).hexdigest())
    self.assertGreaterEqual(len(set(hashes)),2 if clip=='idle' else count,clip+'/'+d)
    if loop:self.assertNotEqual(hashes[0],hashes[-1])
 def test_genuine_views(self):
  for clip in a.CLIPS:self.assertEqual(len({a.sha(ROOT/f'frames/{clip}/{d}/000.png') for d in a.DIRS}),4)
 def test_stable_topology_and_palette(self):
  m=a.Warden();before=[(p['vertices'].copy(),p['colors'].copy()) for p in m.parts]
  for clip in a.CLIPS:
   m.clip=clip
   for t in [0,.3,1]:
    bones=m.pose(t)
    for p,(v,c) in zip(m.parts,before):
     self.assertTrue(np.array_equal(p['vertices'],v));self.assertTrue(np.array_equal(p['colors'],c));self.assertIn(p['bone'],bones)
 def test_loop_closure(self):
  m=a.Warden()
  for clip in ['idle','move','charge']:
   m.clip=clip;p=m.pose(0);q=m.pose(1)
   for k in p:self.assertTrue(np.allclose(p[k],q[k],atol=1e-8),clip+'/'+k)
 def test_all_feet_planted_in_windup(self):
  m=a.Warden();m.clip='charge_windup';p=m.pose(0)
  for t in np.linspace(0,1,8):
   q=m.pose(t)
   for k in p:
    if '_foot_' in k:self.assertTrue(np.allclose(p[k],q[k]))
 def test_limb_lengths(self):
  m=a.Warden()
  for clip in a.CLIPS:
   m.clip=clip
   for t in np.linspace(0,1,7):
    bones=m.pose(t)
    for k,mat in bones.items():
     if '_upper_' in k or '_lower_' in k:self.assertAlmostEqual(float(np.linalg.norm(mat[:3,2])),.33 if k.startswith('hind') else .38,places=6)
 def test_two_tendrils_constant_segment_lengths(self):
  m=a.Warden()
  for clip in a.CLIPS:
   m.clip=clip
   for t in [0,.4,1]:
    bones=m.pose(t);keys=[k for k in bones if k.startswith('tendril_')];self.assertEqual(len(keys),8)
    for side in [-1,1]:
     for j,L in enumerate([.19,.21,.21,.18]):self.assertAlmostEqual(float(np.linalg.norm(bones[f'tendril_{side}_{j}'][:3,2])),L,places=6)
 def test_acid_pressure_and_release(self):
  m=a.Warden();m.clip='acid_attack';p=m.pose(0);q=m.pose(.4);r=m.pose(1)
  self.assertGreater(np.linalg.det(q['throat'][:3,:3]),np.linalg.det(p['throat'][:3,:3])*1.2)
  self.assertLess(np.linalg.det(r['throat'][:3,:3]),np.linalg.det(q['throat'][:3,:3])*.8)
 def test_phase_opens_crown(self):
  m=a.Warden();m.clip='phase_transition';p=m.pose(0);q=m.pose(.5)
  self.assertGreater(np.max(np.abs(p['crown_1']-q['crown_1'])),.1)
 def test_grounded_death(self):
  m=a.Warden();m.clip='death'
  for t in np.linspace(0,1,10):
   bones=m.pose(t);low=100.
   for p in m.parts:
    mat=bones[p['bone']]@p['matrix'];low=min(low,float((mat[:3,:3]@p['vertices'].T+mat[:3,3:4])[2].min()))
   self.assertAlmostEqual(low,.008,places=6)
 def test_sockets_within_cells(self):
  for f in META['frames']:
   self.assertEqual(set(f['sockets']),{'mouth','pulse','tendril_l','tendril_r'})
   for point in f['sockets'].values():self.assertTrue(0<=point[0]<256 and 0<=point[1]<256)
 def test_editable_master_and_no_approval(self):
  raw=(ROOT/'master.glb').read_bytes();self.assertEqual(raw[:4],b'glTF');self.assertEqual(struct.unpack_from('<I',raw,8)[0],len(raw))
  self.assertEqual(META['status'],'review');self.assertIsNone(META['owner_approval'])
if __name__=='__main__':unittest.main(verbosity=2)
