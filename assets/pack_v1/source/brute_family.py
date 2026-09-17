#!/usr/bin/env python3
"""Brute-only art candidate: broad charcoal shell, four weight-bearing limbs.
One current editable mesh/pose source; never regenerates the locked human.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import render_motion as b
DIRS=['e','s','w','n']
CELL,PIVOT=(160,160),(80,136)
CLIPS={'idle':(4,6,True),'move':(6,8,True),'windup':(4,8,False),
       'attack':(4,10,False),'recovery':(2,8,False),'hit':(2,10,False),'death':(6,8,False)}
RECIPE={'asset_id':'brute','cell':list(CELL),'pivot':list(PIVOT),'clip':'move','frames':6,'fps':8,
 'physical_scale':1.27,'gait':{'stride':.22,'lift':.053,'stance':.70},
 'move_distance_per_cycle_game_units':.22/.70*64*1.27,
 'materials':{'flesh':{'hex':'55403B','wear':.26,'specular':.04},
 'muscle':{'hex':'78523F','wear':.27,'specular':.04},'dark_flesh':{'hex':'30242A','wear':.25,'specular':.03},
 'tendon':{'hex':'88664C','wear':.20,'specular':.04},'ridge':{'hex':'51473B','wear':.27,'specular':.035},
 'ivory':{'hex':'A99475','wear':.25,'specular':.05},'claw':{'hex':'A18F77','wear':.22,'specular':.07},
 'mouth':{'hex':'170F15','wear':.11,'specular':.02},'eye':{'hex':'BE9048','wear':.05,'specular':.11},
 'shell':{'hex':'383D3D','wear':.35,'specular':.035},'shell_edge':{'hex':'727466','wear':.29,'specular':.04},
 'shell_dark':{'hex':'252D2D','wear':.29,'specular':.02},'amber':{'hex':'A87C40','wear':.20,'specular':.05}},
 'source':'brute_family.py with the existing render_motion.py mesh/render library',
 'source_lineage':'Four-limbed lineage, independent wide thorax, short skull, heavy forelimbs and segmented keratin shell; no enlarged runner substitute.',
 'approval':'review_pending'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def around(p,m):return b.trans(p)@m@b.trans(-np.asarray(p))
def smooth(t):t=float(np.clip(t,0,1));return t*t*(3-2*t)

class Brute(b.Master):
 def __init__(self):
  super().__init__(copy.deepcopy(RECIPE));self.clip='move'
  # Independent proportions and rig footprint; only the organism's facial parts
  # are shared. No global runner rescale or per-frame shape change.
  base=b.runner_master(self.recipe)
  self.parts=[p for p in base.parts if p['bone'] in ['head','jaw'] and not p['name'].startswith('temple_horn') and p['name'] != 'snout_bone']
  for p in self.parts:
   name=p['name']
   if name=='head_cranium':p['matrix']=b.trans((0,.350,.462))@b.scaling((.182,.170,.116))
   elif name=='brow_ridge':p['matrix']=b.trans((0,.41,.542))@b.scaling((.189,.11,.059))
   elif name.startswith('eye_') and not name.startswith('eye_socket'):p['matrix']=p['matrix']@b.scaling((.7,.72,.7))
  self.add('wide_thorax','torso',(0,-.015,.470),(.330,.352,.211),'flesh',.89,organic=.055)
  self.add('broad_abdomen','torso',(0,-.305,.39),(.253,.192,.151),'dark_flesh',.89,organic=.05)
  self.add('shoulder_mass','torso',(0,.190,.501),(.355,.164,.191),'muscle',.88,organic=.035)
  self.add('neck','torso',(0,.30,.454),(.187,.121,.107),'dark_flesh',1,organic=.065)
  # Layered, individually shaped scutes with raised broken edges and grooves.
  for j in range(5):
   y=-.32+j*.132; taper=[.55,.86,1.,.92,.65][j]; z=[.558,.613,.650,.616,.550][j]
   for side in [-1,1]:
    x=side*.146*taper
    self.add(f'carapace_{side}_{j}','torso',(x,y,z),(.184*taper,.092,.078),'shell',.86,organic=.045,rotation=b.rot((0,1,0),side*.39))
    self.curve(f'carapace_edge_{side}_{j}','torso',[(side*.013,y+.052,z+.077),(side*.137*taper,y+.068,z+.075),(side*.299*taper,y+.056,z-.028)], [.006,.010,.004], 'shell_edge')
    self.curve(f'plate_fissure_{side}_{j}','torso',[(side*.072*taper,y-.04,z+.077),(side*.123*taper,y-.016,z+.081),(side*.153*taper,y+.009,z+.065)], [.003,.004,.001], 'shell_dark')
  for side in [-1,1]:
   self.add(f'shoulder_cap_{side}','torso',(side*.294,.179,.558),(.129,.159,.100),'shell',.70,organic=.025)
   self.curve(f'shoulder_rim_{side}','torso',[(side*.25,.31,.597),(side*.39,.22,.615),(side*.39,.096,.514)],[.01,.014,.004],'shell_edge')
   for j in range(4):
    y=-.19+j*.09
    self.curve(f'flank_membrane_{side}_{j}','torso',[(side*.289,y-.03,.51),(side*.333,y,.452),(side*.279,y+.028,.340)],[.014,.020,.004],'ridge')
   self.add(f'head_guard_{side}','head',(side*.132,.365,.531),(.085,.138,.054),'shell',.72,organic=.025)
   self.curve(f'head_rim_{side}','head',[(side*.031,.458,.585),(side*.150,.456,.575),(side*.213,.377,.532)],[.006,.01,.003],'shell_edge')
   for kind in ['hind','fore']:
    u=f'{kind}_upper_{side}';l=f'{kind}_lower_{side}';f=f'{kind}_foot_{side}'
    radius=.113 if kind=='hind' else .127
    self.add(u+'_mass',u,(0,0,.46),(radius,radius*.93,.53),'muscle',.85,organic=.05)
    self.add(u+'_shell',u,(0,-radius*.70,.41),(radius*.91,.068,.30),'shell',.69,organic=.025)
    self.add(l+'_joint',l,(0,0,0),(.077,.078,.11),'dark_flesh',1)
    self.add(l+'_tendon',l,(0,0,.46),(.076,.071,.49),'flesh',.88,organic=.065)
    self.add(l+'_guard',l,(0,-.065,.45),(.069,.028,.32),'shell',.65)
    self.add(l+'_amber_fold',l,(side*.067,.008,.13),(.012,.032,.068),'amber',1.15)
    self.add(f+'_knuckle',f,(0,.023,.027),(.089,.107,.049),'shell',.74,organic=.05)
    for toe in range(3):
     x=(toe-1)*.057
     self.curve(f'{f}_toe_{toe}',f,[(x,.04,.053),(x,.095,.06),(x*.85,.157 if kind=='fore' else .13,.019)],[.026,.021,.001],'claw')
  for p in self.parts:
   if p['bone'] in ['head','jaw']:p['matrix']=b.trans((0,.045,-.015))@p['matrix']
  self.sockets={'impact':('fore_foot_1',np.array([0,.13,.019,1.]))}

 def rig(self,torso,phase=None,reach=0.0,lift=0.0,head_angle=0.0):
  bones={'torso':torso,'head':torso@around((0,.285,.46),b.rot((1,0,0),head_angle))}
  bones['jaw']=bones['head']@around((0,.34,.405),b.rot((1,0,0),-.07))
  for side in [-1,1]:
   for kind,l1,l2 in [('hind',.28,.28),('fore',.32,.32)]:
    root=[side*.223,-.270,.435,1] if kind=='hind' else [side*.289,.185,.491,1]
    hip=(torso@root)[:3];foot=np.array([side*.29,-.30,.023]) if kind=='hind' else np.array([side*.36,.240,.020])
    if phase is not None:
     p=phase+(0.0 if side==-1 else .5)+(.28 if kind=='fore' else 0.)
     step,up,_=b.footstep(p,.22,.053,.70);foot+=np.array([0,step,up])
    if kind=='fore':foot+=np.array([0,reach,lift])
    knee=b.knee(hip,foot,l1,l2,(0,1,0) if kind=='hind' else (side,.32,0))
    bones[f'{kind}_upper_{side}']=b.link(hip,knee);bones[f'{kind}_lower_{side}']=b.link(knee,foot);bones[f'{kind}_foot_{side}']=b.trans(foot)
  return bones

 def pose(self,t):
  t=float(t)
  if self.clip=='idle':return self.rig(b.trans((0,0,.004*math.sin(2*math.pi*t))))
  if self.clip=='move':
   torso=b.trans((0,0,.006*math.sin(4*math.pi*t)))@around((0,0,.46),b.rot((0,1,0),.019*math.sin(2*math.pi*t)))
   return self.rig(torso,t,head_angle=.013*math.sin(2*math.pi*t))
  if self.clip=='windup':
   a=smooth(t);return self.rig(b.trans((0,-.018*a,-.045*a)),head_angle=-.08*a)
  if self.clip=='attack':
   # First pose agrees with wind-up end; claws rise then strike and settle.
   key=[0,1/3,2/3,1]
   reach=float(np.interp(t,key,[0,.016,.155,0]));lift=float(np.interp(t,key,[0,.20,.06,0]))
   body=float(np.interp(t,key,[-.045,.012,-.055,-.016]))
   return self.rig(b.trans((0,-.018*(1-t),body)),reach=reach,lift=lift,head_angle=-.08*(1-t))
  if self.clip=='recovery':return self.rig(b.trans((0,0,-.016*(1-smooth(t)))))
  if self.clip=='hit':
   s=1-.8*t;return self.rig(b.trans((-.017*s,-.013*s,-.007*s))@around((0,0,.46),b.rot((0,1,0),-.035*s)))
  if self.clip!='death':raise ValueError('Unknown clip '+self.clip)
  bones=self.rig(np.eye(4));fall=smooth(t)
  for side in [-1,1]:
   for kind,length in [('hind',.28),('fore',.32)]:
    u=f'{kind}_upper_{side}';l=f'{kind}_lower_{side}';f=f'{kind}_foot_{side}'
    hip=bones[u][:3,3];start=bones[f][:3,3];target=start*(1-fall)+(hip+np.array([side*.14,.11,-.18]))*fall
    knee=b.knee(hip,target,length,length,(side,.3,0));bones[u]=b.link(hip,knee);bones[l]=b.link(knee,target);bones[f]=b.trans(target)@b.rot((1,0,0),.44*fall)
  collapse=b.trans((-.07*fall,0,-.20*fall))@around((0,0,.37),b.rot((0,1,0),1.35*fall))
  bones={k:collapse@m for k,m in bones.items()}
  minimum=min(float(((bones[p['bone']]@p['matrix'])[:3,:3]@p['vertices'].T+(bones[p['bone']]@p['matrix'])[:3,3:4])[2].min()) for p in self.parts)
  return {k:b.trans((0,0,.008-minimum))@m for k,m in bones.items()}

def build(out: Path, ss=3):
    if out.exists(): raise ValueError('Use a fresh output; source candidates are not silently overwritten')
    out.mkdir(parents=True); model=Brute()
    _,window,actors=b.vtk_scene(model,CELL,PIVOT,ss)
    meta={'asset_id':'brute','status':'review','cell':list(CELL),'pivot':list(PIVOT), 'directions':DIRS,
          'clips':{c:{'frames':n,'fps':fps,'loop':loop} for c,(n,fps,loop) in CLIPS.items()},'frames':[],
          'source':{'brute_family.py':sha(__file__),'render_motion.py':sha(b.__file__)},
          'move_distance_per_cycle_game_units':RECIPE['move_distance_per_cycle_game_units'],
          'owner_approval':None}
    try:
        for clip,(count,fps,loop) in CLIPS.items():
            model.clip=clip
            for direction in DIRS:
                for index in range(count):
                    phase=index/count if loop else index/(count-1)
                    image,sockets=b.render(model,direction,phase,window,actors,ss)
                    box=image.getchannel('A').getbbox()
                    if not box or min(box[:2])<2 or max(box[2:])>158: raise ValueError(f'Clipped {clip}/{direction}/{index}: {box}')
                    path=out/'frames'/clip/direction/f'{index:03d}.png';path.parent.mkdir(parents=True,exist_ok=True);image.save(path)
                    meta['frames'].append({'clip':clip,'direction':direction,'frame':index,'path':path.relative_to(out).as_posix(),'sha256':sha(path),'sockets':sockets})
            print('Rendered brute',clip,flush=True)
    finally: window.Finalize()
    model.clip='move';b.export_glb(model,out/'master.glb')
    (out/'recipe.json').write_text(json.dumps(RECIPE,indent=2)+'\n')
    runtime=out/'runtime';runtime.mkdir()
    atlas=Image.new('RGBA',(1640,1968));lines=['[gd_resource type="SpriteFrames" load_steps=114 format=3]','',
        '[ext_resource type="Texture2D" path="res://assets/brute_review/atlas.png" id="1"]']
    for i,f in enumerate(meta['frames']):
        x=i%10*164+2;y=i//10*164+2;f['region']=[x,y,160,160]
        with Image.open(out/f['path']) as image: atlas.paste(image,(x,y))
        lines+=['',f'[sub_resource type="AtlasTexture" id="f{i}"]','atlas = ExtResource("1")',f'region = Rect2({x}, {y}, 160, 160)','filter_clip = true']
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
    if meta['asset_id']!='brute' or len(meta['frames'])!=112: raise ValueError('Unexpected candidate')
    family=pack/'families/brute'
    if family.exists(): raise ValueError('Existing brute must be reconciled before publishing')
    source=family/'source';source.mkdir(parents=True)
    for f in meta['frames']:
        rel=Path(f['path'])
        if rel.is_absolute() or '..' in rel.parts or rel.parts[0]!='frames':raise ValueError('Unsafe frame path')
        if sha(incoming/rel)!=f['sha256']:raise ValueError('Candidate changed')
        dest=family/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(incoming/rel,dest)
    for name in ['master.glb','recipe.json','manifest.json']:shutil.copyfile(incoming/name,source/name)
    shutil.copytree(incoming/'runtime',family/'review_runtime')
    sources=[pack/'source/brute_family.py',pack/'source/render_motion.py',source/'master.glb',source/'recipe.json']
    delivery={'asset_id':'brute','status':'review','spec_sha256':sha(pack/'pack.json'),
        'sources':[{'path':p.relative_to(pack).as_posix(),'sha256':sha(p),'provenance':'Original project mesh and pose source. Same organism lineage; no stock or independently generated frames. Owner review pending.'} for p in sources],
        'frame_sha256':{(family/f['path']).relative_to(pack).as_posix():f['sha256'] for f in meta['frames']},
        'sockets':{(family/f['path']).relative_to(pack).as_posix():f['sockets'] for f in meta['frames']},
        'review':{},'public_source_permission':False,'owner_approval':None,
        'known_limits':['Modeled review finish, not final artwork approval.','GLB carries editable meshes and movement track; all other actions are in the pose source.','Existing collision and damage timings are unchanged by visual animation.']}
    (family/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
    previews(family,meta)
    print('BRUTE_RECORDED: 112 frames; no human/other-family changes; review only',flush=True)


def previews(family,meta):
    review=family/'reviews';review.mkdir(exist_ok=True)
    for clip,c in meta['clips'].items():
        pages=[]
        for i in range(c['frames']):
            page=Image.new('RGB',(1280,550),(24,30,32));draw=ImageDraw.Draw(page)
            draw.text((18,12),'BRUTE / '+clip.upper()+' / REVIEW CANDIDATE',fill=(220,215,199))
            for j,d in enumerate(DIRS):
                with Image.open(family/'frames'/clip/d/f'{i:03d}.png') as im:
                    page.paste(im,(j*320+80,36),im);large=im.resize((320,320),Image.Resampling.NEAREST);page.paste(large,(j*320,225),large)
                draw.text((j*320+145,205),d.upper(),fill=(194,197,179))
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
