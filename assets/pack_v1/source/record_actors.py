#!/usr/bin/env python3
"""Record review-only actor frames. Owner approval remains null."""
from pathlib import Path
import argparse,json,hashlib
from complete_actors import CLIPS,SIZES,build
import render_motion as b

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def record(pack):
 path=pack/'pack.json';spec=json.loads(path.read_text())
 spec['spec_revision']='0.2.0'
 spec['human_design_decision']='Owner selected human survivor: visible face/short hair, fitted dark shirt, light worn vest, olive cargo trousers; no helmet/robotic armour.'
 spec['actor_bounds_revision']='Fixed family canvases enlarged once to contain death/attack motion; physical scale, camera and pivots do not vary per frame. Trimmed review atlases retain logical ground anchors.'
 for group in spec['asset_groups']:
  for k in group['ids']:
   if k in SIZES:group['cell'],group['pivot']=SIZES[k]
   if k=='player':group['subject']='Human survivor; visible face, short dark hair, exposed forearms, fitted shirt, light tactical vest, olive cargo trousers and compact rifle. No helmet, sealed visor or robot limbs.'
 path.write_text(json.dumps(spec,indent=2)+'\n')
 for kind in CLIPS:
  folder=pack/'families'/kind
  m=build(kind);m.clip='walk' if kind=='player' else 'move'
  n,fps,_=CLIPS[kind][m.clip];m.recipe.update(clip=m.clip,frames=n,fps=fps)
  b.export_glb(m,folder/'source/master.glb')
  sources=[]
  for p in [pack/'source/render_motion.py',pack/'source/complete_actors.py',pack/'source/record_actors.py',folder/'source/rig.json',folder/'source/animations.json',folder/'source/sockets.json',folder/'source/master.glb']:
   sources.append({'path':p.relative_to(pack).as_posix(),'sha256':sha(p),'provenance':'Original Alien Survivor procedural mesh/pose source. Human design selected by the owner; final artwork and rights review not implied. GLB contains the locomotion track; all other actions are reproducible from Python source.'})
  frames={p.relative_to(pack).as_posix():sha(p) for p in sorted((folder/'frames').rglob('*.png'))}
  sockets=json.loads((folder/'source/sockets.json').read_text())
  delivery={'asset_id':kind,'status':'review','spec_sha256':sha(path),'sources':sources,'frame_sha256':frames,'sockets':sockets,'review':{k:False for k in ['style','motion','alpha_edges','pivot_and_scale','direction_coverage','source_rights','aim_and_strafe']},'public_source_permission':False,'owner_approval':None,'notes':['Declared actor coverage is not final-art approval.','Review-only integration was requested; approved-only production export is unchanged.','Four facings approximate continuous aim visually; gameplay aiming is not quantized.']}
  (folder/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
  print(kind,len(frames),'review frames recorded')
 text=(pack/'SPEC.md').read_text()
 text=text.replace('Specification baseline 0.1.0','Specification baseline 0.2.0')
 text=text.replace('amber player accents','olive cloth and exposed human skin')
 for old,new in [('| Player | 128 x 128 | 64, 110 |','| Player | 160 x 160 | 80, 112 |'),('| Runner | 96 x 96 | 48, 78 |','| Runner | 128 x 128 | 64, 80 |'),('| Spitter / charger | 128 x 128 | 64, 104 |','| Spitter | 160 x 160 | 80, 108 |\n| Charger | 160 x 160 | 80, 104 |'),('| Brute | 160 x 160 | 80, 136 |','| Brute | 192 x 192 | 96, 136 |'),('| Brood Warden | 256 x 256 | 128, 204 |','| Brood Warden | 288 x 288 | 144, 204 |')]:text=text.replace(old,new)
 if '## Active human-design revision 0.2.0' not in text:
  text+='\n\n## Active human-design revision 0.2.0\n\nThe owner selected a human rather than enclosed armour. The player has short hair, a visible face, exposed forearms, a fitted dark shirt, a light vest and olive trousers. The actor cells and pivots were enlarged once to contain death and attack bounds without changing physical scale; the table and pack.json are updated together. No per-frame stretching is permitted. All six families are review candidates, not owner-approved production. The separate integration preview is explicitly labelled as such; the production exporter still refuses unapproved art.\n'
 (pack/'SPEC.md').write_text(text)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--pack',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();record(a.pack)
