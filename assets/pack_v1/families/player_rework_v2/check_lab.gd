extends SceneTree
var passed: int = 0
var failed: int = 0
func check(value: bool, text: String) -> void:
	if value: passed += 1
	else:
		failed += 1
		push_error(text)
func _initialize() -> void:
	run.call_deferred()
func run() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	scene.set_process(false)
	await process_frame
	check(scene.loaded and scene.frame_count==128,"128 actual frames loaded")
	check(scene.sequences.size()==24,"24 directional clips")
	if not scene.loaded:
		quit(1)
		return
	for clip: String in scene.EXPECTED:
		scene.play_clip(clip)
		check(scene.frame_index()==0,"first frame")
		for d: String in scene.DIRECTIONS:
			check(scene.sequences[clip+"_"+d].size()==int(scene.EXPECTED[clip]),"all directions present")
	scene.play_clip("fire")
	scene.advance(50.)
	check(scene.frame_index()==3,"fire holds final pose")
	scene.play_clip("walk")
	scene.advance(.1)
	check(scene.frame_index()==1,"walk advances")
	scene.paused=true
	var t: float=scene.clock
	scene.advance(.2)
	check(scene.clock==t,"pause")
	scene.play_clip("walk")
	scene.half_speed=true
	scene.advance(.1)
	check(is_equal_approx(scene.clock,.05),"half speed")
	scene._scrub(7.)
	check(scene.frame_index()==7 and scene.paused,"scrub freezes exact frame")
	scene.play_clip("invalid")
	check(scene.clip=="walk","unknown clip rejected")
	scene.play_clip("ready")
	scene.half_speed=false
	scene.advance(100.)
	check(scene.frame_index()<4,"ready loops")
	for node in scene.get_children():
		if node is Control:
			check(Rect2(Vector2.ZERO,Vector2(1280,720)).encloses(node.get_global_rect()),"UI inside viewport")
	for i in range(10):
		scene.play_clip("ready")
		check(scene.clock==0. and not scene.paused,"clean replay")
	print("PLAYER_V2_LAB_TESTS: %d passed, %d failed"%[passed,failed])
	quit(1 if failed else 0)
