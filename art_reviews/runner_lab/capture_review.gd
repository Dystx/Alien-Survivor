extends SceneTree
var scene
var ticks: int = 0
func _initialize() -> void:
	setup.call_deferred()
func setup() -> void:
	scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	scene.set_process(false)
	DirAccess.make_dir_recursive_absolute("res://captures")
func _process(_delta: float) -> bool:
	if scene == null:
		return false
	ticks += 1
	if ticks == 4:
		scene.play_clip("move")
		scene.advance(0.2)
	if ticks == 8:
		capture("move")
	if ticks == 10:
		scene.play_clip("attack")
		scene._scrub(2.0)
	if ticks == 14:
		capture("attack")
	if ticks == 16:
		scene.play_clip("death")
		scene._scrub(4.0)
		scene.bright = true
		scene.queue_redraw()
	if ticks == 20:
		capture("death")
	if ticks == 25:
		print("RUNNER_CAPTURE_PASS: actual runner pixels")
		quit(0)
	return false
func capture(name: String) -> void:
	var image := root.get_texture().get_image()
	if image == null or image.is_empty():
		push_error("No actual rendered image")
		quit(1)
		return
	if image.save_png("res://captures/" + name + ".png") != OK:
		push_error("Could not save actual render")
		quit(1)
