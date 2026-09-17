#!/usr/bin/env python3
"""Runner-only authored animation pass. Never reads or modifies the locked human.
Fixed geometry, articulated pose functions, camera/light rig and 96px frame cells.
The PNG output is a review candidate, not owner-approved production artwork.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import render_motion as b

DIRS = ['e', 's', 'w', 'n']
CLIPS = {'idle': (4, 6, True), 'move': (6, 12, True), 'attack': (4, 12, False), 'hit': (2, 12, False), 'death': (5, 10, False)}
CELL = (96, 96)
PIVOT = (48, 78)
RECIPE = {
    'asset_id': 'runner', 'clip': 'move', 'frames': 6, 'fps': 12,
    'cell': list(CELL), 'pivot': list(PIVOT), 'physical_scale': .91,
    'gait': {'stride': .24, 'lift': .061},
    'materials': {
        'flesh': {'hex': '704036', 'wear': .24, 'specular': .07},
        'muscle': {'hex': '91503E', 'wear': .21, 'specular': .08},
        'dark_flesh': {'hex': '392328', 'wear': .20, 'specular': .06},
        'tendon': {'hex': '8A6E56', 'wear': .20, 'specular': .07},
        'ridge': {'hex': '674B40', 'wear': .24, 'specular': .05},
        'ivory': {'hex': 'BAA483', 'wear': .22, 'specular': .08},
        'claw': {'hex': 'AA967A', 'wear': .20, 'specular': .11},
        'mouth': {'hex': '180F15', 'wear': .10, 'specular': .03},
        'eye': {'hex': 'C69651', 'wear': .04, 'specular': .15}
    },
    'source': 'runner_family.py with the project render_motion.py mesh/render library',
    'source_lineage': 'Refinement of the original runner master, not an unrelated image sheet',
    'approval': 'review_pending',
    'move_distance_per_cycle_game_units': .24 / .62 * 64 * .91
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def around(point, transform):
    return b.trans(point) @ transform @ b.trans(-np.asarray(point))

def smooth(t):
    t = float(np.clip(t, 0., 1.))
    return t*t*(3.-2.*t)

class Runner(b.Master):
    def __init__(self):
        super().__init__(copy.deepcopy(RECIPE))
        original = b.runner_master(self.recipe)
        self.parts = original.parts
        self.clip = 'move'
        # Refine the same creature: elongated predatory head, subdued eye size,
        # connective tissue and longitudinal folds rather than loose round parts.
        for part in self.parts:
            name = part['name']
            if name == 'head_cranium':
                part['matrix'] = b.trans((0, .355, .481)) @ b.scaling((.124, .194, .106))
            elif name == 'brow_ridge':
                part['matrix'] = b.trans((0, .431, .548)) @ b.scaling((.120, .132, .045))
            elif name.startswith('eye_') and not name.startswith('eye_socket'):
                part['matrix'] = part['matrix'] @ b.scaling((.68, .76, .65))
            elif name.endswith('_joint'):
                part['matrix'] = part['matrix'] @ b.scaling((1.07, 1.07, 1.15))
        self.add('neck_membrane', 'torso', (0, .259, .474), (.131, .135, .10), 'dark_flesh', 1, organic=.055)
        for side in [-1, 1]:
            for i in range(5):
                y = -.218 + i*.073
                self.curve(f'flank_fold_{side}_{i}', 'torso',
                    [(side*.105, y-.026, .555), (side*.177, y, .572), (side*.204, y+.020, .500), (side*.168, y+.035, .398)],
                    [.007, .010, .008, .002], 'ridge')
            self.curve(f'cheek_sinew_{side}', 'head',
                [(side*.101, .284, .472), (side*.133, .365, .462), (side*.086, .49, .431)],
                [.013, .015, .004], 'tendon')
            self.curve(f'lower_fang_{side}', 'jaw',
                [(side*.072, .545, .406), (side*.067, .572, .428), (side*.061, .569, .447)],
                [.013, .008, .0008], 'ivory')
        self.sockets = {'mouth': ('jaw', np.array([0, .55, .413, 1.]))}

    def pose(self, t):
        t = float(t)
        if self.clip == 'move':
            return b.runner_pose(t, self.recipe)
        bones = b.runner_pose(.12, self.recipe)
        if self.clip == 'idle':
            breath = math.sin(2*math.pi*t)
            sway = math.cos(2*math.pi*t)
            body = b.trans((0, 0, .004*breath)) @ around((0, .08, .47), b.rot((0, 1, 0), .012*sway))
            self._upper(bones, body)
            bones['head'] = bones['head'] @ around((0,.32,.48), b.rot((0,0,1),.024*breath))
            bones['jaw'] = bones['head'] @ around((0,.34,.405), b.rot((1,0,0),-.07-.035*breath))
            self._plant_fore(bones, {s: np.array([s*.24,.21,.02]) for s in [-1,1]})
        elif self.clip == 'attack':
            # Four distinct poses: compress, raise claws, strike, settle.
            phases = np.array([0., .33333333, .66666667, 1.])
            thrust = float(np.interp(t, phases, [-.018, -.028, .067, .005]))
            lift = float(np.interp(t, phases, [0., .157, .034, .008]))
            reach = float(np.interp(t, phases, [-.015, .015, .17, .01]))
            self._upper(bones, b.trans((0,thrust,.009+lift*.12)))
            feet = {s: np.array([s*(.24+.028*math.sin(math.pi*t)),.21+reach,.02+lift]) for s in [-1,1]}
            self._plant_fore(bones, feet)
            bones['jaw'] = bones['head'] @ around((0,.34,.405), b.rot((1,0,0),-.09-.34*math.sin(math.pi*t)))
        elif self.clip == 'hit':
            strength = 1.-.78*t
            self._upper(bones, b.trans((-.018*strength,-.016*strength,-.013*strength)) @ around((0,0,.46),b.rot((0,1,0),-.17*strength)))
            self._plant_fore(bones, {s: np.array([s*.24,.21,.02]) for s in [-1,1]})
        elif self.clip == 'death':
            fall = smooth(t)
            for side in [-1,1]:
                for kind,L1,L2,bend in [('hind',.24,.235,(0,1,0)),('fore',.29,.29,(side,.3,0))]:
                    upper=f'{kind}_upper_{side}'; lower=f'{kind}_lower_{side}'; foot=f'{kind}_foot_{side}'
                    hip = bones[upper][:3,3].copy()
                    old_foot=bones[foot][:3,3].copy()
                    tucked=hip+np.array([side*.12, .09 if kind=='hind' else .12, -.17])
                    target=old_foot*(1-fall)+tucked*fall
                    k=b.knee(hip,target,L1,L2,bend)
                    bones[upper]=b.link(hip,k);bones[lower]=b.link(k,target)
                    bones[foot]=b.trans(target)@b.rot((1,0,0),.55*fall)
            collapse=b.trans((-.09*fall,0,-.28*fall)) @ around((0,0,.36),b.rot((0,1,0),1.38*fall))
            bones={name:collapse@mat for name,mat in bones.items()}
            bones['jaw']=bones['jaw']@around((0,.34,.405),b.rot((1,0,0),-.16*fall))
            # Put the actual mesh on the floor after the physical side-fall. No
            # framewise image rotation, stretching, crop or scale normalization.
            minimum=min(float(((bones[p['bone']]@p['matrix'])[:3,:3]@p['vertices'].T+(bones[p['bone']]@p['matrix'])[:3,3:4])[2].min()) for p in self.parts)
            settle=b.trans((0,0,.008-minimum))
            bones={name:settle@mat for name,mat in bones.items()}
        else:
            raise ValueError('Unknown runner clip: '+self.clip)
        return bones

    @staticmethod
    def _upper(bones, mat):
        for name in ['torso','head','jaw']:
            bones[name]=mat@bones[name]

    @staticmethod
    def _plant_fore(bones, feet):
        for side in [-1,1]:
            base=np.array([side*.215,.17,.49,1.])
            hip=(bones['torso']@base)[:3]
            foot=feet[side]
            k=b.knee(hip,foot,.29,.29,(side,.3,0))
            bones[f'fore_upper_{side}']=b.link(hip,k)
            bones[f'fore_lower_{side}']=b.link(k,foot)
            bones[f'fore_foot_{side}']=b.trans(foot)


def build(out: Path, ss=3):
    if out.exists():
        raise ValueError('Choose a new output folder; existing art is never silently overwritten')
    out.mkdir(parents=True)
    model=Runner()
    _,window,actors=b.vtk_scene(model,CELL,PIVOT,ss)
    manifest={'asset_id':'runner','status':'review','cell':list(CELL),'pivot':list(PIVOT),'directions':DIRS,'clips':{},'frames':[],
              'move_distance_per_cycle_game_units':RECIPE['move_distance_per_cycle_game_units'],
              'source':{'runner_family.py':sha(__file__),'render_motion.py':sha(b.__file__)},'owner_approval':None}
    for clip,(count,fps,loop) in CLIPS.items():
        manifest['clips'][clip]={'frames':count,'fps':fps,'loop':loop}
        model.clip=clip
        for direction in DIRS:
            for i in range(count):
                phase=i/count if loop else i/max(1,count-1)
                image,sockets=b.render(model,direction,phase,window,actors,ss)
                alpha=image.getchannel('A'); box=alpha.getbbox()
                if box is None or box[0]<2 or box[1]<2 or box[2]>94 or box[3]>94:
                    raise ValueError(f'Clipped/empty {clip}/{direction}/{i}: {box}')
                file=out/'frames'/clip/direction/f'{i:03d}.png';file.parent.mkdir(parents=True,exist_ok=True)
                image.save(file)
                manifest['frames'].append({'clip':clip,'direction':direction,'frame':i,'path':file.relative_to(out).as_posix(),'sha256':sha(file),'sockets':sockets})
            print(clip,direction,'rendered',flush=True)
    window.Finalize()
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'recipe.json').write_text(json.dumps(RECIPE,indent=2)+'\n')
    model.clip='move'
    b.export_glb(model,out/'runner_master.glb')
    pack_review(out,manifest)
    previews(out,manifest)
    return manifest


def pack_review(out,meta):
    # Review-only atlas. Not the approved-only production exporter.
    atlas=Image.new('RGBA',(1000,900)); entries=meta['frames']
    text=['[gd_resource type="SpriteFrames" load_steps=86 format=3]','',
          '[ext_resource type="Texture2D" path="res://assets/runner_review/atlas.png" id="1"]']
    for i,f in enumerate(entries):
        x=i%10*100+2;y=i//10*100+2
        atlas.paste(Image.open(out/f['path']).convert('RGBA'),(x,y))
        f['region']=[x,y,96,96]
        text += ['',f'[sub_resource type="AtlasTexture" id="f{i}"]','atlas = ExtResource("1")',f'region = Rect2({x}, {y}, 96, 96)','filter_clip = true']
    animations=[]
    for clip,c in meta['clips'].items():
        for direction in DIRS:
            refs=', '.join('{"duration": 1.0, "texture": SubResource("f%d")}'%i for i,f in enumerate(entries) if f['clip']==clip and f['direction']==direction)
            animations.append('{"frames": ['+refs+'], "loop": '+str(c['loop']).lower()+', "name": &"'+clip+'_'+direction+'", "speed": '+str(float(c['fps']))+'}')
    text+=['','[resource]','animations = ['+',\n'.join(animations)+']','']
    runtime=out/'runtime';runtime.mkdir()
    atlas.save(runtime/'atlas.png',optimize=True)
    (runtime/'sprite_frames.tres').write_text('\n'.join(text))
    (runtime/'animation_index.json').write_text(json.dumps(meta,indent=2)+'\n')
    (out/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')


def previews(out,meta):
    preview=out/'reviews';preview.mkdir()
    for clip,c in meta['clips'].items():
        images=[]
        for i in range(c['frames']):
            page=Image.new('RGB',(800,330),(26,31,33));d=ImageDraw.Draw(page)
            d.text((16,10),f'RUNNER / {clip.upper()} / REVIEW CANDIDATE — NOT APPROVED',fill=(215,220,215))
            d.text((16,30),'Four rendered views • top native size • bottom 2x',fill=(144,156,151))
            for j,direction in enumerate(DIRS):
                cell=Image.open(out/'frames'/clip/direction/f'{i:03d}.png').convert('RGBA')
                page.paste(cell,(j*196+54,52),cell)
                large=cell.resize((192,192),Image.Resampling.NEAREST)
                page.paste(large,(j*196+6,138),large)
                d.text((j*196+72,124),direction.upper(),fill=(197,209,200))
            images.append(page)
        ms=round(1000/c['fps'])
        if not c['loop']:
            images+= [images[-1]]*max(1,round(c['fps']*.6))
        images[0].save(preview/f'runner_{clip}.gif',save_all=True,append_images=images[1:],duration=ms,loop=0,disposal=2)
        images[0].save(preview/f'runner_{clip}_half.webp',save_all=True,append_images=images[1:],duration=ms*2,loop=0,lossless=True)
        images[0].save(preview/f'runner_{clip}_poster.png')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--ss',type=int,default=3,choices=range(1,7))
    args=parser.parse_args()
    build(args.out,args.ss)
