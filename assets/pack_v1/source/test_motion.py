#!/usr/bin/env python3
"""Real motion/mesh checks; passing does not approve aesthetics or runtime use."""
from pathlib import Path
import importlib.util,json,struct,unittest,hashlib
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;PACK=HERE.parent
spec=importlib.util.spec_from_file_location('motion',HERE/'render_motion.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def recipe(n):return json.loads((PACK/f'families/{n}/source/rig.json').read_text())
def sequence(n,d):
    r=recipe(n);return [PACK/f'families/{n}/frames/{r["clip"]}/{d}/{i:03d}.png' for i in range(r['frames'])]
class MotionChecks(unittest.TestCase):
    def test_exact_first_motion_scope(self):
        paths=list((PACK/'families/player/frames/walk').rglob('*.png'))+list((PACK/'families/runner/frames/move').rglob('*.png'))
        self.assertEqual(len(paths),56)
    def test_fixed_cells_alpha_and_borders(self):
        for n in ['player','runner']:
            r=recipe(n)
            for d in 'eswn':
                for p in sequence(n,d):
                    im=Image.open(p);self.assertEqual(im.mode,'RGBA');self.assertEqual(list(im.size),r['cell'])
                    a=np.array(im)[:,:,3];self.assertEqual(a.max(),255);self.assertEqual(a[:2].max(),0);self.assertEqual(a[-2:].max(),0);self.assertEqual(a[:,:2].max(),0);self.assertEqual(a[:,-2:].max(),0)
    def test_real_unique_motion_not_translated_stills(self):
        for n in ['player','runner']:
            for d in 'eswn':
                raw=[];cropped=[]
                for p in sequence(n,d):
                    im=Image.open(p).convert('RGBa');raw.append(hashlib.sha256(im.tobytes()).hexdigest());cropped.append(hashlib.sha256(im.crop(im.getbbox()).tobytes()).hexdigest())
                self.assertEqual(len(set(raw)),recipe(n)['frames']);self.assertGreater(len(set(cropped)),1);self.assertNotEqual(cropped[0],cropped[-1])
    def test_distinct_real_views(self):
        for n in ['player','runner']:
            hashes=[hashlib.sha256(b''.join(Image.open(p).tobytes() for p in sequence(n,d))).hexdigest() for d in 'eswn']
            self.assertEqual(len(set(hashes)),4)
    def test_rig_loop_closure(self):
        for name,pose in [('player',m.player_pose),('runner',m.runner_pose)]:
            r=recipe(name)
            for key,a in pose(0,r).items():np.testing.assert_allclose(a,pose(1,r)[key],atol=1e-8)
    def test_two_link_lengths_are_constant(self):
        for name,pose,tests in [('player',m.player_pose,{'thigh':.35,'shin':.355}),('runner',m.runner_pose,{'fore_upper':.29,'fore_lower':.29,'hind_upper':.24,'hind_lower':.235})]:
            for t in np.linspace(0,1,96):
                p=pose(t,recipe(name))
                for bone,length in tests.items():
                    for side in [-1,1]:self.assertAlmostEqual(np.linalg.norm(p[f'{bone}_{side}'][:3,2]),length,places=7)
    def test_stance_foot_speed_is_constant(self):
        for n,stance in [('player',.6),('runner',.62)]:
            r=recipe(n);pts=[m.footstep(t,r['gait']['stride'],r['gait']['lift'],stance) for t in np.linspace(.01,stance-.01,20)]
            delta=np.diff([p[0] for p in pts]);np.testing.assert_allclose(delta,delta[0],atol=1e-9);self.assertTrue(all(p[1]==0 and p[2] for p in pts))
    def test_lift_is_articulated(self):
        for n in ['player','runner']:
            r=recipe(n);positions=[m.footstep(t,r['gait']['stride'],r['gait']['lift']) for t in np.linspace(0,1,60)]
            self.assertGreater(max(v[1] for v in positions),.05)
    def test_projection_dimensions_and_directions(self):
        self.assertAlmostEqual(m.PPU/np.sqrt(2),48);self.assertAlmostEqual(m.UP[2]*m.PPU,58.7877538268,places=7)
        expected={'e':[1,0],'s':[0,1],'w':[-1,0],'n':[0,-1]}
        for d,a in m.ANGLES.items():
            p=(m.rot((0,0,1),a)@np.array([0.,1,0,1]))[:3];screen=np.array([p@m.RIGHT,-p@m.UP]);screen/=np.linalg.norm(screen);np.testing.assert_allclose(screen,expected[d],atol=1e-8)
    def test_muzzle_sockets_follow_gun_and_stay_in_cell(self):
        r=recipe('player');master=m.player_master(r);record=json.loads((PACK/'families/player/source/sockets.json').read_text())
        self.assertEqual(len(record),32)
        for d in 'eswn':
            for i,p in enumerate(sequence('player',d)):
                xy=record[p.relative_to(PACK).as_posix()]['muzzle'];self.assertTrue(0<=xy[0]<128 and 0<=xy[1]<128)
                bone,point=master.sockets['muzzle'];v=(m.rot((0,0,1),m.ANGLES[d])@master.pose(i/8)[bone]@point)[:3]
                expect=[64+v@m.RIGHT*m.PPU,110-v@m.UP*m.PPU];np.testing.assert_allclose(xy,expect,atol=.0001)
    def test_glb_containers_and_animation_tracks(self):
        for n,count in [('player',104),('runner',82)]:
            p=PACK/f'families/{n}/source/master.glb';raw=p.read_bytes();magic,v,length=struct.unpack('<4sII',raw[:12]);self.assertEqual((magic,v,length),(b'glTF',2,len(raw)))
            jlen,jtype=struct.unpack('<I4s',raw[12:20]);self.assertEqual(jtype,b'JSON');doc=json.loads(raw[20:20+jlen]);self.assertEqual(len(doc['meshes']),count);self.assertEqual(len(doc['animations']),1)
            self.assertTrue(any(c['target']['path']=='rotation' for c in doc['animations'][0]['channels']))
            blen,btype=struct.unpack('<I4s',raw[20+jlen:28+jlen]);self.assertEqual(btype,b'BIN\x00')
            for view in doc['bufferViews']:self.assertLessEqual(view.get('byteOffset',0)+view['byteLength'],blen)
    def test_same_geometry_between_frames(self):
        for n,builder in [('player',m.player_master),('runner',m.runner_master)]:
            obj=builder(recipe(n));before=hashlib.sha256(b''.join(p['vertices'].tobytes() for p in obj.parts)).hexdigest()
            for t in [0,.125,.4,.9,1]:obj.pose(t)
            after=hashlib.sha256(b''.join(p['vertices'].tobytes() for p in obj.parts)).hexdigest();self.assertEqual(before,after)
if __name__=='__main__':unittest.main(verbosity=2)
