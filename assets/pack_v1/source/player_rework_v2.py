#!/usr/bin/env python3
"""Player v2: one fully modeled, shoulder-mounted human, eight actual views.
Offline review authoring. Never reads/transforms or overwrites the selected player.
Uses the existing fixed-camera mesh renderer; gameplay remains 2D.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import render_motion as b

DIRS = ['e','se','s','sw','w','nw','n','ne']
CELL, PIVOT = (128,128), (64,110)
CLIPS = {'ready':(4,6,True),'walk':(8,12,True),'fire':(4,18,False)}
# This initial batch intentionally stops before hit, death and strafing production.
R = {
 'asset_id':'player_rework_v2', 'cell':list(CELL),'pivot':list(PIVOT),
 'physical_scale':.84,'clip':'walk','frames':8,'fps':12,
 'materials':{
  'shirt':{'hex':'303936','wear':.20,'specular':.025},
  'cloth_edge':{'hex':'49514A','wear':.17,'specular':.025},
  'vest':{'hex':'4A5140','wear':.24,'specular':.025},
  'webbing':{'hex':'77705A','wear':.18,'specular':.025},
  'pants':{'hex':'4C5140','wear':.23,'specular':.025},
  'crease':{'hex':'343B31','wear':.16,'specular':.02},
  'skin':{'hex':'A87551','wear':.10,'specular':.045},
  'skin_light':{'hex':'BA8B62','wear':.07,'specular':.04},
  'skin_dark':{'hex':'694A36','wear':.08,'specular':.02},
  'hair':{'hex':'302A24','wear':.13,'specular':.03},
  'hair_edge':{'hex':'48392C','wear':.16,'specular':.04},
  'eye':{'hex':'241E19','wear':0.,'specular':.10},
  'boot':{'hex':'272D28','wear':.20,'specular':.02},
  'metal':{'hex':'4C5351','wear':.20,'specular':.12},
  'gun':{'hex':'272D2C','wear':.14,'specular':.085},
  'gun_edge':{'hex':'69716B','wear':.15,'specular':.10}
 }
}
BUTT = np.array([.175,.062,1.405])
MUZZLE_LOCAL = np.array([0.,.745,.023,1.])
TRIGGER_LOCAL = np.array([0.,.176,-.082,1.])
SUPPORT_LOCAL = np.array([-.013,.298,-.038,1.])

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def around(p,m): return b.trans(p)@m@b.trans(-np.asarray(p))
def root_angle(screen_angle):
    x,y=math.cos(screen_angle), math.sin(screen_angle)
    v=x*b.RIGHT[:2]-2*y*np.array([-.70710678118655,.70710678118655])
    return math.atan2(-v[0],v[1])

class Survivor(b.Master):
 def __init__(self):
  super().__init__(json.loads(json.dumps(R)));self.clip='ready'
  # Cloth-contoured trunk, not independent hard armour blocks.
  self.loft('shirt_body','torso',[
   (.83,.14,.10,0),(.92,.157,.112,0),(1.10,.168,.113,.022),
   (1.27,.209,.128,.030),(1.37,.206,.101,.015),(1.405,.135,.075,.010)],'shirt')
  self.loft('fabric_vest','torso',[
   (.94,.166,.125,.023),(1.07,.174,.140,.026),(1.23,.192,.143,.030),
   (1.335,.184,.118,.035),(1.379,.119,.083,.024)],'vest')
  self.add('pelvis_fabric','pelvis',(0,-.012,.808),(.174,.129,.137),'pants',.78)
  self.add('belt','pelvis',(0,.003,.90),(.18,.127,.026),'boot',.42)
  self.add('buckle','pelvis',(.022,.136,.902),(.025,.012,.020),'metal',.36)
  # Flat stitched straps and pouches sewn to fabric, not robot ribs.
  for s in [-1,1]:
   self.curve('shoulder_strap'+str(s),'torso',[(s*.122,-.102,1.30),(s*.142,-.072,1.372),(s*.126,.066,1.382),(s*.125,.135,1.29)],[.017,.021,.02,.017],'webbing')
   self.add('strap_buckle'+str(s),'torso',(s*.128,.148,1.291),(.023,.009,.022),'metal',.45)
   for k in range(2):
    self.add(f'mag_pouch{s}_{k}','torso',(s*(.049+.07*k),.167,1.077),(.028,.024,.078),'vest',.52)
    self.add(f'mag_flap{s}_{k}','torso',(s*(.049+.07*k),.194,1.125),(.027,.008,.026),'webbing',.52)
   self.add('belt_pouch'+str(s),'pelvis',(s*.146,.128,.835),(.042,.033,.052),'vest',.52)
  self.curve('vest_seam','torso',[(0,.176,.985),(0,.180,1.18),(0,.149,1.32)],[.006,.007,.004],'crease')
  for z in [1.16,1.205,1.25]:
   self.curve('stitched_webbing'+str(z),'torso',[(-.153,.150,z),(-.07,.175,z),(0,.18,z),(.07,.175,z),(.153,.150,z)],[.005]*5,'cloth_edge')
  self.add('rear_fabric_panel','torso',(0,-.133,1.16),(.15,.026,.16),'vest',.7)
  self.add('collar','torso',(0,.017,1.408),(.083,.075,.025),'cloth_edge',.8)
  self._head()
  for s in [-1,1]:
   thigh='thigh_'+str(s);shin='shin_'+str(s);foot='foot_'+str(s)
   self.add('trouser_thigh'+str(s),thigh,(0,0,.46),(.098,.089,.51),'pants',.84)
   self.add('cargo_pocket'+str(s),thigh,(s*.078,.017,.43),(.028,.054,.15),'vest',.54)
   self.add('cargo_flap'+str(s),thigh,(s*.083,.020,.33),(.030,.059,.036),'cloth_edge',.60)
   self.add('trouser_calf'+str(s),shin,(0,0,.46),(.073,.074,.53),'pants',.9)
   self.add('soft_knee'+str(s),shin,(0,-.055,.045),(.07,.031,.13),'crease',.8)
   for k in range(3):
    z=.20+k*.24
    self.curve(f'calf_fold{s}_{k}',shin,[(-.054,-.048,z-.03),(0,-.080,z),(.054,-.040,z+.027)],[.006,.009,.003],'cloth_edge')
   self.add('boot_sole'+str(s),foot,(0,.044,-.058),(.075,.145,.023),'boot',.5)
   self.add('leather_boot'+str(s),foot,(0,.04,-.012),(.073,.139,.055),'boot',.66)
   self.add('boot_collar'+str(s),foot,(0,-.012,.065),(.068,.072,.085),'boot',.70)
   self.add('toecap'+str(s),foot,(0,.131,-.017),(.070,.038,.040),'cloth_edge',.7)
   for j in range(4):
    y=.021+j*.019
    self.curve(f'lace{s}_{j}',foot,[(-.040,y,.044),(.036,y+.012,.044)],[.003,.003],'webbing')
   upper='upperarm_'+str(s);fore='forearm_'+str(s);hand='hand_'+str(s)
   self.add('upperarm_skin'+str(s),upper,(0,0,.55),(.064,.061,.50),'skin')
   self.add('rolled_sleeve'+str(s),upper,(0,0,.24),(.079,.073,.35),'shirt',.86)
   self.add('sleeve_cuff'+str(s),upper,(0,0,.47),(.074,.070,.044),'cloth_edge',.6)
   self.add('forearm_skin'+str(s),fore,(0,0,.45),(.051,.047,.53),'skin',1.)
   self.curve('forearm_tendon'+str(s),fore,[(-.024,-.045,.24),(-.018,-.047,.6),(-.007,-.024,.92)],[.004,.005,.002],'skin_light')
   self.add('glove'+str(s),hand,(0,0,0),(.041,.038,.054),'boot',.77)
   self.add('thumb'+str(s),hand,(-s*.032,.014,.014),(.020,.025,.025),'skin_dark')
  self._rifle()
  self.sockets={
   'muzzle':('gun',MUZZLE_LOCAL),
   'stock':('gun',np.array([0,0,0,1.])),
   'trigger_grip':('gun',TRIGGER_LOCAL),
   'support_grip':('gun',SUPPORT_LOCAL),
   'shoulder':('torso',np.r_[BUTT,1.]),
   'eye':('head',np.array([.064,.086,1.615,1.])),
  }

 def loft(self,name,bone,rings,material):
  vertices=[];faces=[];nu=32
  for z,rx,ry,cy in rings:
   for i in range(nu):
    t=i*math.tau/nu;vertices.append((math.cos(t)*rx,math.sin(t)*ry+cy,z))
  for j in range(len(rings)-1):
   for i in range(nu):
    aa=j*nu+i;bb=j*nu+(i+1)%nu;cc=bb+nu;dd=aa+nu
    faces.extend([(aa,bb,dd),(bb,cc,dd)])
  self._part(name,bone,np.array(vertices),np.array(faces,dtype=np.uint32),np.eye(4),material)

 def _head(self):
  self.add('neck','head',(0,.018,1.433),(.059,.055,.074),'skin_dark')
  self.loft('face','head',[
    (1.476,.048,.057,.035),(1.51,.075,.069,.030),
    (1.55,.100,.079,.020),(1.60,.101,.084,.012),
    (1.665,.097,.080,.002),(1.700,.073,.060,-.005)],'skin')
  self.add('cranium','head',(0,-.006,1.623),(.103,.092,.126),'skin',1.)
  self.add('jaw','head',(0,.033,1.511),(.075,.061,.039),'skin_dark',.9)
  self.add('chin','head',(0,.077,1.502),(.042,.021,.023),'skin')
  self.add('nose_bridge','head',(0,.091,1.593),(.018,.024,.045),'skin_light',.7)
  self.add('nose_tip','head',(0,.113,1.56),(.022,.022,.017),'skin_light')
  self.curve('mouth','head',[(-.028,.094,1.525),(0,.099,1.52),(.028,.094,1.525)],[.003,.004,.003],'skin_dark')
  for s in [-1,1]:
   self.add('ear'+str(s),'head',(s*.103,-.004,1.584),(.016,.025,.037),'skin')
   self.add('ear_inner'+str(s),'head',(s*.113,.009,1.581),(.005,.012,.021),'skin_dark')
   self.add('cheek'+str(s),'head',(s*.067,.068,1.556),(.030,.030,.030),'skin_light')
   self.add('eye_socket'+str(s),'head',(s*.046,.085,1.609),(.026,.010,.012),'skin_dark',.7)
   self.add('eye'+str(s),'head',(s*.046,.092,1.608),(.011,.004,.005),'eye',.8)
   self.curve('brow'+str(s),'head',[(s*.02,.096,1.628),(s*.047,.092,1.631),(s*.077,.078,1.624)],[.008,.009,.004],'hair')
  # Hair cap follows the scalp, not a helmet or visor.
  self.loft('cropped_hair','head',[(1.631,.106,.096,-.014),(1.677,.108,.096,-.012),(1.722,.088,.082,-.010),(1.757,.040,.046,-.010),(1.766,.002,.002,-.010)],'hair')
  for i in range(11):
   x=-.085+i*.016
   height=1.736+.022*(1-(x/.10)**2)
   self.curve('hair_lock'+str(i),'head',[(x,-.077,height-.036),(x+.008,-.028,height),(x+.015,.032,height-.009),(x+.02,.059,height-.023)],[.008,.010,.008,.002],'hair_edge' if i%3==0 else 'hair')
  for s in [-1,1]:
   self.add('sideburn'+str(s),'head',(s*.091,.016,1.638),(.010,.025,.030),'hair',.65)

 def _rifle(self):
  self.add('stock_pad','gun',(0,.012,-.003),(.026,.014,.065),'boot',.48)
  self.add('stock','gun',(0,.071,.014),(.025,.059,.034),'gun',.48)
  self.add('receiver','gun',(0,.22,.015),(.027,.095,.038),'gun',.4)
  self.add('handguard','gun',(0,.399,.018),(.028,.095,.031),'gun',.44)
  self.add('barrel','gun',(0,.608,.023),(.010,.137,.010),'metal',1.)
  # Above cylinder dimensions are orientation-dependent; explicit thin bore shell.
  self.curve('bore','gun',[(0,.487,.023),(0,.745,.023)],[.010,.010],'gun')
  self.add('muzzle_brake','gun',(0,.723,.023),(.016,.022,.017),'metal',.6)
  self.add('magazine','gun',(0,.273,-.055),(.023,.036,.060),'gun',.42,rotation=b.rot((1,0,0),-.14))
  self.add('pistol_grip','gun',(0,.171,-.066),(.023,.025,.051),'gun',.5,rotation=b.rot((1,0,0),-.2))
  self.curve('trigger_guard','gun',[(0,.19,-.025),(0,.211,-.037),(0,.199,-.067),(0,.174,-.07)],[.004]*4,'gun_edge')
  self.add('sight_base','gun',(0,.226,.062),(.013,.033,.008),'metal',.45)
  self.add('rear_sight','gun',(0,.213,.079),(.017,.016,.018),'gun',.42)
  self.add('front_sight','gun',(0,.527,.055),(.01,.007,.028),'gun',.5)
  for i in range(6):
   y=.318+i*.024
   self.add('guard_slot'+str(i),'gun',(.029,y,.016),(.003,.008,.009),'boot',.45)
  self.add('charging_handle','gun',(.034,.151,.039),(.014,.010,.008),'gun_edge',.5)
  self.add('ejection_port','gun',(.028,.237,.024),(.003,.023,.012),'boot',.45)

 def pose(self,t):
  walking=self.clip=='walk'
  if self.clip not in CLIPS:raise ValueError(self.clip)
  phase=float(t)%1
  kick=float(np.interp(t,[0,1/3,2/3,1],[0.,1.,.35,0.])) if self.clip=='fire' else 0.
  breath=.0018*math.sin(2*math.pi*t) if self.clip=='ready' else 0.
  bob=.0035*math.cos(4*math.pi*phase) if walking else 0.
  # Shoulders, head and gun absorb recoil together around the upper chest.
  upper=b.trans((0,.019,bob+breath))@around((0,0,1.03),b.rot((1,0,0),-.045+.012*kick))
  bones={'torso':upper,'pelvis':b.trans((0,0,bob)),
         'head':upper@around((0,.025,1.47),b.rot((1,0,0),-.11))@b.trans((.029,.009,-.006))}
  gun=upper@b.trans(BUTT);bones['gun']=gun
  for s in [-1,1]:
   offset,raise_z,stance=b.footstep(phase+(0 if s==-1 else .5),.26,.048) if walking else (0.,0.,True)
   ankle=np.array([s*.133,(.071 if s==-1 else -.075)+offset,.078+raise_z])
   hip=np.array([s*.102,-.008,.805+bob])
   knee=b.knee(hip,ankle,.391,.405,(0,1,0))
   bones['thigh_'+str(s)]=b.link(hip,knee);bones['shin_'+str(s)]=b.link(knee,ankle)
   bones['foot_'+str(s)]=b.trans(ankle)
   shoulder=(upper@np.array([s*.212,.003,1.377,1.]))[:3]
   hand=(gun@(TRIGGER_LOCAL if s==1 else SUPPORT_LOCAL))[:3]
   elbow=b.knee(shoulder,hand,.277,.263,(s*.8,-.18,-.72))
   bones['upperarm_'+str(s)]=b.link(shoulder,elbow)
   bones['forearm_'+str(s)]=b.link(elbow,hand)
   bones['hand_'+str(s)]=b.trans(hand)@b.rot((0,1,0),-.23 if s==1 else .70)
  return bones

def build(out:Path,clips=None,ss=3):
 if out.exists(): raise ValueError('Refusing to overwrite existing artwork')
 out.mkdir(parents=True);model=Survivor()
 _,window,actors=b.vtk_scene(model,CELL,PIVOT,ss)
 selected=list(CLIPS) if clips is None else clips
 meta={'asset_id':'player_rework_v2','status':'review','owner_approval':None,
       'cell':list(CELL),'pivot':list(PIVOT),'directions':DIRS,
       'clips':{c:{'frames':CLIPS[c][0],'fps':CLIPS[c][1],'loop':CLIPS[c][2]} for c in selected},
       'frames':[],'source_sha256':sha(__file__),'renderer_sha256':sha(b.__file__),
       'missing':['hit','death','strafe','reverse','independent moving recoil'],
       'authorship':'New parametric human, not transformed old frame art. Face likeness and finish need owner review.'}
 for clip in selected:
  count,fps,loop=CLIPS[clip];model.clip=clip
  for j,d in enumerate(DIRS):
   b.ANGLES[d]=root_angle(j*math.tau/8)
   for i in range(count):
    t=i/count if loop else i/max(1,count-1)
    im,sockets=b.render(model,d,t,window,actors,ss)
    box=im.getchannel('A').getbbox()
    if not box or box[0]<2 or box[1]<2 or box[2]>126 or box[3]>126:raise ValueError(f'Clipped/empty {clip}/{d}/{i}: {box}')
    p=out/'frames'/clip/d/f'{i:03d}.png';p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
    meta['frames'].append({'clip':clip,'direction':d,'frame':i,'path':p.relative_to(out).as_posix(),'sha256':sha(p),'sockets':sockets})
   print(clip,d,flush=True)
 window.Finalize();model.clip='walk'
 source=out/'source';source.mkdir()
 b.export_glb(model,source/'master.glb')
 runtime=out/'runtime';runtime.mkdir()
 atlas=Image.new('RGBA',(1584,1452)) # 12 x 11 padded 132px slots, no >2048 dimension
 for i,f in enumerate(meta['frames']):
  x=(i%12)*132+2;y=(i//12)*132+2
  atlas.paste(Image.open(out/f['path']),(x,y));f['region']=[x,y,128,128]
 atlas.save(runtime/'atlas.png',optimize=True)
 for p in [out/'manifest.json',runtime/'index.json']:p.write_text(json.dumps(meta,indent=2)+'\n')
 (source/'recipe.json').write_text(json.dumps(R,indent=2)+'\n')
 return meta

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
 p.add_argument('--ready-only',action='store_true');p.add_argument('--ss',type=int,default=3,choices=range(1,5))
 a=p.parse_args();build(a.out,['ready'] if a.ready_only else None,a.ss)
