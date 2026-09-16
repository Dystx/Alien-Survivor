#!/usr/bin/env python3
"""Verification only. Synthetic texture pixels never become production artwork."""
from pathlib import Path
import hashlib, os, re, shutil, struct, subprocess, sys, zlib
root=Path(__file__).resolve().parents[1]
game=root/'game'
engine=sys.argv[1]
# Reuse the inspected, pinned finale staging code, not its command execution.
previous=root/'verification/run.py'
staging=previous.read_text().split('commands=')[0]
exec(compile(staging,str(previous),'exec'),{'__file__':str(previous),'__name__':'human_staging'})
expected={'main.gd':'a79f7e2707c4b4242c5c92cfc8eb2935db127c1cae1c3e7d18dc12e745c5ef14','arena_view.gd':'ccbd713e00351fa562550c35c91a3d5bb2a0bfa7b47e300616dad27c8d901b42','hud.gd':'3e519be8e1df916b087f6c446d598a6b24211845c660820750140cf41db08db8','sprite_factory.gd':'22600bf24e18bfa1a97446fce56391ca7d5dc30fefbd09987f3876d154db7a04'}
def canonical(text):
    return '\n'.join(line.rstrip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#'))
for name,digest in expected.items():
    p=game/'scripts'/name
    clean=canonical(p.read_text())
    if hashlib.sha256(clean.encode()).hexdigest()!=digest:
        raise SystemExit('Unexpected baseline; refusing to patch '+name)
    p.write_text(clean+'\n')
subprocess.run(['patch','-p1','--batch','-i',str(root/'verification/human.patch')],cwd=game,check=True)
for name in ['human_animation.gd','animation_review.gd']:
    shutil.copyfile(root/'verification'/name,game/'scripts'/name)
shutil.copyfile(root/'verification/human_animation_tests.gd',game/'tests/human_animation_tests.gd')
(game/'scenes/animation_review.tscn').write_text('''[gd_scene load_steps=2 format=3]
[ext_resource type="Script" path="res://scripts/animation_review.gd" id="1"]
[node name="HumanAnimationReview" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
script = ExtResource("1")
''')
# Identical frame rectangles and clip timings, deliberately NOT real human artwork.
out=game/'assets/human_survivor';out.mkdir(parents=True,exist_ok=True)
def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
w,h=1056,792
raw=(b'\0'+bytes([84,99,111,255])*w)*h
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')
(out/'human_atlas.png').write_bytes(png)
slots=[]
for direction in ['e','s','w','n']:
    for clip,count in [('idle',1),('walk',6),('hit',2)]:
        for n in range(count):slots.append((clip,direction,n))
slots += [('death','none',n) for n in range(7)]
text=['[gd_resource type="SpriteFrames" load_steps=45 format=3]','','[ext_resource type="Texture2D" path="res://assets/human_survivor/human_atlas.png" id="1"]']
for i,_ in enumerate(slots):
    text+=['',f'[sub_resource type="AtlasTexture" id="f{i}"]','atlas = ExtResource("1")',f'region = Rect2({i%8*132+2}, {i//8*132+2}, 128, 128)','filter_clip = true']
animations=[]
for clip,fps,loop in [('idle',1,True),('walk',9,True),('hit',12,False),('death',10,False)]:
    for direction in (['none'] if clip=='death' else ['e','s','w','n']):
        refs=', '.join('{"duration": 1.0, "texture": SubResource("f%d")}'%i for i,(c,d,n) in enumerate(slots) if c==clip and d==direction)
        animations.append('{"frames": ['+refs+'], "loop": '+str(loop).lower()+', "name": &"'+clip+'_'+direction+'", "speed": '+str(float(fps))+'}')
text+=['','[resource]','animations = ['+',\n'.join(animations)+']','']
(out/'sprite_frames.tres').write_text('\n'.join(text))
print('HUMAN_TEXTURE_FIXTURE: all PNG pixels in this job are synthetic; actual art quality is NOT tested.',flush=True)
for name in ['main.gd','arena_view.gd','hud.gd','sprite_factory.gd','human_animation.gd','animation_review.gd']:
    print('HUMAN_CANONICAL_SHA256',name,hashlib.sha256(canonical((game/'scripts'/name).read_text()).encode()).hexdigest(),flush=True)
(game/'tests/human_scene.gd').write_text('''extends SceneTree
var scene
var review
var ticks: int = 0
var paused_frame: int = 0
func _initialize() -> void:
	_setup.call_deferred()
func _setup() -> void:
	scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	scene.sound.muted = true
func require(ok: bool, message: String) -> void:
	if not ok:
		push_error(message)
		quit(1)
func _process(_dt: float) -> bool:
	ticks += 1
	if ticks == 5:
		scene._on_action("start")
		scene.sim.spawning_enabled = false
		scene.sim.finale_enabled = false
	if ticks == 30:
		scene.sim.health = 0.0
	if ticks == 34:
		require(scene.view.human.dead and scene.hud.waiting_for_death, "Death presentation did not start")
	if ticks == 100:
		require(scene.view.human.death_finished() and not scene.hud.waiting_for_death and scene.hud.overlay.visible, "Results did not follow death")
	if ticks == 105:
		scene._on_action("start")
		scene.sim.spawning_enabled = false
	if ticks == 112:
		require(not scene.view.human.dead and not scene.hud.waiting_for_death, "Restart retained dead player")
	if ticks == 120:
		scene._on_action("animation_review")
		scene = null
	if ticks == 130:
		review = current_scene
		require(review != null and review.actors.size() == 4, "Native animation review did not open")
	if ticks == 160:
		review._toggle_pause()
		paused_frame = review.actors[0].frame
	if ticks == 170:
		require(review.actors[0].frame == paused_frame, "Review pause did not hold frame")
		review._toggle_pause()
		review._play("death")
	if ticks == 235:
		require(review.actors[0].frame == 6, "Shared death did not hold its final frame")
		review._return()
		review = null
	if ticks == 250:
		require(current_scene != null and current_scene.sim.phase == current_scene.sim.Phase.MENU, "Return to title failed")
		print("HUMAN_SCENE_FIXTURE_PASS")
		quit(0)
	return false
''')
commands=[([engine,'--headless','--path',str(game),'--editor','--import','--quit'],None),([engine,'--headless','--path',str(game),'--script','res://tests/run_tests.gd'],'ALIEN_SURVIVOR_TESTS:'),([engine,'--headless','--path',str(game),'--script','res://tests/human_animation_tests.gd'],'HUMAN_ANIMATION_TESTS:'),([engine,'--headless','--path',str(game),'--fixed-fps','60','--script','res://tests/render_smoke.gd','--','--ci-art-fixtures'],'FINALE_SCENE_FIXTURE_PASS'),([engine,'--headless','--path',str(game),'--fixed-fps','60','--script','res://tests/human_scene.gd','--','--ci-art-fixtures'],'HUMAN_SCENE_FIXTURE_PASS')]
if shutil.which('xvfb-run'):
    commands.append((['xvfb-run','-a',engine,'--path',str(game),'--audio-driver','Dummy','--fixed-fps','60','--script','res://tests/human_scene.gd','--','--ci-art-fixtures'],'HUMAN_SCENE_FIXTURE_PASS'))
for cmd,marker in commands:
    print('RUN',' '.join(cmd),flush=True)
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=180,env=dict(os.environ,LIBGL_ALWAYS_SOFTWARE='1'))
    output=result.stdout+result.stderr
    print(output,flush=True)
    if result.returncode or re.search(r'SCRIPT ERROR:|Parse Error:|^ERROR:',output,re.M) or (marker and marker not in output):
        raise SystemExit('HUMAN VERIFICATION FAILED')
print('HUMAN_ENGINE_AND_FIXTURE_SCENE_PASS. Actual image appearance, Mac/mobile, exports and final animation quality are NOT established.',flush=True)
