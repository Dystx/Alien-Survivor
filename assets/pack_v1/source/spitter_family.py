#!/usr/bin/env python3
"""Spitter-only review artwork. One editable master, seven articulated clips.
No player, runner or existing game art is modified. Never grants approval.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import render_motion as b
import runner_family as lineage

DIRS = ['e','s','w','n']
CELL, PIVOT = (128,128), (64,104)
CLIPS = {'idle':(4,6,True),'move':(6,10,True),'windup':(4,8,False),
         'attack':(4,12,False),'recovery':(2,8,False),'hit':(2,12,False),'death':(5,10,False)}
RECIPE = copy.deepcopy(lineage.RECIPE)
RECIPE.update(asset_id='spitter',cell=list(CELL),pivot=list(PIVOT),physical_scale=1.06,
              frames=6,fps=10,clip='move',gait={'stride':.22,'lift':.055},
              source='spitter_family.py using runner_family.py and render_motion.py',
              source_lineage='Same four-limbed organism; squat thorax, paired acid glands and articulated throat',
              move_distance_per_cycle_game_units=.22/.62*64*1.06)
RECIPE['materials'].update({
 'flesh':{'hex':'66423A','wear':.32,'specular':.04},
 'muscle':{'hex':'895442','wear':.27,'specular':.05},
 'dark_flesh':{'hex':'322126','wear':.24,'specular':.03},
 'acid':{'hex':'70823B','wear':.28,'specular':.10},
 'acid_rim':{'hex':'454A2A','wear':.27,'specular':.05},
 'acid_core':{'hex':'A0AD50','wear':.23,'specular':.10},
 'vein':{'hex':'494C2B','wear':.24,'specular':.03},
 'ivory':{'hex':'AF9C7C','wear':.25,'specular':.07},
 'ridge':{'hex':'664D3C','wear':.28,'specular':.04}})

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def around(p,m): return b.trans(p)@m@b.trans(-np.asarray(p))
def smooth(t): return lineage.smooth(t)

class Spitter(b.Master):
 def __init__(self):
  super().__init__(copy.deepcopy(RECIPE)); self.clip='move'
  base=b.runner_master(self.recipe); self.parts=base.parts
  # One shape per body part, not an unrelated image for each pose.
  for p in self.parts:
   name=p['name']
   if name=='thorax':p['matrix']=b.trans((0,-.018,.44))@b.scaling((.252,.30,.188))
   elif name=='abdomen':p['matrix']=b.trans((0,-.256,.377))@b.scaling((.202,.215,.151))
   elif name=='head_cranium':p['matrix']=b.trans((0,.344,.477))@b.scaling((.122,.180,.098))
   elif name=='scapular_mass':p['matrix']=b.trans((0,.14,.477))@b.scaling((.263,.141,.141))
   elif name.startswith('dorsal_spine'):p['matrix']=b.trans((0,0,.02))@b.scaling((.85,1,.86))
   elif name.startswith('eye_') and not name.startswith('eye_socket'):
    p['matrix']=p['matrix']@b.scaling((.7,.72,.7))
  self.add('throat_membrane','throat',(0,.304,.427),(.115,.133,.084),'dark_flesh',1,organic=.085)
  for side in [-1,1]:
   for j in range(2):
    x=side*(.204+.016*j);y=-.203+.185*j;z=.562
    self.add(f'gland_rim_{side}_{j}','sacs',(x,y,z),(.124,.155,.102),'acid_rim',1,organic=.06)
    self.add(f'gland_skin_{side}_{j}','sacs',(x,y,z+.035),(.113,.142,.102),'acid',1,organic=.075)
    self.add(f'gland_lobe_{side}_{j}','sacs',(x-side*.013,y+.005,z+.105),(.074,.112,.044),'acid_core',1,organic=.09)
    for k in range(3):
     yy=y-.075+k*.063
     self.curve(f'gland_vein_{side}_{j}_{k}','sacs',[(x-side*.073,yy,z+.09),(x-side*.018,yy+.015,z+.13),(x+side*.067,yy+.006,z+.097)],[.006,.007,.002],'vein')
   self.curve(f'feeding_duct_{side}','torso',[(side*.19,-.2,.535),(side*.252,.04,.537),(side*.145,.28,.451)],[.023,.03,.009],'acid_rim')
   for j in range(5):
    y=-.225+j*.074
    self.curve(f'flank_fold_{side}_{j}','torso',[(side*.15,y-.02,.51),(side*.234,y,.483),(side*.222,y+.016,.387)],[.01,.013,.003],'ridge')
   for j in range(3):
    self.curve(f'throat_fold_{side}_{j}','throat',[(side*.05,.23+j*.04,.47),(side*.113,.25+j*.04,.435),(side*.064,.27+j*.04,.38)],[.012,.016,.006],'tendon')
   self.curve(f'jaw_cheek_{side}','head',[(side*.1,.29,.46),(side*.122,.389,.454),(side*.088,.495,.416)],[.016,.016,.004],'tendon')
  self.sockets={'mouth':('jaw',np.array([0,.55,.413,1.]))}

 def _mouth_pose(self,bones,pressure):
  bones['head']=bones['torso']@around((0,.27,.46),b.rot((1,0,0),.105*pressure))
  bones['jaw']=bones['head']@around((0,.34,.405),b.rot((1,0,0),-.07-.44*pressure))
  bones['throat']=bones['torso']@around((0,.3,.425),b.scaling((1+.15*pressure,1+.06*pressure,1+.30*pressure)))
  bones['sacs']=bones['torso']@around((0,-.1,.53),b.scaling((1+.09*pressure,1+.04*pressure,1+.26*pressure)))
  return bones

 def pose(self,t):
  t=float(t)
  if self.clip=='move':
   bones=b.runner_pose(t,self.recipe)
   return self._mouth_pose(bones,.03+.025*math.sin(t*2*math.pi))
  bones=b.runner_pose(.12,self.recipe)
  if self.clip=='idle':
   pressure=.045+.035*math.sin(2*math.pi*t)
   bones['torso']=b.trans((0,0,.003*math.sin(2*math.pi*t)))@bones['torso']
  elif self.clip=='windup':
   pressure=.10+.9*smooth(t)
   bones['torso']=b.trans((0,-.014*pressure,-.012*pressure))@bones['torso']
  elif self.clip=='attack':
   pressure=float(np.interp(t,[0,1/3,2/3,1],[1,.5,.10,.025]))
   recoil=math.sin(math.pi*t)*.024
   bones['torso']=b.trans((0,-.014*pressure-recoil,-.012*pressure))@bones['torso']
  elif self.clip=='recovery':
   pressure=.025+.02*t
   bones['torso']=b.trans((0,-.00035*(1-t),-.0003*(1-t)))@bones['torso']
  elif self.clip=='hit':
   pressure=.06
   bones['torso']=b.trans((-.017*(1-.8*t),-.015*(1-.8*t),-.01))@bones['torso']
  elif self.clip=='death':
   pressure=.02*(1-t)
  else:raise ValueError('Unknown clip '+self.clip)
  self._mouth_pose(bones,pressure)
  # Foreclaws stay planted during the warning and spit; the head/jaw articulates.
  lineage.Runner._plant_fore(bones,{s:np.array([s*.24,.21,.02]) for s in [-1,1]})
  if self.clip=='death':
   fall=smooth(t)
   for side in [-1,1]:
    for kind,L in [('fore',.29),('hind',.24)]:
     upper=f'{kind}_upper_{side}';lower=f'{kind}_lower_{side}';foot=f'{kind}_foot_{side}'
     hip=bones[upper][:3,3].copy();old=bones[foot][:3,3].copy()
     target=old*(1-fall)+(hip+np.array([side*.14,.11,-.17]))*fall
     knee=b.knee(hip,target,L,L if kind=='fore' else .235,(side,.3,0))
     bones[upper]=b.link(hip,knee);bones[lower]=b.link(knee,target);bones[foot]=b.trans(target)@b.rot((1,0,0),.5*fall)
   collapse=b.trans((-.07*fall,0,-.26*fall))@around((0,0,.37),b.rot((0,1,0),1.40*fall))
   bones={k:collapse@m for k,m in bones.items()}
   minimum=min(float(((bones[p['bone']]@p['matrix'])[:3,:3]@p['vertices'].T+(bones[p['bone']]@p['matrix'])[:3,3:4])[2].min()) for p in self.parts)
   bones={k:b.trans((0,0,.008-minimum))@m for k,m in bones.items()}
  return bones


def build(out,ss=3):
 out=Path(out)
 if out.exists():raise ValueError('Output must not exist')
 out.mkdir(parents=True);model=Spitter();_,window,actors=b.vtk_scene(model,CELL,PIVOT,ss)
 meta={'asset_id':'spitter','status':'review','cell':list(CELL),'pivot':list(PIVOT),'directions':DIRS,
       'move_distance_per_cycle_game_units':RECIPE['move_distance_per_cycle_game_units'],
       'clips':{k:{'frames':n,'fps':fps,'loop':loop} for k,(n,fps,loop) in CLIPS.items()},'frames':[],
       'source':{p.name:sha(p) for p in [Path(__file__),Path(b.__file__),Path(lineage.__file__)]},'owner_approval':None}
 for clip,(count,fps,loop) in CLIPS.items():
  model.clip=clip
  for direction in DIRS:
   for i in range(count):
    t=i/count if loop else i/max(1,count-1)
    image,sockets=b.render(model,direction,t,window,actors,ss)
    box=image.getchannel('A').getbbox()
    if not box or box[0]<2 or box[1]<2 or box[2]>126 or box[3]>126:raise ValueError(f'Clipped {clip}/{direction}/{i}: {box}')
    p=out/'frames'/clip/direction/f'{i:03d}.png';p.parent.mkdir(parents=True,exist_ok=True);image.save(p)
    meta['frames'].append({'clip':clip,'direction':direction,'frame':i,'path':p.relative_to(out).as_posix(),'sha256':sha(p),'sockets':sockets})
  print('rendered',clip,flush=True)
 window.Finalize();model.clip='move';b.export_glb(model,out/'master.glb')
 (out/'recipe.json').write_text(json.dumps(RECIPE,indent=2)+'\n')
 runtime=out/'runtime';runtime.mkdir();atlas=Image.new('RGBA',(1320,1452))
 lines=['[gd_resource type="SpriteFrames" load_steps=110 format=3]','', '[ext_resource type="Texture2D" path="res://assets/spitter_review/atlas.png" id="1"]']
 for i,f in enumerate(meta['frames']):
  x=i%10*132+2;y=i//10*132+2;f['region']=[x,y,128,128]
  atlas.paste(Image.open(out/f['path']),(x,y))
  lines+=['',f'[sub_resource type="AtlasTexture" id="f{i}"]','atlas = ExtResource("1")',f'region = Rect2({x}, {y}, 128, 128)','filter_clip = true']
 animations=[]
 for clip,c in meta['clips'].items():
  for direction in DIRS:
   frames=', '.join('{"duration": 1.0, "texture": SubResource("f%d")}'%i for i,f in enumerate(meta['frames']) if f['clip']==clip and f['direction']==direction)
   animations.append('{"frames": ['+frames+'], "loop": '+str(c['loop']).lower()+', "name": &"'+clip+'_'+direction+'", "speed": '+str(float(c['fps']))+'}')
 lines+=['','[resource]','animations = ['+',\n'.join(animations)+']',''];atlas.save(runtime/'atlas.png',optimize=True)
 (runtime/'sprite_frames.tres').write_text('\n'.join(lines))
 for p in [out/'manifest.json',runtime/'animation_index.json']:p.write_text(json.dumps(meta,indent=2)+'\n')
 return meta

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--ss',type=int,default=3,choices=range(1,7));args=p.parse_args();build(args.out,args.ss)
