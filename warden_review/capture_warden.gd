extends SceneTree
var scene
var ticks: int = 0
func _initialize() -> void:
	setup.call_deferred()
func setup() -> void:
	scene = load("res://scenes/warden_review.tscn").instantiate()
	root.add_child(scene)
	scene.set_process(false)
	DirAccess.make_dir_recursive_absolute("res://captures")
func _process(_dt: float) -> bool:
	if scene == null: return false
	ticks += 1
	if ticks == 3: pose("charge",2)
	if ticks == 8: capture("charge")
	if ticks == 10: pose("acid_attack",3)
	if ticks == 15: capture("acid")
	if ticks == 17: pose("phase_transition",2)
	if ticks == 22: capture("phase")
	if ticks == 24:
		pose("death",9)
		scene.bright = true
		scene.queue_redraw()
	if ticks == 29: capture("death")
	if ticks == 31:
		scene._action("View")
		pose("pulse_attack",4)
	if ticks == 36: capture("native")
	if ticks == 40:
		print("WARDEN_REAL_CAPTURE_PASS")
		quit(0)
	return false
func pose(clip: String, frame: int) -> void:
	scene.play_clip(clip)
	scene._scrub(frame)
	scene._process(0.0)
	for child in scene.get_children():
		if child is OptionButton:
			child.select(scene.CLIPS.find(clip))
func capture(name: String) -> void:
	var im := root.get_texture().get_image()
	if im == null or im.is_empty() or im.save_png("res://captures/warden_"+name+".png") != OK:
		push_error("Actual Warden capture missing")
		quit(1)
