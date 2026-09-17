extends SceneTree
var scene
var ticks: int = 0
func _initialize() -> void:
	setup.call_deferred()
func setup() -> void:
	scene=load("res://main.tscn").instantiate()
	root.add_child(scene)
	scene.set_process(false)
	DirAccess.make_dir_recursive_absolute("res://captures")
func _process(_dt: float) -> bool:
	if scene==null: return false
	ticks+=1
	if ticks==3:
		scene.play_clip("ready")
		scene._scrub(0.)
	if ticks==8: capture("ready")
	if ticks==10:
		scene.play_clip("fire")
		scene._scrub(1.)
		scene.markers=true
		scene.queue_redraw()
	if ticks==15: capture("fire_sockets")
	if ticks==17:
		scene.play_clip("walk")
		scene.markers=false
	if ticks>=20 and ticks<60 and ticks%5==0:
		scene._scrub(float((ticks-20)/5))
	if ticks>=23 and ticks<63 and (ticks-23)%5==0:
		capture("walk_%02d"%int((ticks-23)/5))
	if ticks==67:
		print("PLAYER_V2_CAPTURE_PASS")
		quit(0)
	return false
func capture(name: String) -> void:
	var im:=root.get_texture().get_image()
	if im==null or im.is_empty() or im.save_png("res://captures/"+name+".png")!=OK:
		push_error("No actual capture")
		quit(1)
