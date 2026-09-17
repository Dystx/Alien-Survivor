#!/usr/bin/env python3
"""One original charger master, seven authored clips, four real views.
Offline authoring only. Does not read, regenerate or modify the selected human.
Outputs are review candidates; production approval remains with the owner.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import render_motion as b

DIRS = ['e', 's', 'w', 'n']
CELL, PIVOT = (128, 128), (64, 104)
CLIPS = {'idle': (4, 6, True), 'move': (6, 12, True), 'windup': (4, 8, False),
         'charge': (6, 16, True), 'recovery': (4, 10, False),
         'hit': (2, 12, False), 'death': (5, 10, False)}
RECIPE = {
    'asset_id': 'charger', 'clip': 'move', 'frames': 6, 'fps': 12,
    'cell': list(CELL), 'pivot': list(PIVOT), 'physical_scale': 1.06,
    'gait': {'stride': .235, 'lift': .056},
    'charge_gait': {'stride': .35, 'lift': .105},
    'materials': {
        'flesh': {'hex': '704337', 'wear': .25, 'specular': .04},
        'muscle': {'hex': '92553D', 'wear': .22, 'specular': .045},
        'dark_flesh': {'hex': '382329', 'wear': .22, 'specular': .025},
        'tendon': {'hex': '9C785A', 'wear': .18, 'specular': .035},
        'ridge': {'hex': '765342', 'wear': .25, 'specular': .035},
        'ivory': {'hex': 'B4A086', 'wear': .24, 'specular': .065},
        'ivory_light': {'hex': 'D0B99B', 'wear': .18, 'specular': .05},
        'claw': {'hex': 'B2A18B', 'wear': .19, 'specular': .08},
        'mouth': {'hex': '1C1218', 'wear': .10, 'specular': .02},
        'eye': {'hex': 'C48F47', 'wear': .045, 'specular': .12},
        'ember': {'hex': 'A86435', 'wear': .17, 'specular': .04},
    },
    'source_lineage': 'Four-limbed runner lineage, heavy forward thorax and keratin wedge skull. No acid sacs or robot parts.',
    'source': 'charger_family.py plus existing render_motion.py',
    'move_distance_per_cycle_game_units': .235 / .62 * 64 * 1.06,
    'charge_distance_per_cycle_game_units': .35 / .62 * 64 * 1.06,
    'approval': 'review_pending',
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def around(point, mat):
    return b.trans(point) @ mat @ b.trans(-np.asarray(point))

def smooth(t):
    t = float(np.clip(t, 0, 1))
    return t*t*(3-2*t)

class Charger(b.Master):
    def __init__(self):
        super().__init__(copy.deepcopy(RECIPE))
        original = b.runner_master(self.recipe)
        self.parts = [p for p in original.parts if not p['name'].startswith('dorsal_spine')]
        self.clip = 'move'
        for p in self.parts:
            name = p['name']
            if name == 'thorax':
                p['matrix'] = b.trans((0, .037, .455)) @ b.scaling((.243, .282, .186))
            elif name == 'scapular_mass':
                p['matrix'] = b.trans((0, .157, .489)) @ b.scaling((.286, .152, .163))
            elif name == 'head_cranium':
                p['matrix'] = b.trans((0, .369, .470)) @ b.scaling((.147, .206, .114))
            elif name == 'brow_ridge':
                p['matrix'] = b.trans((0, .412, .526)) @ b.scaling((.148, .152, .055))
            elif name.startswith('eye_') and not name.startswith('eye_socket'):
                p['matrix'] = p['matrix'] @ b.scaling((.70, .80, .62))
            elif name.startswith('fore_upper') and name.endswith('_muscle'):
                p['matrix'] = p['matrix'] @ b.scaling((1.23, 1.18, 1.0))
        # A continuous flattened wedge, not a smooth sphere or a rescaled runner.
        vertices = np.array([[-.14,.285,.535],[.14,.285,.535],[-.169,.405,.580],
                             [.169,.405,.580],[-.055,.650,.464],[.055,.650,.464],
                             [-.13,.292,.603],[.13,.292,.603],[0,.420,.650],
                             [0,.662,.490]], dtype=float)
        faces = np.array([(0,2,6),(1,7,3),(6,2,8),(7,8,3),(6,8,7),
                          (2,4,9),(2,9,8),(8,9,3),(3,9,5),(4,5,9),
                          (0,6,7),(0,7,1),(0,1,3),(0,3,2),(2,3,5),(2,5,4)], dtype=np.uint32)
        self._part('keratin_wedge', 'head', vertices, faces, np.eye(4), 'ivory')
        self.curve('wedge_keel', 'head', [(0,.304,.610),(0,.417,.654),(0,.558,.568),(0,.659,.492)],
                   [.023,.020,.014,.002], 'ivory_light')
        self.add('neck_membrane','torso',(0,.279,.463),(.14,.141,.102),'dark_flesh',1,organic=.085)
        for side in [-1,1]:
            self.add(f'shoulder_plate_{side}','torso',(side*.233,.12,.575),(.097,.151,.060),
                     'ridge',.66,organic=.025,rotation=b.rot((0,1,0),side*.38))
            self.curve(f'shoulder_edge_{side}','torso',[(side*.17,.25,.579),(side*.289,.134,.616),(side*.264,.015,.544)],
                       [.008,.014,.003],'ivory')
            for i in range(4):
                y=-.204+i*.080
                self.curve(f'flank_crease_{side}_{i}','torso',[(side*.13,y-.02,.566),(side*.217,y,.562),(side*.24,y+.029,.441)],
                           [.008,.012,.003],'ridge')
            self.curve(f'cheek_tendon_{side}','head',[(side*.11,.278,.465),(side*.139,.367,.45),(side*.093,.506,.416)],
                       [.014,.018,.003],'tendon')
            self.curve(f'wedge_crack_{side}','head',[(side*.043,.48,.597),(side*.082,.443,.615),(side*.098,.408,.613)],
                       [.003,.004,.001],'ridge')
            for i in range(3):
                self.add(f'ember_scar_{side}_{i}','torso',(side*.245,.066+i*.047,.492),(.009,.016,.019),'ember',1)
        # Compact ridges preserve lineage without spitter sacs or brute armour.
        for i in range(3):
            y=-.255+i*.129
            self.add(f'spinal_scutum_{i}','torso',(0,y,.566),(.094,.076,.043),'ridge',.76)
        self.sockets = {'ram_tip':('head',np.array([0,.662,.490,1.]))}

    def planted(self, torso, head_angle=0.0):
        bones = {'torso':torso,'head':torso@around((0,.28,.46),b.rot((1,0,0),head_angle))}
        bones['jaw'] = bones['head'] @ around((0,.34,.405),b.rot((1,0,0),-.07))
        for side in [-1,1]:
            for kind,l1,l2,bend in [('hind',.24,.235,(0,1,0)),('fore',.29,.29,(side,.3,0))]:
                base=[side*.133,-.23,.405,1.] if kind=='hind' else [side*.215,.17,.49,1.]
                hip=(torso@base)[:3]
                foot=np.array([side*.178,-.235,.023]) if kind=='hind' else np.array([side*.24,.210,.020])
                knee=b.knee(hip,foot,l1,l2,bend)
                bones[f'{kind}_upper_{side}']=b.link(hip,knee)
                bones[f'{kind}_lower_{side}']=b.link(knee,foot)
                bones[f'{kind}_foot_{side}']=b.trans(foot)
        return bones

    @staticmethod
    def brace(amount):
        return b.trans((0,-.024*amount,-.057*amount)) @ around((0,.03,.44),b.rot((1,0,0),-.09*amount))

    def charging(self,t):
        # Trotting charge has a longer articulated stride. Root stays in-place;
        # runtime moves the creature using the existing simulation velocity.
        torso=self.brace(1.0) @ b.trans((0,0,.013*math.sin(t*2*math.pi)**2))
        bones={'torso':torso,'head':torso@around((0,.28,.46),b.rot((1,0,0),-.13))}
        bones['jaw']=bones['head']@around((0,.34,.405),b.rot((1,0,0),-.07))
        for side in [-1,1]:
            for kind,l1,l2,bend in [('hind',.24,.235,(0,1,0)),('fore',.29,.29,(side,.3,0))]:
                phase=(t+(0 if side==-1 else .5)+(.5 if kind=='fore' else 0))%1
                step,lift,stance=b.footstep(phase,.35,.105,.62)
                base=[side*.133,-.23,.405,1.] if kind=='hind' else [side*.215,.17,.49,1.]
                hip=(torso@base)[:3]
                foot=np.array([side*.178,-.235+step,.023+lift]) if kind=='hind' else np.array([side*.24,.210+step,.020+lift])
                knee=b.knee(hip,foot,l1,l2,bend)
                bones[f'{kind}_upper_{side}']=b.link(hip,knee)
                bones[f'{kind}_lower_{side}']=b.link(knee,foot)
                bones[f'{kind}_foot_{side}']=b.trans(foot)
        return bones

    def pose(self,t):
        t=float(t)
        if self.clip=='move': return b.runner_pose(t,self.recipe)
        if self.clip=='charge': return self.charging(t)
        if self.clip=='idle':
            return self.planted(b.trans((0,0,.004*math.sin(t*2*math.pi))), .012*math.sin(t*2*math.pi))
        if self.clip=='windup':
            amount=smooth(t)
            return self.planted(self.brace(amount),-.13*amount)
        if self.clip=='recovery':
            amount=1-smooth(t)
            return self.planted(self.brace(amount),-.13*amount)
        if self.clip=='hit':
            strength=1-.8*t
            return self.planted(b.trans((-.021*strength,-.022*strength,-.016)) @ around((0,0,.44),b.rot((0,1,0),-.10*strength)))
        if self.clip!='death': raise ValueError('Unknown clip '+self.clip)
        bones=self.planted(np.eye(4)); fall=smooth(t)
        for side in [-1,1]:
            for kind,l1,l2 in [('hind',.24,.235),('fore',.29,.29)]:
                upper=f'{kind}_upper_{side}';lower=f'{kind}_lower_{side}';foot_key=f'{kind}_foot_{side}'
                hip=bones[upper][:3,3].copy();start=bones[foot_key][:3,3].copy()
                foot=start*(1-fall)+(hip+np.array([side*.12,.11,-.17]))*fall
                knee=b.knee(hip,foot,l1,l2,(side,.3,0))
                bones[upper]=b.link(hip,knee);bones[lower]=b.link(knee,foot)
                bones[foot_key]=b.trans(foot)@b.rot((1,0,0),.50*fall)
        collapse=b.trans((-.06*fall,0,-.24*fall))@around((0,0,.37),b.rot((0,1,0),1.4*fall))
        bones={k:collapse@m for k,m in bones.items()}
        minimum=min(float(((bones[p['bone']]@p['matrix'])[:3,:3]@p['vertices'].T+(bones[p['bone']]@p['matrix'])[:3,3:4])[2].min()) for p in self.parts)
        return {k:b.trans((0,0,.008-minimum))@m for k,m in bones.items()}

def build(out: Path, ss=3):
    if out.exists(): raise ValueError('Use a fresh output; source candidates are not silently overwritten')
    out.mkdir(parents=True); model=Charger()
    _,window,actors=b.vtk_scene(model,CELL,PIVOT,ss)
    meta={'asset_id':'charger','status':'review','cell':list(CELL),'pivot':list(PIVOT), 'directions':DIRS,
          'clips':{c:{'frames':n,'fps':fps,'loop':loop} for c,(n,fps,loop) in CLIPS.items()},'frames':[],
          'source':{'charger_family.py':sha(__file__),'render_motion.py':sha(b.__file__)},
          'move_distance_per_cycle_game_units':RECIPE['move_distance_per_cycle_game_units'],
          'charge_distance_per_cycle_game_units':RECIPE['charge_distance_per_cycle_game_units'],'owner_approval':None}
    try:
        for clip,(count,fps,loop) in CLIPS.items():
            model.clip=clip
            for direction in DIRS:
                for index in range(count):
                    phase=index/count if loop else index/(count-1)
                    image,sockets=b.render(model,direction,phase,window,actors,ss)
                    box=image.getchannel('A').getbbox()
                    if not box or min(box[:2])<2 or max(box[2:])>126: raise ValueError(f'Clipped {clip}/{direction}/{index}: {box}')
                    path=out/'frames'/clip/direction/f'{index:03d}.png';path.parent.mkdir(parents=True,exist_ok=True);image.save(path)
                    meta['frames'].append({'clip':clip,'direction':direction,'frame':index,'path':path.relative_to(out).as_posix(),'sha256':sha(path),'sockets':sockets})
            print('Rendered charger',clip,flush=True)
    finally: window.Finalize()
    model.clip='move';b.export_glb(model,out/'master.glb')
    (out/'recipe.json').write_text(json.dumps(RECIPE,indent=2)+'\n')
    runtime=out/'runtime';runtime.mkdir()
    atlas=Image.new('RGBA',(1320,1716));lines=['[gd_resource type="SpriteFrames" load_steps=126 format=3]','',
        '[ext_resource type="Texture2D" path="res://assets/charger_review/atlas.png" id="1"]']
    for i,f in enumerate(meta['frames']):
        x=i%10*132+2;y=i//10*132+2;f['region']=[x,y,128,128]
        with Image.open(out/f['path']) as image: atlas.paste(image,(x,y))
        lines+=['',f'[sub_resource type="AtlasTexture" id="f{i}"]','atlas = ExtResource("1")',f'region = Rect2({x}, {y}, 128, 128)','filter_clip = true']
    animations=[]
    for clip,c in meta['clips'].items():
        for direction in DIRS:
            refs=', '.join('{"duration": 1.0, "texture": SubResource("f%d")}'%i for i,f in enumerate(meta['frames']) if f['clip']==clip and f['direction']==direction)
            animations.append('{"frames": ['+refs+'], "loop": '+str(c['loop']).lower()+', "name": &"'+clip+'_'+direction+'", "speed": '+str(float(c['fps']))+'}')
    lines+=['','[resource]','animations = ['+',\n'.join(animations)+']','']
    atlas.save(runtime/'atlas.png',optimize=True);(runtime/'sprite_frames.tres').write_text('\n'.join(lines))
    for path in [out/'manifest.json',runtime/'animation_index.json']:path.write_text(json.dumps(meta,indent=2)+'\n')
    return meta


def record(incoming: Path, pack: Path):
    meta=json.loads((incoming/'manifest.json').read_text())
    if meta['asset_id']!='charger' or len(meta['frames'])!=124: raise ValueError('Unexpected candidate')
    family=pack/'families/charger'
    if family.exists(): raise ValueError('Existing charger must be reconciled before publishing')
    source=family/'source';source.mkdir(parents=True)
    for f in meta['frames']:
        rel=Path(f['path'])
        if rel.is_absolute() or '..' in rel.parts or rel.parts[0]!='frames':raise ValueError('Unsafe frame path')
        if sha(incoming/rel)!=f['sha256']:raise ValueError('Candidate changed')
        dest=family/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(incoming/rel,dest)
    for name in ['master.glb','recipe.json','manifest.json']:shutil.copyfile(incoming/name,source/name)
    shutil.copytree(incoming/'runtime',family/'review_runtime')
    sources=[pack/'source/charger_family.py',pack/'source/render_motion.py',source/'master.glb',source/'recipe.json']
    delivery={'asset_id':'charger','status':'review','spec_sha256':sha(pack/'pack.json'),
        'sources':[{'path':p.relative_to(pack).as_posix(),'sha256':sha(p),'provenance':'Original project mesh and pose source. Same organism lineage; no stock or independently generated frames. Owner review pending.'} for p in sources],
        'frame_sha256':{(family/f['path']).relative_to(pack).as_posix():f['sha256'] for f in meta['frames']},
        'sockets':{(family/f['path']).relative_to(pack).as_posix():f['sockets'] for f in meta['frames']},
        'review':{},'public_source_permission':False,'owner_approval':None,
        'known_limits':['Modeled review finish, not final artwork approval.','GLB carries editable meshes and movement track; all other actions are in the pose source.','Existing collision and damage timings are unchanged by visual animation.']}
    (family/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
    previews(family,meta)
    print('CHARGER_RECORDED: 124 frames; no human/other-family changes; review only',flush=True)


def previews(family,meta):
    review=family/'reviews';review.mkdir(exist_ok=True)
    for clip,c in meta['clips'].items():
        pages=[]
        for i in range(c['frames']):
            page=Image.new('RGB',(1024,440),(24,30,32));draw=ImageDraw.Draw(page)
            draw.text((18,12),'CHARGER / '+clip.upper()+' / REVIEW CANDIDATE',fill=(220,215,199))
            for j,d in enumerate(DIRS):
                with Image.open(family/'frames'/clip/d/f'{i:03d}.png') as im:
                    page.paste(im,(j*256+64,36),im);large=im.resize((256,256),Image.Resampling.NEAREST);page.paste(large,(j*256,175),large)
                draw.text((j*256+112,160),d.upper(),fill=(194,197,179))
            pages.append(page)
        if not c['loop']:pages += [pages[-1]]*max(1,round(c['fps']*.6))
        pages[0].save(review/(clip+'.gif'),save_all=True,append_images=pages[1:],duration=round(1000/c['fps']),loop=0,disposal=2)
        pages[0].save(review/(clip+'_half.webp'),save_all=True,append_images=pages[1:],duration=round(2000/c['fps']),loop=0,lossless=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--record',type=Path)
    parser.add_argument('--pack',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--ss',type=int,default=3,choices=range(1,7))
    args=parser.parse_args()
    if args.record:record(args.record,args.pack)
    elif args.out:build(args.out,args.ss)
    else:parser.error('Provide --out for render or --record for publication')
