extends SceneTree
const Human = preload("res://scripts/human_animation.gd")
const Firing = preload("res://scripts/firing_presentation.gd")
const Simulation = preload("res://scripts/simulation.gd")
const Iso = preload("res://scripts/projection.gd")
var passed: int = 0
var failed: int = 0
func check(ok: bool, text: String) -> void:
	if ok:
		passed += 1
		print("PASS ", text)
	else:
		failed += 1
		print("FAIL ", text)
func _initialize() -> void:
	var human := Human.new()
	var firing := Firing.new()
	for direction in Human.DIRECTIONS:
		human.direction = direction
		for clip: String in ["idle", "walk", "hit"]:
			human.clip = clip
			var count := Human.FRAMES.get_frame_count(human.animation_name())
			for i in range(count):
				human.time = float(i) / Human.FRAMES.get_animation_speed(human.animation_name()) + 0.001
				human.walk_time = human.time
				var socket := Firing.muzzle_cell(human)
				check(socket.x > 0 and socket.y > 0 and socket.x < 128 and socket.y < 128, "calibrated socket in frame " + clip + "/" + direction + "/" + str(i))
		human.clip = "walk"
		var at_feet := Vector2(300, 240)
		var origin := at_feet + Firing.muzzle_offset(human, 0.96)
		var moved := at_feet + Vector2(31, -12) + Firing.muzzle_offset(human, 0.96)
		check((moved - origin).is_equal_approx(Vector2(31, -12)), "flash follows moving muzzle " + direction)
		check(firing.behind_body(human) == (direction == "n"), "correct rear occlusion " + direction)
	human.reset()
	firing.advance(0.016, human, true, [], 450.0, 0.96)
	check(firing.visible(human), "new shot is visible")
	var age := firing.flash_age
	firing.advance(0.0, human, false, [], 450.0, 0.96)
	check(firing.flash_age == age, "paused presentation freezes flash")
	firing.advance(0.060, human, false, [], 450.0, 0.96)
	check(not firing.visible(human), "flash expires within 55ms")
	firing.advance(0.016, human, true, [], 450.0, 0.96)
	human.direction = "w"
	firing.advance(0.016, human, false, [], 450.0, 0.96)
	check(not firing.visible(human), "old flash cannot swing to opposite facing")
	var bullet := Simulation.Bullet.new()
	bullet.position = Vector2(80, 90)
	bullet.previous = bullet.position
	bullet.velocity = Vector2(300, 70)
	bullet.remaining = 450.0
	firing.advance(0.016, human, true, [bullet], 450.0, 0.96)
	var points := firing.trace_points(bullet)
	var expected := Iso.project(bullet.position) + Firing.muzzle_offset(human, 0.96)
	check(points[0].is_equal_approx(expected) and points[1].is_equal_approx(expected), "tracer starts exactly at muzzle with no backwards tail")
	var record: Dictionary = firing.traces[bullet.get_instance_id()].duplicate()
	human.direction = "s"
	firing.advance(0.016, human, false, [bullet], 450.0, 0.96)
	check(firing.traces[bullet.get_instance_id()] == record, "spawned bullet keeps its original attachment")
	bullet.position += bullet.velocity.normalized() * 5.0
	bullet.remaining = 445.0
	points = firing.trace_points(bullet)
	check(points[0].is_equal_approx(expected), "first tracer tail stays at barrel, not behind body")
	var old_size := firing.traces.size()
	for i in range(10):
		firing.trace_points(bullet)
	check(firing.traces.size() == old_size, "drawing queries do not create presentation state")
	firing.advance(0.016, human, false, [], 450.0, 0.96)
	check(firing.traces.is_empty(), "dead projectile entries are removed")
	human.dead = true
	firing.advance(0.016, human, true, [], 450.0, 0.96)
	check(not firing.visible(human), "no firing flash after death")
	for i in range(10):
		firing.reset()
		check(firing.traces.is_empty() and firing.shot_serial == 0 and firing.flash_age == Firing.FLASH_SECONDS, "restart clears firing state")
	print("FIRING_TESTS: %d passed, %d failed" % [passed, failed])
	quit(0 if failed == 0 else 1)
