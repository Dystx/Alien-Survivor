extends SceneTree
var passed: int = 0
var failed: int = 0
func check(ok: bool, message: String) -> void:
	if ok:
		passed += 1
	else:
		failed += 1
		push_error(message)
func _initialize() -> void:
	run.call_deferred()
func run() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	scene.set_process(false)
	await process_frame
	check(scene.loaded and scene.frames_total == 84, "actual runner atlas loads all 84 frames")
	if not scene.loaded:
		quit(1)
		return
	var resource: SpriteFrames = load("res://assets/runner_review/sprite_frames.tres")
	check(resource != null and resource.get_animation_names().size() == 20, "real SpriteFrames resource imports all twenty clips")
	for clip: String in scene.CLIPS:
		scene.play_clip(clip)
		check(scene.frame_index() == 0, "clip starts at first frame: " + clip)
		for direction: String in scene.DIRECTIONS:
			check(scene.sequences[clip+"_"+direction].size() == int(scene.EXPECTED[clip]), "complete real direction: " + clip+"_"+direction)
		scene.advance(100.0)
		if not bool(scene.clips[clip].loop):
			check(scene.frame_index() == int(scene.EXPECTED[clip])-1, "non-looping clip holds final frame: " + clip)
	scene.play_clip("move")
	scene.advance(0.1)
	check(scene.frame_index() == 1, "normal playback advances")
	scene.paused = true
	var old_clock: float = scene.clock
	scene.advance(1.0)
	check(scene.clock == old_clock, "pause freezes time")
	scene.play_clip("move")
	scene.half_speed = true
	scene.advance(0.1)
	check(is_equal_approx(scene.clock, 0.05), "half speed changes playback only")
	scene._scrub(5.0)
	check(scene.frame_index() == 5 and scene.paused, "slider freezes exact frame")
	scene.play_clip("death")
	scene.half_speed = false
	scene.advance(10.0)
	check(scene.frame_index() == 4, "death holds corpse")
	for i in range(10):
		scene.play_clip("move")
		check(scene.clock == 0.0 and not scene.paused, "replay resets viewer")
	print("RUNNER_REVIEW_TESTS: %d passed, %d failed" % [passed, failed])
	quit(1 if failed else 0)
