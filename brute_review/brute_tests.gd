extends SceneTree
const Brute = preload("res://scripts/brute_animation.gd")
const Sim = preload("res://scripts/simulation.gd")
var passed: int = 0
var failed: int = 0
func check(value: bool, label: String) -> void:
	if value:
		passed += 1
		print("PASS ", label)
	else:
		failed += 1
		push_error("FAIL " + label)
func _initialize() -> void:
	var expected: Dictionary = {"idle": 4, "move": 6, "windup": 4, "attack": 4, "recovery": 2, "hit": 2, "death": 6}
	check(Brute.Frames.get_animation_names().size() == 28, "28 declared brute clips")
	var frames_total: int = 0
	for clip: String in expected:
		for d: String in ["e", "s", "w", "n"]:
			var name := StringName(clip + "_" + d)
			check(Brute.Frames.get_frame_count(name) == int(expected[clip]), "frame count " + String(name))
			frames_total += Brute.Frames.get_frame_count(name)
	check(frames_total == 112, "112 actual frame slots")
	var sim := Sim.new()
	sim.reset()
	sim.spawning_enabled = false
	sim.finale_enabled = false
	var enemy = sim.add_enemy(sim.player + Vector2(120, 40), 0.0, "brute")
	var controller := Brute.new()
	var empty: Array[Dictionary] = []
	controller.advance(0.016, sim.enemies, empty, sim.player, true)
	check(controller.live.size() == 1 and controller.live[enemy.id].clip == "idle", "new brute starts with a stable pivot")
	enemy.position.x += 4.0
	controller.advance(0.016, sim.enemies, empty, sim.player, true)
	check(controller.live[enemy.id].clip == "move", "actual displacement selects locomotion")
	var cycle: float = controller.live[enemy.id].cycle
	check(cycle > 0.0, "travel advances gait phase")
	controller.advance(0.016, sim.enemies, empty, sim.player, true)
	check(controller.live[enemy.id].clip == "idle", "blocked brute stops cycling feet")
	check(controller.live[enemy.id].cycle == cycle, "standing preserves gait phase")
	var frozen_age: float = controller.live[enemy.id].age
	controller.advance(0.0, sim.enemies, empty, sim.player, true)
	check(controller.live[enemy.id].age == frozen_age, "pause does not advance animation")
	enemy.flash = 0.08
	controller.advance(0.016, sim.enemies, empty, sim.player, true)
	check(controller.live[enemy.id].clip == "hit", "hit uses the authored pose")
	controller.advance(0.016, sim.enemies, empty, sim.player, true)
	check(controller.live[enemy.id].hit_age > 0.0, "constant flash does not restart hit pose")
	enemy.flash = 0.0
	controller.advance(0.3, sim.enemies, empty, sim.player, true)
	enemy.position = sim.player + Vector2(20,0)
	var health_before: float = sim.health
	var enemy_health: float = enemy.health
	controller.advance(0.016, sim.enemies, empty, sim.player, true)
	check(controller.live[enemy.id].clip == "attack", "near brute displays claw gesture")
	check(sim.health == health_before and enemy.health == enemy_health, "presentation never deals or defers damage")
	controller.advance(0.43, sim.enemies, empty, sim.player, true)
	check(controller.live[enemy.id].clip == "recovery", "contact gesture settles without disabling damage")
	check(enemy.windup == 0.0 and enemy.action_timer == 0.0, "no invented simulation telegraph or stun")
	var before_damage: float = enemy.health
	sim.damage_enemy(enemy, 10.0)
	check(is_equal_approx(before_damage - enemy.health, 8.0), "existing twenty percent armour reduction unchanged")
	check(controller.for_enemy(enemy) != null, "live pose resolves an actual texture")
	var death_event: Dictionary = {"type":"death", "kind":"brute", "position":enemy.position, "direction":enemy.direction}
	sim.damage_enemy(enemy, 10000.0)
	var death_events: Array[Dictionary] = [death_event]
	controller.advance(0.016, sim.enemies, death_events, sim.player, true)
	check(controller.live.is_empty() and controller.deaths.size() == 1, "dead brute leaves live state and enters one fall")
	controller.advance(0.9, sim.enemies, empty, sim.player, true)
	check(float(controller.deaths[0].age) == Brute.DEATH_DURATION, "corpse holds final frame")
	check(Brute.texture("death", Vector2.RIGHT, 10.0) == Brute.texture("death", Vector2.RIGHT, 0.74), "death never loops back to standing")
	controller.advance(0.016, sim.enemies, empty, sim.player, false)
	check(controller.deaths.is_empty(), "corpse option removes completed remains")
	for i in range(90):
		controller.advance(0.01, sim.enemies, death_events, sim.player, true)
	check(controller.deaths.size() == Brute.MAX_CORPSES, "corpse count is bounded")
	for i in range(10):
		controller.reset()
		check(controller.live.is_empty() and controller.deaths.is_empty(), "clean brute restart")
	print("BRUTE_TESTS: %d passed, %d failed" % [passed,failed])
	quit(0 if failed == 0 else 1)
