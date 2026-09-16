#!/usr/bin/env python3
"""Coherent actor review source. An articulated HUMAN, not an armoured robot.
All views/actions come from the same per-family editable mesh and pose functions.
This is authoring output; it does not grant owner approval or production export.
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image
import render_motion as b

DIRS=['e','s','w','n']
CLIPS={
 'player':{'idle':(4,6,True),'walk':(8,12,True),'walk_back':(8,12,True),'strafe_left':(8,12,True),'strafe_right':(8,12,True),'shoot':(4,16,False),'walk_fire':(8,12,True),'hit':(2,12,False),'death':(6,10,False)},
 'runner':{'idle':(4,6,True),'move':(6,12,True),'attack':(4,12,False),'hit':(2,12,False),'death':(5,10,False)},
 'spitter':{'idle':(4,6,True),'move':(6,10,True),'windup':(4,8,False),'attack':(4,12,False),'recovery':(2,8,False),'hit':(2,12,False),'death':(5,10,False)},
 'charger':{'idle':(4,6,True),'move':(6,12,True),'windup':(4,8,False),'charge':(6,16,True),'recovery':(4,10,False),'hit':(2,12,False),'death':(5,10,False)},
 'brute':{'idle':(4,6,True),'move':(6,8,True),'windup':(4,8,False),'attack':(4,10,False),'recovery':(2,8,False),'hit':(2,10,False),'death':(6,8,False)},
 'brood_warden':{'idle':(4,6,True),'move':(6,8,True),'acid_attack':(6,10,False),'charge_windup':(8,10,False),'charge':(6,14,True),'pulse_attack':(8,12,False),'recovery':(4,8,False),'hit':(2,10,False),'death':(10,8,False),'phase_transition':(6,10,False)}
}
SIZES={'player':([160,160],[80,112]),'runner':([128,128],[64,80]),'spitter':([160,160],[80,108]),'charger':([160,160],[80,104]),'brute':([192,192],[96,136]),'brood_warden':([288,288],[144,204])}

def material(hex,wear=.12,specular=.05,**kw):return dict(hex=hex,wear=wear,specular=specular,**kw)
def recipe(kind):
 cell,pivot=SIZES[kind]
 if kind=='player':
  mats={'cloth':material('303735',.13),'trousers':material('4E5140',.18),'vest':material('41463D',.19),'webbing':material('252D28',.16),'pouch':material('53543F',.13),'skin':material('BA8969',.045,.10),'skin_shadow':material('956A51',.04),'hair':material('2D241F',.15),'stubble':material('574033',.1),'white':material('B7B7A7',.03),'black':material('1B2223',.13),'steel':material('414A4D',.12,.16),'plate':material('566162',.1,.19),'edge':material('7A8583',.1,.17),'amber':material('B59C67',.09)}
  gait={'stride':.33,'lift':.10};scale=1.0
 else:
  mats={'flesh':material('804737',.14,.10),'muscle':material('975542',.14,.13),'dark_flesh':material('432629',.13,.08),'tendon':material('9A7862',.14,.1),'ivory':material('C2AD8B',.1,.12),'ridge':material('9F866D',.15,.1),'mouth':material('1D1216',.06),'eye':material('D6A75E',.05,.24),'claw':material('B6A48B',.1,.16),'acid':material('839D2F',.14,.25),'acid_light':material('B1C949',.1,.25),'shell':material('353C3C',.17,.15),'shell_edge':material('727569',.17,.12)}
  gait={'stride':.255,'lift':.068};scale={'runner':1.0,'spitter':1.14,'charger':1.22,'brute':1.65,'brood_warden':2.25}[kind]
 return {'asset_id':kind,'cell':cell,'pivot':pivot,'physical_scale':scale,'gait':gait,'materials':mats,'clips':CLIPS[kind],'camera':'pack_v1 dimetric 30-degree elevation, fixed scale and light','source_kind':'original procedural mesh with named articulated node transforms','review':'candidate; no owner approval asserted'}

class ActionMaster(b.Master):
 def __init__(self,r):super().__init__(r);self.clip='idle'
 def pose(self,t):return pose(self.recipe,t,self.clip)

def human_master(r):
 m=ActionMaster(r)
 m.add('shirt','torso',(0,0,1.09),(.197,.124,.246),'cloth',.60)
 m.add('cargo_pelvis','pelvis',(0,0,.756),(.201,.117,.113),'trousers',.94)
 m.add('vest_front','torso',(0,.109,1.145),(.188,.048,.185),'vest',.39)
 m.add('vest_back','torso',(0,-.117,1.139),(.18,.032,.186),'vest',.42)
 for side in [-1,1]:
  m.add('vest_strap_'+str(side),'torso',(side*.134,.048,1.344),(.03,.134,.035),'webbing',.65)
  m.add('vest_side_'+str(side),'torso',(side*.181,-.008,1.09),(.025,.119,.136),'webbing',.8)
  m.add('chest_pocket_'+str(side),'torso',(side*.099,.16,1.208),(.061,.029,.079),'pouch',.68)
  m.add('pocket_flap_'+str(side),'torso',(side*.099,.189,1.236),(.062,.009,.019),'vest',.55)
  m.add('pocket_stitch_'+str(side),'torso',(side*.099,.199,1.224),(.049,.003,.002),'edge',.7)
  m.add('waist_pouch_'+str(side),'pelvis',(side*.147,.11,.792),(.061,.047,.063),'pouch',.63)
  for j in range(3):m.add(f'molle_{side}_{j}','torso',(side*.104,.176,1.0+j*.035),(.062,.008,.007),'webbing',.6)
 m.add('zip','torso',(0,.161,1.17),(.006,.006,.157),'black',.6)
 m.add('zip_pull','torso',(0,.171,1.276),(.008,.005,.017),'edge',.6)
 m.add('belt','pelvis',(0,0,.824),(.214,.127,.029),'webbing',.68)
 m.add('belt_buckle','pelvis',(0,.131,.826),(.033,.014,.022),'edge',.55)
 # Open human face, ears and short hair. No helmet, visor, mask or metal joints.
 m.add('neck','head',(0,.002,1.381),(.058,.058,.086),'skin')
 m.add('head','head',(0,.022,1.492),(.086,.084,.126),'skin',.93)
 m.add('jaw','head',(0,.053,1.403),(.065,.059,.050),'skin',.72)
 m.add('short_hair','head',(0,-.008,1.586),(.090,.078,.043),'hair',.72)
 m.add('hair_back','head',(0,-.064,1.520),(.079,.024,.071),'hair',.90)
 m.add('chin_stubble','head',(0,.092,1.409),(.047,.006,.022),'stubble',1.15)
 m.add('lower_lip','head',(0,.105,1.432),(.021,.004,.004),'skin_shadow')
 m.add('nose_bridge','head',(0,.098,1.482),(.013,.016,.032),'skin')
 m.add('nose_tip','head',(0,.116,1.465),(.017,.012,.011),'skin')
 for side in [-1,1]:
  m.add('ear_'+str(side),'head',(side*.088,.015,1.473),(.013,.02,.026),'skin')
  m.add('ear_inner_'+str(side),'head',(side*.101,.02,1.473),(.003,.009,.012),'skin_shadow')
  m.add('eye_socket_'+str(side),'head',(side*.038,.092,1.501),(.024,.003,.007),'skin_shadow')
  m.add('eye_white_'+str(side),'head',(side*.038,.096,1.501),(.012,.002,.002),'white')
  m.add('eye_pupil_'+str(side),'head',(side*.038,.098,1.501),(.005,.002,.003),'black')
  m.add('eyebrow_'+str(side),'head',(side*.038,.096,1.513),(.026,.004,.004),'hair',.85)
  m.add('cheek_'+str(side),'head',(side*.055,.068,1.462),(.023,.015,.023),'skin')
  a=f'thigh_{side}';s=f'shin_{side}';f=f'foot_{side}'
  m.add(a+'_trouser',a,(0,0,.48),(.091,.090,.55),'trousers',.72)
  m.add(a+'_pocket',a,(side*.078,0,.48),(.027,.074,.17),'pouch',.70)
  m.add(a+'_pocket_flap',a,(side*.103,0,.36),(.009,.073,.034),'vest',.66)
  m.add(s+'_knee_joint',s,(0,0,0),(.080,.076,.07),'trousers',.85)
  m.add(s+'_trouser',s,(0,0,.50),(.073,.073,.54),'trousers',.74)
  for z in [.19,.60,.81]:m.add(s+'_fold'+str(z),s,(0,-.006,z),(.077,.075,.027),'trousers',1.20)
  m.add(s+'_kneepad',s,(0,-.075,.04),(.074,.020,.093),'webbing',.83)
  m.add(f+'_boot',f,(0,.047,.033),(.078,.127,.061),'black',.83)
  m.add(f+'_toe',f,(0,.137,.036),(.074,.036,.033),'webbing',.75)
  m.add(f+'_sole',f,(0,.052,-.013),(.080,.136,.020),'black',.65)
  for j in range(4):m.add(f'_laces{side}_{j}',f,(0,.035+j*.019,.090),(.04,.002,.002),'pouch',.7)
  a=f'upperarm_{side}';f=f'forearm_{side}'
  m.add(a+'_bicep',a,(0,0,.54),(.065,.064,.50),'skin',.9)
  m.add(a+'_sleeve',a,(0,0,.16),(.080,.080,.28),'cloth',.60)
  m.add(a+'_rolled_hem',a,(0,0,.36),(.084,.084,.023),'cloth',.72)
  m.add(f+'_elbow',f,(0,0,0),(.052,.053,.06),'skin')
  m.add(f+'_forearm',f,(0,0,.45),(.052,.052,.56),'skin',.92)
  m.add(f+'_tendon',f,(.019,-.043,.40),(.014,.010,.29),'skin',1.2)
  m.add(f+'_fingerless_glove',f,(0,0,.91),(.055,.053,.126),'black',.82)
  m.add(f'_fingers{side}',f,(0,-.016,1.0),(.051,.045,.08),'skin',1.08)
  if side==-1:
   m.add('wristwatch_band',f,(0,0,.69),(.062,.06,.035),'black',.85)
   m.add('wristwatch',f,(-.01,-.062,.70),(.025,.01,.04),'edge',.65)
 # Reuse only the compact rifle geometry, not the obsolete robotic body.
 armored=b.player_master({**r,'materials':{**r['materials'],'visor':r['materials']['amber']}})
 for part in armored.parts:
  if part['bone']=='gun':m.parts.append(part)
 m.sockets=armored.sockets
 return m

def alien_master(r):
 raw=b.runner_master(r);m=ActionMaster(r);m.parts=raw.parts;m.sockets=raw.sockets
 kind=r['asset_id']
 if kind=='spitter':
  for p in m.parts:
   if p['name']=='thorax':p['matrix']=b.trans((0,.025,.46))@b.scaling((.23,.26,.205))
  for side in [-1,1]:
   for j in range(3):
    pos=(side*(.14+.035*(j%2)),-.22+j*.155,.64)
    m.add(f'acid_sac_{side}_{j}','torso',pos,(.087,.1,.09),'acid',1.05,organic=.06)
    m.add(f'acid_sac_core_{side}_{j}','torso',(pos[0],pos[1]+.015,pos[2]+.073),(.05,.059,.029),'acid_light',1.05)
 elif kind=='charger':
  m.add('reinforced_forehead','head',(0,.405,.563),(.15,.165,.055),'ivory',.7)
  m.curve('head_ram','head',[(0,.50,.55),(0,.63,.56),(0,.73,.44)],[.075,.05,.002],'ivory')
  for side in [-1,1]:
   m.add(f'charge_shoulder_{side}','torso',(side*.225,.15,.52),(.10,.14,.10),'ridge',1.05)
 elif kind in ['brute','brood_warden']:
  for p in m.parts:
   if p['name'] in ['thorax','scapular_mass']:p['matrix']=p['matrix']@b.scaling((1.20,1.05,1.05))
  for j in range(5):
   for side in [-1,1]:
    m.add(f'shell_{side}_{j}','torso',(side*.11,-.26+j*.117,.60),(.144,.076,.083),'shell',.8,rotation=b.rot((0,1,0),side*.33))
    m.curve(f'shell_seam_{side}_{j}','torso',[(side*.02,-.31+j*.117,.64),(side*.14,-.29+j*.117,.68),(side*.25,-.26+j*.117,.57)],[.011,.013,.007],'shell_edge')
  m.add('head_shell','head',(0,.39,.565),(.155,.12,.057),'shell',.78)
  if kind=='brood_warden':
   for side in [-1,1]:
    name='tendril_'+str(side)
    m.curve(name,name,[(side*.19,-.20,.50),(side*.33,-.32,.64),(side*.43,-.17,.76),(side*.48,.09,.66),(side*.45,.25,.42)],[.045,.043,.035,.022,.002],'flesh')
    m.add('warden_gland_'+str(side),'torso',(side*.25,.03,.62),(.072,.19,.072),'acid',1.1)
 return m

def smooth(t):return t*t*(3-2*t)
def around(point,m):return b.trans(point)@m@b.trans(-np.array(point))
def transform_upper(bones,mat):
 for name in ['torso','head','jaw','gun','upperarm_-1','forearm_-1','upperarm_1','forearm_1']:
  if name in bones:bones[name]=mat@bones[name]

def pose(r,t,clip):
 kind=r['asset_id'];human=kind=='player';is_move=clip in ['walk','walk_back','strafe_left','strafe_right','walk_fire','move','charge']
 phase=t%1 if is_move else 0.0
 rr={**r,'gait':dict(r['gait'])}
 if not is_move:rr['gait']={'stride':0.0,'lift':0.0}
 bones=b.player_pose(phase,rr) if human else b.runner_pose(phase,rr)
 if human and clip in ['walk_back','strafe_left','strafe_right']:
  angle={'walk_back':math.pi,'strafe_left':math.pi/2,'strafe_right':-math.pi/2}[clip]
  for side in [-1,1]:
   f,lift,stance=b.footstep(phase+(0 if side==-1 else .5),rr['gait']['stride'],rr['gait']['lift'])
   hip=np.array([side*.125,0,.697+.009*math.cos(4*math.pi*phase)])
   ankle=np.array([side*.133-math.sin(angle)*f,math.cos(angle)*f,.05+lift])
   k=b.knee(hip,ankle,.35,.355,(0,1,0))
   bones[f'thigh_{side}']=b.link(hip,k);bones[f'shin_{side}']=b.link(k,ankle);bones[f'foot_{side}']=b.trans(ankle)@b.rot((0,0,1),angle*.20)
 if clip=='idle':
  wave=math.sin(2*math.pi*t)
  transform_upper(bones,b.trans((0,0,.006*wave)))
  if not human:bones['jaw']=bones['jaw']@around((0,.34,.405),b.rot((1,0,0),.035*wave))
 elif clip in ['shoot','walk_fire']:
  recoil=((t/.22 if t<.22 else 1.0-.94*(t-.22)/.78) if clip=='shoot' else .5+.5*math.sin(4*math.pi*t))
  transform_upper(bones,around((0,0,1.0),b.rot((1,0,0),.025*recoil)))
  for name in ['gun','forearm_1','forearm_-1']:bones[name]=b.trans((0,-.026*recoil,0))@bones[name]
 elif clip=='hit':
  a=.105*(1-t)+.025*t
  transform_upper(bones,around((0,0,1 if human else .45),b.rot((1,0,0),a)))
 elif clip=='death':
  s=smooth(float(np.clip(t,0,1)))
  c=.77 if human else .39;ground=.13 if human else .12
  root=b.trans((0,0,c+(ground-c)*s))@b.rot((0,1,0),s*1.50)@b.trans((0,0,-c))
  for name in bones:bones[name]=root@bones[name]
  for side in [-1,1]:
   names=[f'shin_{side}',f'forearm_{side}'] if human else [f'fore_lower_{side}',f'hind_lower_{side}']
   for name in names:bones[name]=bones[name]@b.rot((1,0,0),s*.35)
 elif clip in ['windup','charge_windup']:
  s=smooth(float(t));transform_upper(bones,b.trans((0,-.02*s,-.035*s))@around((0,0,.45),b.rot((1,0,0),-.18*s)))
  if 'jaw' in bones:bones['jaw']=bones['jaw']@around((0,.34,.405),b.rot((1,0,0),-.20*s))
 elif clip in ['attack','acid_attack','pulse_attack','phase_transition','recovery']:
  s=((t/.32 if t<.32 else 1.0-.93*(t-.32)/.68) if clip!='recovery' else 1-t)
  transform_upper(bones,b.trans((0,.035*s,.014*s))@around((0,0,.45),b.rot((1,0,0),.08*s)))
  if 'jaw' in bones:bones['jaw']=bones['jaw']@around((0,.34,.405),b.rot((1,0,0),-.30*s))
  if not human and clip in ['attack','pulse_attack','phase_transition']:
   for side in [-1,1]:
    for name in [f'fore_upper_{side}',f'fore_lower_{side}',f'fore_foot_{side}']:
     bones[name]=around((side*.215,.17,.49),b.rot((1,0,0),-.38*s))@bones[name]
 if kind=='brood_warden':
  for side in [-1,1]:
   amplitude=.16 if clip in ['phase_transition','pulse_attack'] else .045
   wave=math.sin(2*math.pi*t+side*.7) if clip not in ['death','hit'] else float(t)*.5
   bones['tendril_'+str(side)]=bones['torso']@around((side*.19,-.20,.5),b.rot((0,1,0),side*amplitude*wave))
 return bones

def build(kind):
 r=recipe(kind);return human_master(r) if kind=='player' else alien_master(r)

def render_family(kind,pack,ss=3,only=None):
 m=build(kind);r=m.recipe;folder=pack/'families'/kind
 _,w,actors=b.vtk_scene(m,r['cell'],r['pivot'],ss)
 sockets={};info={}
 clips=CLIPS[kind] if only is None else {only:CLIPS[kind][only]}
 for clip,(n,fps,loop) in clips.items():
  m.clip=clip
  for d in DIRS:
   for i in range(n):
    t=i/n if loop else i/max(1,n-1)
    im,sc=b.render(m,d,t,w,actors,ss);out=folder/'frames'/clip/d/f'{i:03d}.png';out.parent.mkdir(parents=True,exist_ok=True);im.save(out)
    sockets[out.relative_to(pack).as_posix()]=sc
  info[clip]={'frames':n,'fps':fps,'loop':loop}
  print(kind,clip,n*4,'frames',flush=True)
 w.Finalize()
 (folder/'source').mkdir(exist_ok=True,parents=True)
 (folder/'source/rig.json').write_text(json.dumps(r,indent=2)+'\n')
 (folder/'source/sockets.json').write_text(json.dumps(sockets,indent=2)+'\n')
 (folder/'source/animations.json').write_text(json.dumps(info,indent=2)+'\n')
 return m,info

def main():
 p=argparse.ArgumentParser();p.add_argument('--pack',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--assets',nargs='+',default=list(CLIPS));p.add_argument('--clip');p.add_argument('--ss',type=int,default=3);a=p.parse_args()
 for k in a.assets:render_family(k,a.pack,a.ss,a.clip)
if __name__=='__main__':main()
