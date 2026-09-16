extends SceneTree
## Run with the real pinned Godot engine. Pixel checks are a separate Python test.
const Human = preload("res://scripts/human_animation.gd")
var passes: int = 0
var failures: int = 0
func _init() -> void:
	_run.call_deferred()
func check(ok: bool, label: String) -> void:
	if ok:
		passes += 1
		print("PASS " + label)
	else:
		failures += 1
		push_error("FAIL " + label)
func _run() -> void:
	var h := Human.new()
	check(h.clip == "idle" and h.frame_index() == 0, "starts idle")
	for d: Vector2 in [Vector2.RIGHT, Vector2.DOWN, Vector2.LEFT, Vector2.UP]:
		h.advance(0.01, false, d, false, false, true)
		check(h.direction == Human.direction_for(d), "screen direction")
		check(h.texture() != null, "frame texture resource loads")
	h.advance(0.12, true, Vector2.RIGHT, false, false, true)
	check(h.clip == "walk" and h.frame_index() == 1, "walk advances")
	var saved: float = h.walk_time
	h.advance(0, true, Vector2.DOWN, true, true, true)
	check(h.walk_time == saved and h.clip == "walk", "zero delta does not advance")
	h.advance(0.02, false, Vector2.RIGHT, false, false, true)
	check(h.clip == "idle" and h.walk_time == saved, "stationary feet stop")
	h.advance(0.01, true, Vector2.RIGHT, true, true, true)
	check(h.clip == "hit" and h.shot_remaining > 0, "hit precedence and firing effect")
	h.advance(0.2, true, Vector2.RIGHT, false, false, true)
	check(h.clip == "walk", "hit recovers")
	h.advance(0.01, false, Vector2.RIGHT, false, false, false)
	check(h.dead and h.animation_name() == &"death_none" and h.frame_index() == 0, "common death starts")
	h.advance(0.8, false, Vector2.RIGHT, false, false, false)
	check(h.death_finished() and h.frame_index() == 6, "death ends and holds")
	h.advance(0.1, true, Vector2.RIGHT, false, true, true)
	check(h.dead, "cannot revive without reset")
	for i in range(10):
		h.reset()
		check(not h.dead and h.clip == "idle" and h.time == 0 and h.walk_time == 0 and h.shot_remaining == 0, "clean restart")
	print("HUMAN_ANIMATION_TESTS: %d passed, %d failed" % [passes, failures])
	quit(0 if failures == 0 else 1)
