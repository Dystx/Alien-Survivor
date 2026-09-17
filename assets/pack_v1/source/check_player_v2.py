#!/usr/bin/env python3
"""Actual pixel, geometry and attachment checks for player v2; not art approval."""
import hashlib,json,math,struct,sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
import player_rework_v2 as a
ROOT=Path(sys.argv[1]);sys.argv=sys.argv[:1]
META=json.loads((ROOT/'manifest.json').read_text())

class Checks(unittest.TestCase):
 def test_exact_scope(self):
  self.assertEqual(len(META['frames']),128)
  self.assertEqual(len(list((ROOT/'frames').rglob('*.png'))),128)
  self.assertEqual(META['directions'],a.DIRS)
  self.assertEqual(set(META['clips']),{'ready','walk','fire'})
 def test_alpha_and_hashes(self):
  for f in META['frames']:
   im=Image.open(ROOT/f['path'])
   self.assertEqual(im.mode,'RGBA');self.assertEqual(im.size,a.CELL)
   box=im.getchannel('A').getbbox()
   self.assertTrue(box and box[0]>=2 and box[1]>=2 and box[2]<=126 and box[3]<=126)
   self.assertEqual(a.sha(ROOT/f['path']),f['sha256'])
 def test_atlas_source_pixels(self):
  atlas=Image.open(ROOT/'runtime/atlas.png')
  self.assertLessEqual(max(atlas.size),2048)
  for f in META['frames']:
   x,y,w,h=f['region']
   self.assertEqual(atlas.crop((x,y,x+w,y+h)).tobytes(),Image.open(ROOT/f['path']).tobytes())
 def test_socket_bounds(self):
  for f in META['frames']:
   for name,p in f['sockets'].items():
    self.assertTrue(1<p[0]<127 and 1<p[1]<127,(name,p))
 def test_stock_seated_on_shoulder_every_frame(self):
  for f in META['frames']:
   self.assertTrue(np.allclose(f['sockets']['stock'],f['sockets']['shoulder'],atol=.0001))
  model=a.Survivor()
  for clip in a.CLIPS:
   model.clip=clip
   for t in np.linspace(0,1,25):
    p=model.pose(t)
    self.assertTrue(np.allclose(p['gun']@np.array([0,0,0,1]),p['torso']@np.r_[a.BUTT,1]))
 def test_rifle_is_above_upper_chest(self):
  model=a.Survivor()
  for clip in a.CLIPS:
   model.clip=clip
   for t in np.linspace(0,1,11):
    p=model.pose(t)
    self.assertGreater((p['gun']@np.array([0,0,0,1]))[2],1.39)
    self.assertGreater((p['gun']@a.MUZZLE_LOCAL)[2],1.35)
 def test_hands_hold_rifle(self):
  model=a.Survivor()
  for clip in a.CLIPS:
   model.clip=clip
   for t in np.linspace(0,1,15):
    p=model.pose(t)
    for s,grip in [(1,a.TRIGGER_LOCAL),(-1,a.SUPPORT_LOCAL)]:
     self.assertTrue(np.allclose(p['hand_'+str(s)][:3,3],(p['gun']@grip)[:3]))
     self.assertTrue(np.allclose((p['forearm_'+str(s)]@np.array([0,0,1,1]))[:3],(p['gun']@grip)[:3]))
 def test_fixed_limb_lengths(self):
  model=a.Survivor()
  for clip in a.CLIPS:
   model.clip=clip
   for t in np.linspace(0,1,19):
    p=model.pose(t)
    for side in [-1,1]:
     for bone,length in [('upperarm',.277),('forearm',.263),('thigh',.391),('shin',.405)]:
      self.assertAlmostEqual(np.linalg.norm(p[f'{bone}_{side}'][:3,2]),length,places=8)
 def test_recoil_does_not_move_feet(self):
  model=a.Survivor();model.clip='fire';first=model.pose(0)
  for t in np.linspace(0,1,31):
   p=model.pose(t)
   for bone in ['pelvis','foot_-1','foot_1']:
    self.assertTrue(np.array_equal(p[bone],first[bone]))
  self.assertFalse(np.allclose(model.pose(1/3)['torso'],first['torso']))
 def test_loop_closure(self):
  model=a.Survivor()
  for clip in ['ready','walk']:
   model.clip=clip;first=model.pose(0);last=model.pose(1)
   for name in first:self.assertTrue(np.allclose(first[name],last[name],atol=1e-8))
 def test_genuine_views_and_moving_limbs(self):
  for clip,(count,_,_) in a.CLIPS.items():
   self.assertEqual(len({a.sha(ROOT/f'frames/{clip}/{d}/000.png') for d in a.DIRS}),8)
   for d in a.DIRS:
    minimum=8 if clip=='walk' else (3 if clip=='fire' else 2)
    self.assertGreaterEqual(len({a.sha(ROOT/f'frames/{clip}/{d}/{i:03d}.png') for i in range(count)}),minimum)
 def test_topology_constant(self):
  model=a.Survivor();original=[p['vertices'].copy() for p in model.parts]
  for clip in a.CLIPS:
   model.clip=clip
   for t in [0,.25,.5,.75,1]:
    model.pose(t)
    for p,v in zip(model.parts,original):self.assertTrue(np.array_equal(p['vertices'],v))
 def test_screen_direction_calibration(self):
  for j,d in enumerate(a.DIRS):
   theta=j*math.tau/8
   root=a.b.rot((0,0,1),a.root_angle(theta))
   forward=(root@np.array([0,1,0,0]))[:3]
   screen=np.array([forward@a.b.RIGHT,-forward@a.b.UP])
   screen/=np.linalg.norm(screen)
   self.assertTrue(np.allclose(screen,[math.cos(theta),math.sin(theta)],atol=1e-8),d)
 def test_no_helmet_or_old_robot_construction(self):
  names=' '.join(p['name'] for p in a.Survivor().parts)
  self.assertIn('cropped_hair',names);self.assertIn('face',names)
  for name in ['visor','helmet','cuirass','respirator','backpack_spine']:
   self.assertNotIn(name,names)
 def test_editable_source_and_review_status(self):
  raw=(ROOT/'source/master.glb').read_bytes()
  self.assertEqual(raw[:4],b'glTF');self.assertEqual(struct.unpack_from('<I',raw,8)[0],len(raw))
  self.assertEqual(META['status'],'review');self.assertIsNone(META['owner_approval'])
  self.assertEqual(META['source_sha256'],a.sha(a.__file__))
  self.assertEqual(META['renderer_sha256'],a.sha(a.b.__file__))
  self.assertIn('death',META['missing'])
if __name__=='__main__':unittest.main(verbosity=2)
