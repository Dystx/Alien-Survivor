#!/usr/bin/env python3
"""Inspect actual runner frames and their stable authoring rig; not owner approval."""
import hashlib,json,struct,sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
import runner_family as a
ROOT=Path(sys.argv[1]);sys.argv=sys.argv[:1]
META=json.loads((ROOT/'manifest.json').read_text())
class RunnerChecks(unittest.TestCase):
 def test_exact_scope(self):
  self.assertEqual(len(META['frames']),84)
  self.assertEqual(len(list((ROOT/'frames').rglob('*.png'))),84)
  self.assertEqual(set(META['clips']),set(a.CLIPS))
 def test_declared_hashes(self):
  for f in META['frames']:self.assertEqual(a.sha(ROOT/f['path']),f['sha256'])
 def test_rgba_cells_and_borders(self):
  for f in META['frames']:
   im=Image.open(ROOT/f['path']);self.assertEqual(im.mode,'RGBA');self.assertEqual(im.size,(96,96))
   box=im.getchannel('A').getbbox();self.assertTrue(box);self.assertTrue(box[0]>=2 and box[1]>=2 and box[2]<=94 and box[3]<=94)
 def test_unique_articulation(self):
  for clip,(count,_,_) in a.CLIPS.items():
   for direction in a.DIRS:
    hashes=set()
    for i in range(count):
     im=Image.open(ROOT/f'frames/{clip}/{direction}/{i:03d}.png').convert('RGBA');im=im.crop(im.getchannel('A').getbbox())
     hashes.add(hashlib.sha256(im.convert('RGBa').tobytes()).hexdigest())
    self.assertEqual(len(hashes),count)
 def test_genuine_directions(self):
  for clip in a.CLIPS:
   hashes=[a.sha(ROOT/f'frames/{clip}/{direction}/000.png') for direction in a.DIRS]
   self.assertEqual(len(set(hashes)),4)
 def test_atlas_matches_every_source_pixel(self):
  atlas=Image.open(ROOT/'runtime/atlas.png')
  for f in META['frames']:
   x,y,w,h=f['region'];im=Image.open(ROOT/f['path'])
   self.assertEqual(atlas.crop((x,y,x+w,y+h)).tobytes(),im.tobytes())
 def test_geometry_does_not_morph(self):
  rig=a.Runner();original=[p['vertices'].copy() for p in rig.parts]
  for clip in a.CLIPS:
   rig.clip=clip
   for t in np.linspace(0,1,6):
    rig.pose(t)
    for p,v in zip(rig.parts,original):self.assertTrue(np.array_equal(p['vertices'],v))
 def test_loop_poses_close(self):
  rig=a.Runner()
  for clip in ['move','idle']:
   rig.clip=clip;start=rig.pose(0);end=rig.pose(1)
   for name in start:self.assertTrue(np.allclose(start[name],end[name],atol=1e-8),name)
 def test_attack_is_articulated(self):
  rig=a.Runner();rig.clip='attack';base=rig.pose(0);strike=rig.pose(2/3)
  relative_base=np.linalg.inv(base['torso'])@base['fore_lower_1'];relative_strike=np.linalg.inv(strike['torso'])@strike['fore_lower_1']
  self.assertGreater(float(np.max(np.abs(relative_base-relative_strike))),.03)
 def test_death_stays_on_ground(self):
  rig=a.Runner();rig.clip='death'
  for t in np.linspace(0,1,5):
   bones=rig.pose(t);minimum=100.
   for p in rig.parts:
    m=bones[p['bone']]@p['matrix'];pts=m[:3,:3]@p['vertices'].T+m[:3,3:4];minimum=min(minimum,float(pts[2].min()))
   self.assertAlmostEqual(minimum,.008,places=5)
 def test_editable_model_and_review_status(self):
  raw=(ROOT/'runner_master.glb').read_bytes();self.assertEqual(raw[:4],b'glTF');self.assertEqual(struct.unpack_from('<I',raw,8)[0],len(raw))
  self.assertEqual(META['status'],'review');self.assertIsNone(META['owner_approval'])
if __name__=='__main__':unittest.main(verbosity=2)
