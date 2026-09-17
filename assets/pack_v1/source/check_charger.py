#!/usr/bin/env python3
"""Actual charger frames and stable source geometry checks; not art approval."""
import hashlib,json,struct,sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
import charger_family as c
ROOT=Path(sys.argv[1]);sys.argv=sys.argv[:1]
META=json.loads((ROOT/'manifest.json').read_text())
class Checks(unittest.TestCase):
 def test_scope(self):
  self.assertEqual(len(META['frames']),124);self.assertEqual(len(list((ROOT/'frames').rglob('*.png'))),124)
  self.assertEqual(set(META['clips']),set(c.CLIPS))
 def test_rgba_and_borders(self):
  for f in META['frames']:
   im=Image.open(ROOT/f['path']);self.assertEqual(im.mode,'RGBA');self.assertEqual(im.size,(128,128))
   box=im.getchannel('A').getbbox();self.assertTrue(box);self.assertTrue(min(box[:2])>=2 and max(box[2:])<=126)
 def test_hashes(self):
  for f in META['frames']:self.assertEqual(c.sha(ROOT/f['path']),f['sha256'])
 def test_atlas_regions_match_source_pixels(self):
  atlas=Image.open(ROOT/'runtime/atlas.png');self.assertLessEqual(max(atlas.size),2048)
  for f in META['frames']:
   x,y,w,h=f['region'];self.assertEqual(atlas.crop((x,y,x+w,y+h)).tobytes(),Image.open(ROOT/f['path']).tobytes())
 def test_motion_not_translated_stills(self):
  for clip,(n,_,loop) in c.CLIPS.items():
   for d in c.DIRS:
    hashes=[]
    for i in range(n):
     im=Image.open(ROOT/f'frames/{clip}/{d}/{i:03d}.png');im=im.crop(im.getchannel('A').getbbox())
     hashes.append(hashlib.sha256(im.convert('RGBa').tobytes()).hexdigest())
    self.assertGreaterEqual(len(set(hashes)),2 if clip=='idle' else n)
    if loop:self.assertNotEqual(hashes[0],hashes[-1])
 def test_unique_real_directions(self):
  for clip in c.CLIPS:self.assertEqual(len({c.sha(ROOT/f'frames/{clip}/{d}/000.png') for d in c.DIRS}),4)
 def test_constant_source_topology(self):
  model=c.Charger();before=[p['vertices'].copy() for p in model.parts]
  for clip in c.CLIPS:
   model.clip=clip
   for t in [0,.5,1]:
    bones=model.pose(t)
    for p,v in zip(model.parts,before):
     self.assertTrue(np.array_equal(v,p['vertices']));self.assertIn(p['bone'],bones)
 def test_loop_closure(self):
  model=c.Charger()
  for clip in ['idle','move','charge']:
   model.clip=clip;a=model.pose(0);b=model.pose(1)
   for k in a:self.assertTrue(np.allclose(a[k],b[k],atol=1e-8),k)
 def test_windup_plants_all_four_feet(self):
  model=c.Charger();model.clip='windup';a=model.pose(0);b=model.pose(1)
  for k in a:
   if '_foot_' in k:self.assertTrue(np.allclose(a[k],b[k]),k)
  self.assertLess(b['torso'][2,3],a['torso'][2,3]-.03)
 def test_recovery_settles_to_idle(self):
  model=c.Charger();model.clip='recovery';a=model.pose(1);model.clip='idle';b=model.pose(0)
  for k in a:self.assertTrue(np.allclose(a[k],b[k],atol=1e-8),k)
 def test_fixed_limb_lengths(self):
  model=c.Charger()
  for clip in c.CLIPS:
   model.clip=clip
   for t in np.linspace(0,1,12):
    bones=model.pose(t)
    for side in [-1,1]:
     for kind,upper,lower in [('fore',.29,.29),('hind',.24,.235)]:
      self.assertAlmostEqual(np.linalg.norm(bones[f'{kind}_upper_{side}'][:3,2]),upper,places=6)
      self.assertAlmostEqual(np.linalg.norm(bones[f'{kind}_lower_{side}'][:3,2]),lower,places=6)
 def test_grounded_death(self):
  model=c.Charger();model.clip='death'
  for t in np.linspace(0,1,5):
   bones=model.pose(t);minimum=100.
   for p in model.parts:
    m=bones[p['bone']]@p['matrix'];minimum=min(minimum,float((m[:3,:3]@p['vertices'].T+m[:3,3:4])[2].min()))
   self.assertAlmostEqual(minimum,.008,places=5)
 def test_socket_and_design(self):
  for f in META['frames']:
   x,y=f['sockets']['ram_tip'];self.assertTrue(0<=x<128 and 0<=y<128)
  names=[p['name'] for p in c.Charger().parts]
  self.assertIn('keratin_wedge',names);self.assertFalse(any('acid' in s or 'rifle' in s for s in names))
 def test_editable_model_not_approval(self):
  raw=(ROOT/'master.glb').read_bytes();self.assertEqual(raw[:4],b'glTF');self.assertEqual(len(raw),struct.unpack_from('<I',raw,8)[0])
  self.assertIsNone(META['owner_approval']);self.assertEqual(META['status'],'review')
if __name__=='__main__':unittest.main(verbosity=2)
