#!/usr/bin/env python3
"""Brood Warden candidate. One editable four-limb, two-tendril master.
Fixed camera, physical scale and geometry. Does not render or replace the human.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import render_motion as b
DIRS=['e','s','w','n']; CELL=(256,256); PIVOT=(128,204)
CLIPS={'idle':(4,6,True),'move':(6,8,True),'charge_windup':(8,10,False),
 'charge':(6,14,True),'acid_attack':(6,10,False),'pulse_attack':(8,12,False),
 'recovery':(4,8,False),'hit':(2,10,False),'phase_transition':(6,10,False),'death':(10,8,False)}
RECIPE={'asset_id':'brood_warden','cell':list(CELL),'pivot':list(PIVOT),'clip':'move','frames':6,'fps':8,
 'physical_scale':1.80,'gait':{'stride':.28,'lift':.060,'stance':.70},
 'move_distance_per_cycle_game_units':.28/.70*64*1.80,
 'charge_distance_per_cycle_game_units':.38/.62*64*1.80,
 'materials':{k:{'hex':v,'wear':.27,'specular':.05} for k,v in {
  'flesh':'634237','muscle':'895540','dark_flesh':'31232A','tendon':'9B7657',
  'ridge':'574837','ivory':'BDAC8E','claw':'B4A087','mouth':'160E16','eye':'C39950',
  'shell':'333B3B','edge':'777869','groove':'1F2727','acid':'77823B','core':'B2B761','amber':'B08143'}.items()},
 'source':'warden_family.py plus existing render_motion.py',
 'design':'Broad anchored thorax, crown scutes, four limbs, two articulated tendrils, ventral acid throat. No new player art.',
 'approval':'review_pending'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def around(p,m):return b.trans(p)@m@b.trans(-np.asarray(p))
def smooth(t):t=float(np.clip(t,0,1));return t*t*(3-2*t)

class Warden(b.Master):
 def __init__(self):
  super().__init__(copy.deepcopy(RECIPE));self.clip='move'
  base=b.runner_master(self.recipe)
  self.parts=[p for p in base.parts if p['bone'] in ['head','jaw'] and not p['name'].startswith('temple_horn')]
  for p in self.parts:
   if p['name']=='head_cranium':p['matrix']=b.trans((0,.382,.53))@b.scaling((.185,.217,.14))
   elif p['name']=='brow_ridge':p['matrix']=b.trans((0,.463,.617))@b.scaling((.195,.143,.045))
   elif p['name'].startswith('eye_') and not p['name'].startswith('eye_socket'):p['matrix']=p['matrix']@b.scaling((.8,.8,.8))
  self.add('thorax','torso',(0,-.06,.54),(.40,.45,.258),'flesh',.90,organic=.06)
  self.add('abdomen','torso',(0,-.39,.40),(.29,.22,.17),'dark_flesh',.90,organic=.05)
  self.add('shoulder_bridge','torso',(0,.215,.575),(.43,.20,.219),'muscle',.88,organic=.035)
  self.add('neck','torso',(0,.355,.50),(.18,.19,.123),'dark_flesh',1.05,organic=.065)
  self.add('throat','throat',(0,.365,.455),(.155,.164,.12),'acid',1.05,organic=.10)
  self.add('throat_core','throat',(0,.467,.45),(.098,.069,.085),'core',1.10,organic=.07)
  for side in [-1,1]:
   # Hinged dorsal crown; source geometry remains constant between all actions.
   for j in range(5):
    y=-.38+j*.16;z=[.60,.72,.78,.74,.63][j];taper=[.65,.9,1,.90,.65][j]
    bone='crown_'+str(side)
    self.add(f'crown_plate_{side}_{j}',bone,(side*.18*taper,y,z),(.21*taper,.104,.075),'shell',.79,organic=.055)
    self.curve(f'crown_edge_{side}_{j}',bone,[(side*.028,y+.06,z+.067),(side*.19*taper,y+.08,z+.062),(side*.385*taper,y+.025,z-.045)],[.007,.014,.004],'edge')
    self.curve(f'crown_spine_{side}_{j}',bone,[(side*.20*taper,y,z+.048),(side*.26*taper,y-.03,z+.165),(side*.29*taper,y-.08,z+.19)],[.043,.025,.001],'ivory')
   for j in range(5):
    y=-.24+j*.085
    self.curve(f'flank_fold_{side}_{j}','torso',[(side*.28,y-.03,.56),(side*.392,y,.49),(side*.325,y+.03,.35)],[.018,.025,.005],'ridge')
   self.add(f'neck_guard_{side}','head',(side*.16,.36,.592),(.091,.164,.067),'shell',.76,organic=.03)
   self.curve(f'head_crown_{side}','head',[(side*.085,.39,.635),(side*.17,.33,.765),(side*.21,.20,.80)],[.051,.033,.001],'ivory')
   for kind in ['hind','fore']:
    u=f'{kind}_upper_{side}';l=f'{kind}_lower_{side}';f=f'{kind}_foot_{side}'
    radius=.118 if kind=='hind' else .144
    self.add(u+'_mass',u,(0,0,.47),(radius,radius,.52),'muscle',.88,organic=.06)
    self.add(u+'_guard',u,(0,-radius*.68,.39),(radius*.92,.065,.34),'shell',.72,organic=.045)
    self.add(l+'_joint',l,(0,0,0),(.08,.08,.09),'dark_flesh')
    self.add(l+'_limb',l,(0,0,.47),(.078,.079,.50),'flesh',.88,organic=.07)
    self.curve(l+'_rib',l,[(0,-.08,.03),(.036,-.092,.25),(0,-.088,.80)],[.026,.020,.003],'ivory')
    self.add(f+'_knuckle',f,(0,.021,.04),(.098,.124,.066),'shell',.82,organic=.045)
    for j in range(3):
     x=(j-1)*.066
     self.curve(f'{f}_claw{j}',f,[(x,.05,.06),(x,.13,.068),(x*.88,.212 if kind=='fore' else .17,.018)],[.031,.023,.001],'claw')
   for j in range(4):
    bone=f'tendril_{side}_{j}';r=.052*(1-.19*j)
    self.curve(bone,bone,[(0,0,0),(0,0,.34),(0,0,.70),(0,0,1)],[r,r*.94,r*.80,r*.74],'flesh')
    self.add(bone+'_ring',bone,(0,0,.08),(r*1.13,r*1.13,.058),'ridge',1.08)
    if j==3:self.curve(bone+'_tip',bone,[(0,0,.82),(0,0,1.05),(0,.025,1.2)],[.016,.010,.001],'ivory')
  self.sockets={'mouth':('jaw',np.array([0,.55,.413,1.])),
   'pulse':('torso',np.array([0,.10,.54,1.])),
   'tendril_l':('tendril_-1_3',np.array([0,0,1.,1.])),
   'tendril_r':('tendril_1_3',np.array([0,0,1.,1.]))}

 def rig(self,torso,phase=None,charge=False,pressure=0.,spread=0.,sway=0.,reach=0.,lift=0.):
  bones={'torso':torso,'head':torso@around((0,.32,.50),b.rot((1,0,0),.16*pressure))}
  bones['jaw']=bones['head']@around((0,.34,.405),b.rot((1,0,0),-.065-.43*pressure))
  bones['throat']=torso@around((0,.365,.455),b.scaling((1+.10*pressure,1+.07*pressure,1+.26*pressure)))
  for side in [-1,1]:
   bones['crown_'+str(side)]=torso@around((side*.045,0,.62),b.rot((0,1,0),side*(.055*pressure+.22*spread)))
   for kind,l1,l2 in [('hind',.33,.33),('fore',.38,.38)]:
    hip=(torso@np.array([side*(.29 if kind=='hind' else .34),-.29 if kind=='hind' else .235,.49 if kind=='hind' else .565,1.]))[:3]
    foot=np.array([side*(.38 if kind=='hind' else .46),-.35 if kind=='hind' else .31,.025])
    if phase is not None:
     offset=(0 if side==-1 else .5)+(.23 if kind=='fore' else 0)
     step,up,_=b.footstep(phase+offset,.38 if charge else .28,.08 if charge else .06,.62 if charge else .70)
     foot+=np.array([0,step,up])
    if kind=='fore':foot+=np.array([0,reach,lift])
    knee=b.knee(hip,foot,l1,l2,(0,1,0) if kind=='hind' else (side,.3,0))
    bones[f'{kind}_upper_{side}']=b.link(hip,knee);bones[f'{kind}_lower_{side}']=b.link(knee,foot);bones[f'{kind}_foot_{side}']=b.trans(foot)
   # Constant-length tendril segments; only joint rotations change.
   point=(torso@np.array([side*.30,-.22,.61,1.]))[:3]
   for j,length in enumerate([.19,.21,.21,.18]):
    yaw=side*(.75+.24*j+.40*spread)+.09*sway
    pitch=[.90,.28,-.28,-.95][j]+.48*spread+.055*sway
    direction=np.array([math.cos(pitch)*math.sin(yaw),math.cos(pitch)*math.cos(yaw),math.sin(pitch)])
    end=point+torso[:3,:3]@direction*length
    bones[f'tendril_{side}_{j}']=b.link(point,end);point=end
  return bones

 def pose(self,t):
  t=float(t);wave=math.sin(2*math.pi*t)
  if self.clip=='idle':return self.rig(b.trans((0,0,.004*wave)),pressure=.035+.025*wave,sway=wave)
  if self.clip in ['move','charge']:
   charging=self.clip=='charge'
   torso=b.trans((0,0,(-.04 if charging else 0)+.006*math.sin(4*math.pi*t)))@around((0,0,.53),b.rot((0,1,0),.017*wave))
   return self.rig(torso,t,charging,pressure=.04,sway=wave,spread=.07 if charging else 0)
  if self.clip=='charge_windup':
   a=smooth(t);return self.rig(b.trans((0,-.022*a,-.04*a)),pressure=.035+.005*a,spread=.07*a,sway=.08*a)
  if self.clip=='acid_attack':
   # Frames 0..2 build pressure; frame 3 begins emission, frames 4..5 recover.
   p=float(np.interp(t,[0,.4,.6,.8,1],[.035,1,.65,.12,.08]));back=-.019*p
   return self.rig(b.trans((0,back,-.012*p)),pressure=p,spread=.1*p,sway=.12*p)
  if self.clip=='pulse_attack':
   p=float(np.interp(t,[0,3/7,4/7,1],[0,1,.84,.06]))
   return self.rig(b.trans((0,0,-.027*p)),pressure=.035+.38*p,spread=p,sway=.16*p,reach=.015*p)
  if self.clip=='phase_transition':
   a=math.sin(math.pi*t);return self.rig(b.trans((0,-.012*a,.025*a)),pressure=.035+.62*a+.02*t,spread=.90*a+.08*t,sway=.32*math.sin(2*math.pi*t))
  if self.clip=='recovery':return self.rig(b.trans((0,0,-.025*(1-smooth(t)))),pressure=.035,sway=.12*(1-t))
  if self.clip=='hit':
   a=1-.8*t;return self.rig(b.trans((-.019*a,-.015*a,-.009*a)),pressure=.07,sway=-.2*a)
  if self.clip!='death':raise ValueError('Unknown clip '+self.clip)
  fall=smooth(t);bones=self.rig(np.eye(4),pressure=.035,spread=-.42*fall,sway=.06*(1-fall))
  for side in [-1,1]:
   for kind,length in [('hind',.33),('fore',.38)]:
    u=f'{kind}_upper_{side}';l=f'{kind}_lower_{side}';f=f'{kind}_foot_{side}'
    hip=bones[u][:3,3];start=bones[f][:3,3];target=start*(1-fall)+(hip+np.array([side*.15,.10,-.18]))*fall
    knee=b.knee(hip,target,length,length,(side,.3,0));bones[u]=b.link(hip,knee);bones[l]=b.link(knee,target);bones[f]=b.trans(target)@b.rot((1,0,0),.42*fall)
  collapse=b.trans((-.09*fall,0,-.26*fall))@around((0,0,.45),b.rot((0,1,0),1.40*fall))
  bones={k:collapse@m for k,m in bones.items()}
  minimum=min(float(((bones[p['bone']]@p['matrix'])[:3,:3]@p['vertices'].T+(bones[p['bone']]@p['matrix'])[:3,3:4])[2].min()) for p in self.parts)
  return {k:b.trans((0,0,.008-minimum))@m for k,m in bones.items()}

def build(out,ss=3):
 out=Path(out)
 if out.exists():raise ValueError('Output must be fresh; never overwrite another family')
 out.mkdir(parents=True);m=Warden();_,window,actors=b.vtk_scene(m,CELL,PIVOT,ss)
 meta={'asset_id':'brood_warden','status':'review','cell':list(CELL),'pivot':list(PIVOT),'directions':DIRS,
  'clips':{k:{'frames':n,'fps':fps,'loop':loop} for k,(n,fps,loop) in CLIPS.items()},'frames':[],
  'move_distance_per_cycle_game_units':RECIPE['move_distance_per_cycle_game_units'],
  'charge_distance_per_cycle_game_units':RECIPE['charge_distance_per_cycle_game_units'],
  'source':{Path(p).name:sha(p) for p in [__file__,b.__file__]},'owner_approval':None}
 try:
  for clip,(n,fps,loop) in CLIPS.items():
   m.clip=clip
   for d in DIRS:
    for i in range(n):
     im,sockets=b.render(m,d,i/n if loop else i/(n-1),window,actors,ss);box=im.getchannel('A').getbbox()
     if not box or min(box[:2])<2 or max(box[2:])>254:raise ValueError(f'Clipped {clip}/{d}/{i}: {box}')
     p=out/'frames'/clip/d/f'{i:03d}.png';p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
     meta['frames'].append({'clip':clip,'direction':d,'frame':i,'path':p.relative_to(out).as_posix(),'sha256':sha(p),'sockets':sockets})
   print('Rendered Warden',clip,flush=True)
 finally:window.Finalize()
 m.clip='move';b.export_glb(m,out/'master.glb');(out/'recipe.json').write_text(json.dumps(RECIPE,indent=2)+'\n')
 runtime=out/'runtime';runtime.mkdir();count=len(meta['frames']);pages=math.ceil(count/49)
 lines=[f'[gd_resource type="SpriteFrames" load_steps={1+pages+count} format=3]','']
 for p in range(pages):lines.append(f'[ext_resource type="Texture2D" path="res://assets/warden_review/atlas_{p}.png" id="a{p}"]')
 atlases=[Image.new('RGBA',(1820,1820)) for _ in range(pages)]
 for i,f in enumerate(meta['frames']):
  page=i//49;cell=i%49;x=cell%7*260+2;y=cell//7*260+2
  f.update(atlas=f'atlas_{page}.png',region=[x,y,256,256])
  with Image.open(out/f['path']) as im:atlases[page].paste(im,(x,y))
  lines+=['',f'[sub_resource type="AtlasTexture" id="f{i}"]',f'atlas = ExtResource("a{page}")',f'region = Rect2({x}, {y}, 256, 256)','filter_clip = true']
 animations=[]
 for clip,c in meta['clips'].items():
  for d in DIRS:
   frames=', '.join('{"duration": 1.0, "texture": SubResource("f%d")}'%i for i,f in enumerate(meta['frames']) if f['clip']==clip and f['direction']==d)
   animations.append('{"frames": ['+frames+'], "loop": '+str(c['loop']).lower()+', "name": &"'+clip+'_'+d+'", "speed": '+str(float(c['fps']))+'}')
 lines+=['','[resource]','animations = ['+',\n'.join(animations)+']','']
 for p,im in enumerate(atlases):im.save(runtime/f'atlas_{p}.png',optimize=True)
 (runtime/'sprite_frames.tres').write_text('\n'.join(lines))
 for p in [out/'manifest.json',runtime/'animation_index.json']:p.write_text(json.dumps(meta,indent=2)+'\n')
 return meta

def record(incoming,pack):
 incoming=Path(incoming);pack=Path(pack);meta=json.loads((incoming/'manifest.json').read_text())
 if meta['asset_id']!='brood_warden' or len(meta['frames'])!=240:raise ValueError('Wrong candidate')
 family=pack/'families/brood_warden'
 if family.exists():raise ValueError('Reconcile existing Warden first; no silent replacement')
 source=family/'source';source.mkdir(parents=True)
 for f in meta['frames']:
  rel=Path(f['path'])
  if rel.is_absolute() or '..' in rel.parts or rel.parts[0]!='frames' or sha(incoming/rel)!=f['sha256']:raise ValueError('Unsafe or changed frame')
  target=family/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(incoming/rel,target)
 for n in ['master.glb','recipe.json','manifest.json']:shutil.copyfile(incoming/n,source/n)
 shutil.copytree(incoming/'runtime',family/'review_runtime')
 sources=[pack/'source/warden_family.py',pack/'source/render_motion.py',source/'master.glb',source/'recipe.json']
 delivery={'asset_id':'brood_warden','status':'review','spec_sha256':sha(pack/'pack.json'),
  'sources':[{'path':p.relative_to(pack).as_posix(),'sha256':sha(p),'provenance':'Original project mesh/pose source. Same organism lineage; no ripped or independently generated image frames. Owner review pending.'} for p in sources],
  'frame_sha256':{(family/f['path']).relative_to(pack).as_posix():f['sha256'] for f in meta['frames']},
  'sockets':{(family/f['path']).relative_to(pack).as_posix():f['sockets'] for f in meta['frames']},
  'review':{},'public_source_permission':False,'owner_approval':None,
  'known_limits':['Modeled candidate finish, not final owner art approval.','GLB has the movement track; all ten action poses are editable in the Python source.','Existing simulation owns all attack and phase timing. Mouth/pulse sockets do not imply final attached VFX.']}
 (family/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n');previews(family,meta)
 print('WARDEN_RECORDED: 240 frames; protected human/families untouched; review only',flush=True)

def previews(family,meta):
 out=family/'reviews';out.mkdir(exist_ok=True)
 for clip,c in meta['clips'].items():
  pages=[]
  for i in range(c['frames']):
   im=Image.new('RGB',(1056,315),(24,30,32));draw=ImageDraw.Draw(im)
   draw.text((16,10),'BROOD WARDEN / '+clip.upper()+' / CANDIDATE — NATIVE SIZE',fill=(215,213,195))
   for j,d in enumerate(DIRS):
    with Image.open(family/'frames'/clip/d/f'{i:03d}.png') as f:im.paste(f,(j*264+4,38),f)
    draw.text((j*264+125,298),d.upper(),fill=(190,195,177))
   pages.append(im)
  if not c['loop']:pages += [pages[-1]]*max(1,round(c['fps']*.6))
  pages[0].save(out/(clip+'.gif'),save_all=True,append_images=pages[1:],duration=round(1000/c['fps']),loop=0,disposal=2)
  pages[0].save(out/(clip+'_half.webp'),save_all=True,append_images=pages[1:],duration=round(2000/c['fps']),loop=0,lossless=True)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path);p.add_argument('--record',type=Path);p.add_argument('--pack',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--ss',type=int,choices=range(1,7),default=3);args=p.parse_args()
 if args.record:record(args.record,args.pack)
 elif args.out:build(args.out,args.ss)
 else:p.error('Supply --out or --record')
