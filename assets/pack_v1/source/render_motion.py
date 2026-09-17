#!/usr/bin/env python3
"""Original articulated sprite masters. Offline authoring only; no game code.
VTK renders consistent geometry; PNGs are not transformed still illustrations.
"""
from __future__ import annotations
import argparse, hashlib, json, math, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

PACK=Path(__file__).resolve().parents[1]
PPU=math.sqrt(48**2+48**2)
RIGHT=np.array([1,1,0.0])/math.sqrt(2)
UP=np.array([-.5,.5,math.sqrt(1.5)])/math.sqrt(2)
EYE=np.array([math.sqrt(.375),-math.sqrt(.375),.5])
ANGLES={'e':-math.pi/4,'s':-3*math.pi/4,'w':3*math.pi/4,'n':math.pi/4}

def unit(v):
    v=np.asarray(v,dtype=float); return v/max(np.linalg.norm(v),1e-9)
def trans(p=(0,0,0)):
    m=np.eye(4);m[:3,3]=p;return m
def rot(axis,a):
    x,y,z=unit(axis);c=math.cos(a);s=math.sin(a);t=1-c
    m=np.eye(4);m[:3,:3]=[[t*x*x+c,t*x*y-s*z,t*x*z+s*y],[t*x*y+s*z,t*y*y+c,t*y*z-s*x],[t*x*z-s*y,t*y*z+s*x,t*z*z+c]];return m
def scaling(p):
    return np.diag([*p,1.0])
def link(a,b):
    a=np.array(a);b=np.array(b);z=unit(b-a);ref=np.array([1.,0,0])
    if abs(z@ref)>.94:ref=np.array([0.,1,0])
    x=unit(ref-z*(z@ref));y=np.cross(z,x)
    m=np.eye(4);m[:3,:3]=np.stack([x,y,b-a],axis=1);m[:3,3]=a;return m

def knee(hip,foot,l1,l2,bend):
    hip=np.array(hip);foot=np.array(foot);d=foot-hip;dist=np.linalg.norm(d);z=unit(d)
    if dist>l1+l2 or dist<abs(l1-l2):raise ValueError('IK target unreachable')
    along=(l1*l1-l2*l2+dist*dist)/(2*dist)
    bend=unit(np.array(bend)-z*np.dot(bend,z))
    return hip+z*along+bend*math.sqrt(max(0,l1*l1-along*along))

def footstep(phase,stride,lift,stance=.6):
    t=phase%1
    if t<stance:return stride*(.5-t/stance),0.0,True
    t=(t-stance)/(1-stance)
    return stride*(-.5+t),lift*math.sin(math.pi*t)**1.3,False

# Meshes have constant topology and constant source-bound material colours.
def surface(n=1.0,organic=0.0,nu=28,nv=18):
    vertices=[];faces=[]
    for j in range(nv+1):
        lat=-math.pi/2+math.pi*j/nv
        for i in range(nu):
            lon=2*math.pi*i/nu
            f=lambda q:math.copysign(abs(q)**n,q)
            x=f(math.cos(lat))*f(math.cos(lon));y=f(math.cos(lat))*f(math.sin(lon));z=f(math.sin(lat))
            ripple=1+organic*math.cos(lon*5+.7)*math.cos(lat*4)*math.cos(lat)**2
            vertices.append((x*ripple,y*ripple,z))
    for j in range(nv):
        for i in range(nu):
            a=j*nu+i;b=j*nu+(i+1)%nu;c=b+nu;d=a+nu
            faces.extend([(a,b,d),(b,c,d)])
    return np.array(vertices,dtype=float),np.array(faces,dtype=np.uint32)

def tapered_curve(points,radii,segments=10):
    # One continuous tapered mesh; no framewise silhouette invention.
    points=np.array(points,dtype=float);vs=[];fs=[]
    for j,p in enumerate(points):
        tangent=unit(points[min(j+1,len(points)-1)]-points[max(0,j-1)])
        axis=np.array([1.,0,0]) if abs(tangent[0])<.9 else np.array([0.,1,0])
        u=unit(np.cross(tangent,axis));v=np.cross(tangent,u)
        for k in range(segments):
            a=2*math.pi*k/segments;vs.append(p+radii[j]*(math.cos(a)*u+math.sin(a)*v))
        if j:
            for k in range(segments):
                a=(j-1)*segments+k;b=(j-1)*segments+(k+1)%segments;c=b+segments;d=a+segments
                fs.extend([(a,b,d),(b,c,d)])
    return np.array(vs),np.array(fs,dtype=np.uint32)

class Master:
    def __init__(self,recipe):self.recipe=recipe;self.parts=[];self.sockets={}
    def add(self,name,bone,center,scale,material,shape=1.,organic=0.,rotation=None):
        v,f=surface(shape,organic)
        mat=trans(center)@(np.eye(4) if rotation is None else rotation)@scaling(scale)
        self._part(name,bone,v,f,mat,material)
    def curve(self,name,bone,points,radii,material):
        v,f=tapered_curve(points,radii);self._part(name,bone,v,f,np.eye(4),material)
    def _part(self,name,bone,v,f,mat,material):
        spec=self.recipe['materials'][material];rgb=np.array([int(spec['hex'][i:i+2],16) for i in (0,2,4)])/255
        # Object-space wear; static under animation and actor rotation.
        noise=np.sin(v@np.array([37.1,91.7,53.2])+len(self.parts)*2.381)*np.sin(v@np.array([73.4,17.3,41.9]))
        streak=np.sin(v[:,2]*45+v[:,0]*11)*.35
        tint=1+spec.get('wear',0)*(.7*noise+streak)
        colors=np.clip(rgb[None,:]*tint[:,None],0,1)
        self.parts.append(dict(name=name,bone=bone,vertices=v,faces=f,matrix=mat,colors=colors,material=material))
    def pose(self,t):return player_pose(t,self.recipe) if self.recipe['asset_id']=='player' else runner_pose(t,self.recipe)


def player_master(r):
    m=Master(r)
    # Cloth undersuit, split cuirass, utility belt and backpack all share torso rig.
    m.add('undersuit','torso',(0,0,1.05),(.23,.13,.27),'cloth',.85)
    m.add('pelvis','pelvis',(0,0,.76),(.225,.13,.11),'cloth',.65)
    m.add('cuirass','torso',(0,.04,1.16),(.238,.157,.213),'steel',.56)
    m.add('chest_left','torso',(-.112,.185,1.19),(.101,.025,.125),'plate',.55,rotation=rot((0,1,0),-.08))
    m.add('chest_right','torso',(.112,.185,1.19),(.101,.025,.125),'plate',.55,rotation=rot((0,1,0),.08))
    m.add('sternum','torso',(0,.192,1.19),(.025,.025,.139),'edge',.35)
    for z in [1.02,.965,.91]:m.add('abdomen_'+str(z),'torso',(0,.135,z),(.162,.037,.032),'steel',.4)
    for side in [-1,1]:
        for j in range(3):
            m.add(f'breast_rivet_{side}_{j}','torso',(side*.19,.198,1.115+j*.065),(.007,.008,.007),'edge')
        m.add(f'clavicle_{side}','torso',(side*.115,.155,1.35),(.106,.028,.024),'edge',.35)
        m.add(f'waist_pouch_{side}','pelvis',(side*.16,.125,.8),(.07,.055,.075),'pouch',.35)
        m.add(f'pouch_clasp_{side}','pelvis',(side*.16,.182,.81),(.018,.008,.018),'edge',.4)
    m.add('belt','pelvis',(0,0,.82),(.24,.139,.04),'black',.4)
    m.add('belt_buckle','pelvis',(0,.147,.82),(.044,.017,.029),'edge',.3)
    m.add('backpack','torso',(0,-.195,1.145),(.167,.09,.205),'steel',.3)
    m.add('backpack_spine','torso',(0,-.29,1.16),(.05,.02,.165),'plate',.3)
    for z in [1.02,1.08,1.14,1.20,1.26]:m.add('pack_vent_'+str(z),'torso',(0,-.313,z),(.079,.007,.009),'black',.3)
    for x in [-.12,.12]:m.add('pack_rail_'+str(x),'torso',(x,-.289,1.15),(.013,.018,.163),'edge',.35)
    m.add('pack_warning_tab','torso',(.08,-.295,1.295),(.045,.01,.017),'amber',.4)
    # Helmet is consistently modeled, including genuine rear plates.
    m.add('neck','head',(0,0,1.405),(.08,.075,.065),'black')
    m.add('helmet_shell','head',(0,.017,1.505),(.15,.145,.155),'plate',.87)
    m.add('visor_black_seal','head',(0,.133,1.52),(.133,.038,.049),'black',.6)
    m.add('amber_visor','head',(0,.158,1.529),(.117,.024,.023),'visor',.45)
    m.add('lower_mask','head',(0,.151,1.45),(.078,.043,.049),'steel',.48)
    for x in [-.035,0,.035]:m.add('respirator_'+str(x),'head',(x,.195,1.445),(.009,.009,.028),'black',.4)
    m.add('crown_ridge','head',(0,.0,1.651),(.032,.105,.011),'edge',.4)
    m.add('rear_helmet_plate','head',(0,-.127,1.512),(.096,.025,.065),'steel',.4)
    for side in [-1,1]:
        m.add(f'ear_housing_{side}','head',(side*.146,0,1.5),(.025,.062,.064),'steel',.5)
        m.add(f'ear_disk_{side}','head',(side*.171,0,1.5),(.008,.035,.037),'edge')
        # Local Z on a segment runs from proximal joint to distal joint.
        a='thigh_'+str(side);b='shin_'+str(side);f='foot_'+str(side)
        m.add(a+'_suit',a,(0,0,.50),(.106,.10,.48),'cloth')
        m.add(a+'_armor',a,(0,-.055,.48),(.09,.055,.32),'steel',.4)
        m.add(a+'_seam',a,(0,-.109,.48),(.008,.005,.20),'edge',.4)
        m.add(b+'_joint',b,(0,0,0),(.105,.097,.12),'black')
        m.add(b+'_kneecap',b,(0,-.078,.06),(.095,.045,.13),'plate',.42)
        m.add(b+'_armor',b,(0,0,.51),(.085,.083,.41),'steel',.42)
        m.add(b+'_ridge',b,(0,-.081,.53),(.034,.017,.26),'edge',.35)
        for z in [.36,.77]:m.add(b+'_strap'+str(z),b,(0,0,z),(.091,.09,.035),'black',.4)
        m.add(f+'_sole',f,(0,.042,-.017),(.096,.157,.026),'black',.55)
        m.add(f+'_boot',f,(0,.035,.025),(.089,.137,.059),'steel',.55)
        m.add(f+'_toe',f,(0,.13,.029),(.087,.044,.04),'plate',.55)
        m.add(f'hip_guard_{side}','pelvis',(side*.229,0,.76),(.037,.126,.13),'steel',.5)
        a='upperarm_'+str(side);b='forearm_'+str(side)
        m.add(a+'_suit',a,(0,0,.55),(.084,.082,.48),'cloth')
        m.add(a+'_shoulder',a,(0,0,.12),(.131,.127,.26),'plate',.66)
        m.add(a+'_shoulder_stripe',a,(.135,0,.12),(.009,.06,.055),'amber',.35)
        m.add(b+'_joint',b,(0,0,0),(.08,.078,.11),'black')
        m.add(b+'_brace',b,(0,0,.40),(.09,.081,.32),'steel',.45)
        m.add(b+'_hand',b,(0,0,.9),(.073,.068,.21),'black',.55)
        m.add(b+'_knuckles',b,(0,-.067,.86),(.062,.017,.07),'edge',.4)
    # Compact rifle, separate muzzle socket; no flash baked into frame.
    m.add('rifle_receiver','gun',(0,.05,0),(.045,.155,.048),'steel',.25)
    m.add('rifle_upper','gun',(0,.12,.049),(.036,.155,.023),'plate',.28)
    m.add('rifle_stock','gun',(0,-.17,-.005),(.047,.088,.042),'black',.28)
    m.add('rifle_magazine','gun',(0,.04,-.092),(.031,.056,.059),'steel',.35,rotation=rot((1,0,0),.18))
    m.add('rifle_grip','gun',(0,-.079,-.076),(.026,.027,.05),'black',.3)
    m.add('rifle_handguard','gun',(0,.265,.0),(.04,.08,.039),'black',.35)
    m.add('rifle_barrel','gun',(0,.392,.014),(.020,.081,.02),'edge')
    m.add('rifle_muzzle','gun',(0,.458,.013),(.03,.025,.029),'steel',.4)
    m.add('rifle_bore','gun',(0,.483,.013),(.018,.002,.017),'black')
    m.add('sight_base','gun',(0,.01,.085),(.023,.064,.012),'black',.3)
    m.add('optic','gun',(0,.02,.108),(.021,.062,.021),'steel')
    for j in range(5):m.add('rifle_cooling_'+str(j),'gun',(.043,.15+j*.025,.011),(.005,.007,.025),'black',.3)
    m.add('rifle_mark','gun',(.047,.03,.005),(.004,.036,.012),'amber',.3)
    m.sockets['muzzle']=('gun',np.array([0,.485,.013,1.]))
    return m

def player_pose(t,r):
    t=t%1;g=r['gait'];bob=.009*math.cos(4*math.pi*t);lean=.055
    torso=trans((0,lean,bob))@trans((0,0,1.0))@rot((0,0,1),.025*math.sin(2*math.pi*t))@trans((0,0,-1.0))
    bones={'torso':torso,'pelvis':trans((0,0,bob)),'head':torso@rot((0,0,1),-.012*math.sin(2*math.pi*t))}
    for side in [-1,1]:
        f,lift,stance=footstep(t+(0 if side==-1 else .5),g['stride'],g['lift'])
        hip=np.array([side*.125,0,.697+bob]);ankle=np.array([side*.133,f,.05+lift])
        k=knee(hip,ankle,.35,.355,(0,1,0))
        bones['thigh_'+str(side)]=link(hip,k);bones['shin_'+str(side)]=link(k,ankle)
        bones['foot_'+str(side)]=trans(ankle)@rot((1,0,0),-.20*math.sin(math.pi*((t+(0 if side==-1 else .5))%1))) if not stance else trans(ankle)
        shoulder=np.array([side*.27,.006,1.30]);elbow=np.array([side*.30,.11,1.065]);hand=np.array([.076 if side==1 else .015,.25 if side==1 else .49,1.10])
        bones['upperarm_'+str(side)]=torso@link(shoulder,elbow)
        bones['forearm_'+str(side)]=torso@link(elbow,hand)
    bones['gun']=torso@trans((.076,.276,1.115))
    return bones


def runner_master(r):
    m=Master(r)
    m.add('thorax','torso',(0,.01,.47),(.205,.25,.182),'flesh',1,organic=.035)
    m.add('abdomen','torso',(0,-.23,.40),(.145,.175,.115),'dark_flesh',1,organic=.04)
    m.add('scapular_mass','torso',(0,.155,.505),(.247,.126,.144),'flesh',1,organic=.035)
    # Flesh remains organic, with tendons/ridges rather than metal plates.
    for side in [-1,1]:
        for j in range(4):
            y=-.15+j*.076
            m.add(f'rib_{side}_{j}','torso',(side*(.15+(.035 if j>0 else 0)),y,.479),(.045,.026,.115),'muscle',1,rotation=rot((0,1,0),side*.38))
        m.curve('lateral_tendon_'+str(side),'torso',[(side*.13,-.32,.44),(side*.2,-.1,.52),(side*.225,.14,.56)], [.014,.018,.01],'tendon')
    for j in range(7):
        y=-.34+j*.085;z=.44+.17*math.sin((j+1)/8*math.pi)
        m.add('vertebra_'+str(j),'torso',(0,y,z),(.047,.044,.035),'ivory',.7)
        m.curve('dorsal_spine_'+str(j),'torso',[(0,y,z),(0,y-.027,z+.07),(0,y-.10,z+.10),(0,y-.16,z+.08)],[.035,.029,.015,.001],'ivory')
    m.add('head_cranium','head',(0,.342,.48),(.135,.173,.107),'flesh',1,organic=.025)
    m.add('brow_ridge','head',(0,.413,.536),(.132,.102,.051),'ridge',.75)
    m.add('mouth_cavity','head',(0,.490,.439),(.114,.082,.067),'mouth')
    m.add('snout_bone','head',(0,.510,.513),(.04,.083,.027),'ivory',.75)
    m.add('jaw','jaw',(0,.475,.396),(.109,.139,.029),'dark_flesh',1,organic=.03)
    for side in [-1,1]:
        m.add('eye_socket_'+str(side),'head',(side*.112,.41,.517),(.029,.032,.025),'mouth')
        m.add('eye_'+str(side),'head',(side*.131,.45,.527),(.012,.023,.013),'eye')
        m.curve('temple_horn_'+str(side),'head',[(side*.097,.291,.55),(side*.16,.24,.626),(side*.21,.145,.666)],[.033,.022,.0008],'ivory')
        for j in range(4):
            x=side*(.022+j*.021);y=.505-.018*j
            m.curve(f'tooth_{side}_{j}','head',[(x,y,.481),(x,y+.006,.448),(x,y+.015,.436)],[.009,.006,.0005],'ivory')
    for side in [-1,1]:
        for kind in ['hind','fore']:
            a=f'{kind}_upper_{side}';b=f'{kind}_lower_{side}';f=f'{kind}_foot_{side}'
            radius=.086 if kind=='hind' else .077
            m.add(a+'_muscle',a,(0,0,.47),(radius,radius*.85,.51),'muscle',1,organic=.065)
            m.add(a+'_tendon',a,(0,-radius*.70,.48),(.019,.021,.42),'tendon')
            m.add(b+'_joint',b,(0,0,0),(.056,.06,.11),'dark_flesh')
            m.add(b+'_sinew',b,(0,0,.44),(.047,.05,.43),'flesh',1,organic=.045)
            m.add(b+'_ridge',b,(0,-.037,.44),(.025,.024,.37),'ridge')
            m.add(f+'_palm',f,(0,0,.015),(.056,.075,.032),'dark_flesh',1,organic=.02)
            for finger in range(3):
                x=(finger-1)*.038;length=.205 if kind=='fore' else .079
                m.curve(f'{f}_claw{finger}',f,[(x,0,.03),(x,.070,.075),(x*.83,length,.060),(x*.70,length+.026,.021)],[.021,.016,.007,.0008],'claw')
    return m

def runner_pose(t,r):
    t=t%1;g=r['gait'];bob=.011*math.cos(4*math.pi*t);roll=.045*math.sin(2*math.pi*t)
    torso=trans((0,0,bob))@trans((0,0,.46))@rot((0,1,0),roll)@trans((0,0,-.46))
    bones={'torso':torso,'head':torso@trans((0,.32,.48))@rot((0,0,1),.017*math.sin(2*math.pi*t))@trans((0,-.32,-.48))}
    bones['jaw']=bones['head']@trans((0,.34,.405))@rot((1,0,0),-.06-.035*math.sin(2*math.pi*t))@trans((0,-.34,-.405))
    for side in [-1,1]:
        for kind in ['hind','fore']:
            phase=t+(0 if side==-1 else .5)+(0.5 if kind=='fore' else 0)
            step,lift,stance=footstep(phase,g['stride'],g['lift'],.62)
            if kind=='hind':
                hip=np.array([side*.133,-.23,.405+bob]);foot=np.array([side*.178,-.235+step,.023+lift]);k=knee(hip,foot,.24,.235,(0,1,0))
            else:
                hip=np.array([side*.215,.17,.49+bob]);foot=np.array([side*.24,.210+step,.020+lift]);k=knee(hip,foot,.29,.29,(side,.3,0))
            bones[f'{kind}_upper_{side}']=link(hip,k);bones[f'{kind}_lower_{side}']=link(k,foot);bones[f'{kind}_foot_{side}']=trans(foot)
    return bones


def normal_vectors(v,f):
    n=np.zeros_like(v);fn=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
    for i in range(3):np.add.at(n,f[:,i],fn)
    lengths=np.linalg.norm(n,axis=1);bad=lengths<1e-10
    n[bad]=np.array([0.,0.,1.]); lengths[bad]=1
    return n/lengths[:,None]

def vtk_scene(master,cell,pivot,ss):
    import vtk
    from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray
    renderer=vtk.vtkRenderer();renderer.SetBackground(0,0,0);renderer.SetBackgroundAlpha(0);renderer.AutomaticLightCreationOff()
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.SetAlphaBitPlanes(1);window.SetMultiSamples(0);window.SetSize(cell[0]*ss,cell[1]*ss);window.AddRenderer(renderer)
    # Origin -> fixed ground pivot. Source +Y is forward; spec v == -source Y.
    center_y=(pivot[1]-cell[1]/2)/PPU
    center=UP*center_y
    cam=renderer.GetActiveCamera();cam.SetPosition(*(center+EYE*8));cam.SetFocalPoint(*center);cam.SetViewUp(*UP);cam.ParallelProjectionOn();cam.SetParallelScale(cell[1]/PPU/2);cam.SetClippingRange(.1,20)
    for pos,intensity,color in [(RIGHT*-3+UP*5+EYE*4,1.0,(1,.94,.84)),(RIGHT*3+UP*1+EYE*2,.42,(.77,.85,1)),(-EYE*3+UP*5,.4,(.88,.92,1))]:
        l=vtk.vtkLight();l.SetLightTypeToSceneLight();l.SetPosition(*pos);l.SetFocalPoint(0,0,.75);l.SetColor(*color);l.SetIntensity(intensity);renderer.AddLight(l)
    actors=[]
    for part in master.parts:
        v=part['vertices'];f=part['faces'];poly=vtk.vtkPolyData();pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(v,deep=True));poly.SetPoints(pts)
        cells=vtk.vtkCellArray();arr=np.column_stack([np.full(len(f),3),f]).astype(np.int64).ravel();cells.ImportLegacyFormat(numpy_to_vtkIdTypeArray(arr,deep=True));poly.SetPolys(cells)
        ns=normal_vectors(v,f);norm=numpy_to_vtk(ns,deep=True);norm.SetName('Normals');poly.GetPointData().SetNormals(norm)
        col=numpy_to_vtk(np.uint8(np.clip(part['colors'],0,1)*255),deep=True);col.SetName('Material');poly.GetPointData().SetScalars(col)
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(poly);mapper.SetColorModeToDirectScalars()
        actor=vtk.vtkActor();actor.SetMapper(mapper);prop=actor.GetProperty();prop.SetInterpolationToPhong();prop.SetAmbient(.24);prop.SetDiffuse(.78)
        spec=master.recipe['materials'][part['material']];prop.SetSpecular(spec.get('specular',.13));prop.SetSpecularPower(spec.get('shine',26))
        if spec.get('emissive'):prop.SetAmbient(.8);prop.SetDiffuse(.4)
        renderer.AddActor(actor);actors.append(actor)
    if master.recipe.get('asset_id') in ('runner','spitter','charger','brute','brood_warden'):
        import creature_surface
        creature_surface.apply(master, actors, normal_vectors)
    basic=vtk.vtkRenderStepsPass(); ao=vtk.vtkSSAOPass(); ao.SetDelegatePass(basic); ao.SetRadius(.08); ao.SetBias(.004); ao.SetKernelSize(64); ao.BlurOn(); renderer.SetPass(ao)
    return renderer,window,actors

def render(master,direction,t,window,actors,ss):
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy
    pose=master.pose(t);root=rot((0,0,1),ANGLES[direction]);scale=master.recipe.get('physical_scale',1.0)
    for part,actor in zip(master.parts,actors):
        mat=root@scaling([scale]*3)@pose[part['bone']]@part['matrix'];vm=vtk.vtkMatrix4x4()
        for j in range(4):
            for i in range(4):vm.SetElement(j,i,mat[j,i])
        actor.SetUserMatrix(vm)
    window.Render();capture=vtk.vtkWindowToImageFilter();capture.SetInput(window);capture.SetInputBufferTypeToRGBA();capture.ReadFrontBufferOff();capture.Update()
    w,h=window.GetSize();ar=vtk_to_numpy(capture.GetOutput().GetPointData().GetScalars()).reshape(h,w,4)[::-1].copy()
    image=Image.fromarray(ar).resize((w//ss,h//ss),Image.Resampling.LANCZOS)
    data=np.array(image);data[data[:,:,3]<3]=0;image=Image.fromarray(data)
    sockets={}
    for k,(bone,point) in master.sockets.items():
        p=(root@scaling([scale]*3)@pose[bone]@point)[:3];pivot=master.recipe['pivot']
        sockets[k]=[round(float(p@RIGHT*PPU+pivot[0]),4),round(float(pivot[1]-p@UP*PPU),4)]
    return image,sockets

# Portable editable glTF master: named articulated nodes, rigid submeshes and a
# baked locomotion track. No character is reconstructed from generated bitmaps.
def export_glb(master,path):
    buffer=bytearray();views=[];accessors=[]
    def put(array,component,kind,target=None):
        nonlocal buffer
        while len(buffer)%4:buffer.append(0)
        a=np.ascontiguousarray(array);off=len(buffer);buffer+=a.tobytes();view={'buffer':0,'byteOffset':off,'byteLength':a.nbytes}
        if target:view['target']=target
        vi=len(views);views.append(view);acc={'bufferView':vi,'componentType':component,'count':len(a),'type':kind}
        if kind in ['VEC3','SCALAR']:
            acc['min']=np.atleast_1d(a.min(axis=0)).tolist();acc['max']=np.atleast_1d(a.max(axis=0)).tolist()
        ai=len(accessors);accessors.append(acc);return ai
    def trs(m):
        from scipy.spatial.transform import Rotation
        s=np.linalg.norm(m[:3,:3],axis=0);q=Rotation.from_matrix(m[:3,:3]/s).as_quat()
        return m[:3,3].tolist(),q.tolist(),s.tolist()
    start=master.pose(0);nodes=[{'name':master.recipe['asset_id']+'_master','children':[], 'rotation':[-math.sqrt(.5),0,0,math.sqrt(.5)], 'scale':[master.recipe.get('physical_scale',1.0)]*3}];bones={}
    for bone,mat in start.items():
        t,q,s=trs(mat);bones[bone]=len(nodes);nodes.append({'name':bone,'translation':t,'rotation':q,'scale':s,'children':[]});nodes[0]['children'].append(bones[bone])
    materials=[];mids={}
    for key,spec in master.recipe['materials'].items():
        mids[key]=len(materials);materials.append({'name':key,'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':spec.get('metallic',0),'roughnessFactor':spec.get('roughness',.65)},'doubleSided':False})
    meshes=[];images=[];textures=[]
    detailed = master.recipe.get('asset_id') in ('runner','spitter','charger','brute','brood_warden')
    if detailed:
        import creature_surface
        import io
    for part in master.parts:
        v=part['vertices'].astype('<f4');f=part['faces'].astype('<u4').ravel();n=normal_vectors(v,part['faces']).astype('<f4');col=np.where(part['colors']<=.04045,part['colors']/12.92,((part['colors']+.055)/1.055)**2.4).astype('<f4')
        attrs={'POSITION':put(v,5126,'VEC3',34962),'NORMAL':put(n,5126,'VEC3',34962),'COLOR_0':put(col,5126,'VEC3',34962)}
        material_id=mids[part['material']]
        if detailed:
            vv,ff,nn,uv=creature_surface.mesh_uv(part,normal_vectors)
            attrs={'POSITION':put(vv.astype('<f4'),5126,'VEC3',34962),'NORMAL':put(nn.astype('<f4'),5126,'VEC3',34962),
                   'TEXCOORD_0':put(uv.astype('<f4'),5126,'VEC2',34962)}
            f=ff.astype('<u4').ravel()
            spec=master.recipe['materials'][part['material']]
            pixels=creature_surface.texture_pixels(master.recipe['asset_id'],part['name'],part['material'],spec['hex'])
            memory=io.BytesIO();Image.fromarray(pixels).save(memory,format='PNG',optimize=True);raw=memory.getvalue()
            while len(buffer)%4:buffer.append(0)
            off=len(buffer);buffer+=raw
            view_id=len(views);views.append({'buffer':0,'byteOffset':off,'byteLength':len(raw)})
            image_id=len(images);images.append({'bufferView':view_id,'mimeType':'image/png','name':part['name']+'_surface'})
            texture_id=len(textures);textures.append({'source':image_id})
            material_id=len(materials);materials.append({'name':part['name']+'_material','pbrMetallicRoughness':
                {'baseColorTexture':{'index':texture_id},'metallicFactor':0,'roughnessFactor':.87},'doubleSided':False})
        mesh={'name':part['name'],'primitives':[{'attributes':attrs,'indices':put(f,5125,'SCALAR',34963),'material':material_id}]};mi=len(meshes);meshes.append(mesh)
        ni=len(nodes);nodes.append({'name':part['name'],'mesh':mi,'matrix':part['matrix'].T.ravel().tolist()});nodes[bones[part['bone']]]['children'].append(ni)
    for key,(bone,p) in master.sockets.items():
        ni=len(nodes);nodes.append({'name':'socket_'+key,'translation':p[:3].tolist()});nodes[bones[bone]]['children'].append(ni)
    frames=master.recipe['frames'];fps=master.recipe['fps'];times=np.arange(frames+1,dtype='<f4')/fps;timeacc=put(times,5126,'SCALAR');samplers=[];channels=[]
    poses=[master.pose(i/frames) for i in range(frames+1)]
    for bone in bones:
        values=[trs(p[bone]) for p in poses]
        for index,(prop,typ) in enumerate([('translation','VEC3'),('rotation','VEC4'),('scale','VEC3')]):
            a=np.array([v[index] for v in values],dtype='<f4')
            if prop=='rotation':
                for i in range(1,len(a)):
                    if np.dot(a[i-1],a[i])<0:a[i]*=-1
            o=put(a,5126,typ);si=len(samplers);samplers.append({'input':timeacc,'output':o,'interpolation':'LINEAR'});channels.append({'sampler':si,'target':{'node':bones[bone],'path':prop}})
    doc={'asset':{'version':'2.0','generator':'Alien Survivor original parametric motion master'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':nodes,'meshes':meshes,'materials':materials,'animations':[{'name':master.recipe['clip'],'samplers':samplers,'channels':channels}],'accessors':accessors,'bufferViews':views,'buffers':[{'byteLength':len(buffer)}],'extras':{'coordinate_system':'source X right, Y forward, Z up; authoring rig, not runtime 3D','recipe':master.recipe,'note':'Source pose nodes use Z-up; import with the matching source coordinate note.'}}
    if detailed:
        doc.update(images=images,textures=textures)
        doc['extras']['surface_source']=creature_surface.VERSION
    encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);buffer+=b'\0'*((-len(buffer))%4)
    size=12+8+len(encoded)+8+len(buffer)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,size)+struct.pack('<I4s',len(encoded),b'JSON')+encoded+struct.pack('<I4s',len(buffer),b'BIN\0')+buffer)


def main():
    p=argparse.ArgumentParser();p.add_argument('--asset',choices=['player','runner','both'],default='both');p.add_argument('--pack',type=Path,default=PACK);p.add_argument('--ss',type=int,default=3);args=p.parse_args()
    if args.ss<1 or args.ss>6:raise SystemExit('supersample must be 1..6')
    for name in (['player','runner'] if args.asset=='both' else [args.asset]):
        folder=args.pack/'families'/name;recipe=json.loads((folder/'source/rig.json').read_text());master=player_master(recipe) if name=='player' else runner_master(recipe)
        delivery=folder/'delivery.json'
        if delivery.exists() and json.loads(delivery.read_text()).get('status')=='approved':
            raise SystemExit(f'{name}: refusing to change owner-approved source/frames')
        r,w,actors=vtk_scene(master,recipe['cell'],recipe['pivot'],args.ss)
        sockets={};fps=recipe['fps'];N=recipe['frames'];directions=list(ANGLES)
        for d in directions:
            for i in range(N):
                image,sc=render(master,d,i/N,w,actors,args.ss);out=folder/'frames'/recipe['clip']/d/f'{i:03}.png';out.parent.mkdir(parents=True,exist_ok=True);image.save(out)
                sockets[out.relative_to(args.pack).as_posix()]=sc
            print(name,d,'rendered',flush=True)
        w.Finalize()
        export_glb(master,folder/'source/master.glb')
        (folder/'source/sockets.json').write_text(json.dumps(sockets,indent=2)+'\n')
        print(name,len(master.parts),'model parts',flush=True)
if __name__=='__main__':main()
