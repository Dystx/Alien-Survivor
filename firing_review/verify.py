#!/usr/bin/env python3
"""Verify firing source with explicit fixtures. This is not artwork approval."""
from pathlib import Path
import hashlib, os, re, shutil, struct, subprocess, sys, zlib
root=Path(__file__).resolve().parents[1]
game=root/'game'; here=root/'firing_review'; engine=sys.argv[1]
previous=root/'verification/human_run.py'
source=previous.read_text().split('commands=[',1)[0]
exec(compile(source,str(previous),'exec'),{'__file__':str(previous),'__name__':'firing_staging'})
def canonical(text):
    return '\n'.join(l.rstrip() for l in text.splitlines() if l.strip() and not l.lstrip().startswith('#'))
for name in ['main.gd','arena_view.gd','hud.gd']:
    p=game/'scripts'/name;p.write_text(canonical(p.read_text())+'\n')
subprocess.run(['patch','-p1','--batch','--fuzz=0','-i',str(here/'firing.patch')],cwd=game,check=True)
for name in ['firing_presentation.gd','firing_review.gd']:
    shutil.copyfile(here/name,game/'scripts'/name)
shutil.copyfile(here/'firing_tests.gd',game/'tests/firing_tests.gd')
(game/'scenes/firing_review.tscn').write_text('''[gd_scene load_steps=2 format=3]
[ext_resource type="Script" path="res://scripts/firing_review.gd" id="1"]
[node name="FiringReview" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
script = ExtResource("1")
''')
# The lab preloads its effect from disk. Gameplay scenery uses existing fixtures.
# This temporary file is not committed as production artwork.
def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
out=game/'assets/sprites/fx/muzzle_0.png';out.parent.mkdir(parents=True,exist_ok=True)
raw=(b'\0'+bytes([255,205,90,255])*96)*80
out.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',96,80,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))
(game/'tests/firing_scene.gd').write_text('''extends SceneTree
var scene
var review
var ticks: int = 0
var frozen: float = 0.0
func _initialize() -> void:
\t_setup.call_deferred()
func _setup() -> void:
\tscene = load("res://scenes/main.tscn").instantiate()
\troot.add_child(scene)
\tcurrent_scene = scene
\tscene.sound.muted = true
func require(ok: bool, message: String) -> void:
\tif not ok:
\t\tpush_error(message)
\t\tquit(1)
func _process(_dt: float) -> bool:
\tticks += 1
\tif ticks == 5:
\t\tscene._on_action("start")
\t\tscene.sim.spawning_enabled = false
\t\tscene.sim.add_enemy(scene.sim.player + Vector2(210, 60))
\tif ticks == 20:
\t\trequire(scene.sim.shot_count > 0, "Live scene never fired")
\t\tscene._on_action("pause")
\t\tfrozen = scene.view.firing.flash_age
\tif ticks == 30:
\t\trequire(scene.view.firing.flash_age == frozen, "Pause advanced firing presentation")
\t\tscene._on_action("resume")
\tif ticks == 45:
\t\tscene._on_action("firing_review")
\t\tscene = null
\tif ticks == 55:
\t\treview = current_scene
\t\trequire(review != null and review.humans.size() == 4, "Firing review did not open")
\t\treview._action("Walk")
\tif ticks == 80:
\t\treview._action("Turn")
\tif ticks == 100:
\t\treview._action("Hit")
\t\treview._action("Sockets")
\tif ticks == 120:
\t\treview._action("Pause")
\t\tfrozen = review.clock
\tif ticks == 132:
\t\trequire(review.clock == frozen, "Lab pause advanced animation")
\t\treview._action("Pause")
\t\treview._action("0.5x")
\tif ticks == 165:
\t\treview._action("Return")
\t\treview = null
\tif ticks == 175:
\t\tscene = current_scene
\t\trequire(scene.sim.phase == scene.sim.Phase.MENU, "Lab did not return to menu")
\t\tscene._on_action("start")
\tif ticks == 180:
\t\trequire(scene.view.firing.traces.is_empty(), "Restart retained old projectile attachment")
\t\tprint("FIRING_SCENE_PASS")
\t\tquit(0)
\treturn false
''')
for name in ['main.gd','arena_view.gd','hud.gd','firing_presentation.gd','firing_review.gd','simulation.gd','human_animation.gd']:
    print('FIRING_CANONICAL_SHA256',name,hashlib.sha256(canonical((game/'scripts'/name).read_text()).encode()).hexdigest(),flush=True)
commands=[([engine,'--headless','--path',str(game),'--editor','--import','--quit'],0,None)]
for filename,marker in [('run_tests.gd','ALIEN_SURVIVOR_TESTS:'),('human_animation_tests.gd','HUMAN_ANIMATION_TESTS:'),('firing_tests.gd','FIRING_TESTS:')]:
    commands.append(([engine,'--headless','--path',str(game),'--script','res://tests/'+filename],0,marker))
commands.append(([engine,'--headless','--path',str(game),'--script','res://tests/run_tests.gd','--','--self-test-failure'],1,'intentional runner self-check'))
for scene,marker in [('human_scene.gd','HUMAN_SCENE_FIXTURE_PASS'),('render_smoke.gd','FINALE_SCENE_FIXTURE_PASS'),('firing_scene.gd','FIRING_SCENE_PASS')]:
    cmd=[engine,'--path',str(game),'--audio-driver','Dummy','--fixed-fps','60','--script','res://tests/'+scene,'--','--ci-art-fixtures']
    commands.append(([engine,'--headless']+cmd[1:],0,marker))
    if scene=='firing_scene.gd':commands.append((['xvfb-run','-a']+cmd,0,marker))
for cmd,code,marker in commands:
    print('RUN',' '.join(cmd),flush=True)
    r=subprocess.run(cmd,text=True,capture_output=True,timeout=180,env=dict(os.environ,LIBGL_ALWAYS_SOFTWARE='1'))
    output=r.stdout+r.stderr;print(output,flush=True)
    if r.returncode!=code or re.search(r'SCRIPT ERROR:|Parse Error:|^ERROR:',output,re.M) or marker and marker not in output:
        raise SystemExit('FIRING VERIFICATION FAILED')
print('FIRING_ENGINE_FIXTURE_PASS. Real code; synthetic images. Not Mac, actual-art appearance, controller, audio, export, performance or owner approval.',flush=True)
