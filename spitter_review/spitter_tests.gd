extends SceneTree
const Spitter = preload("res://scripts/spitter_animation.gd")
const Sim = preload("res://scripts/simulation.gd")
var passed: int = 0
var failed: int = 0
func check(value: bool, label: String) -> void:
	if value:
		passed += 1
		print("PASS ", label)
	else:
		failed += 1
		push_error(label)
func _initialize() -> void:
	var counts := {"idle":4,"move":6,"windup":4,"attack":4,"recovery":2,"hit":2,"death":5}
	var total: int = 0
	check(Spitter.Frames.get_animation_names().size() == 28, "28 real spitter clips")
	for clip: String in counts:
		for d: String in ["e","s","w","n"]:
			var key := StringName(clip + "_" + d)
			check(Spitter.Frames.get_frame_count(key) == int(counts[clip]), "complete " + String(key))
			total += Spitter.Frames.get_frame_count(key)
	check(total == 108, "108 real spitter frames")
	var sim := Sim.new()
	sim.reset()
	sim.spawning_enabled = false
	sim.finale_enabled = false
	var enemy = sim.add_enemy(sim.player + Vector2(140,50), 0.0, "spitter")
	var controller := Spitter.new()
	var none: Array[Dictionary] = []
	controller.advance(0.016, sim.enemies, none, true)
	check(controller.live[enemy.id].clip == "idle", "idle before actual displacement")
	enemy.position.x += 4.0
	controller.advance(0.016, sim.enemies, none, true)
	check(controller.live[enemy.id].clip == "move", "distance selects gait")
	var cycle: float = controller.live[enemy.id].cycle
	controller.advance(0.016, sim.enemies, none, true)
	check(controller.live[enemy.id].clip == "idle" and controller.live[enemy.id].cycle == cycle, "blocked feet do not cycle")
	sim._arm_attack(enemy, "spit", Vector2.LEFT, 0.65)
	var health: float = sim.health
	controller.advance(0.016, sim.enemies, sim.events, true)
	check(controller.live[enemy.id].clip == "windup" and controller.live[enemy.id].age == 0.0, "simulation arms first warning pose")
	enemy.windup = 0.3
	controller.advance(0.016, sim.enemies, none, true)
	check(controller.live[enemy.id].age > 0.0 and sim.enemy_projectiles.is_empty(), "windup advances without producing a projectile")
	var age: float = controller.live[enemy.id].age
	controller.advance(0.0, sim.enemies, none, true)
	check(controller.live[enemy.id].age == age, "pause freezes spitter")
	enemy.flash = 0.08
	controller.advance(0.016, sim.enemies, none, true)
	check(controller.live[enemy.id].clip == "windup", "hit cannot hide attack telegraph")
	enemy.windup = 0.0
	sim._execute_attack(enemy)
	controller.advance(0.016, sim.enemies, sim.events, true)
	check(controller.live[enemy.id].clip == "attack" and sim.enemy_projectiles.size() == 1, "simulation release selects attack")
	enemy.recovery = 0.08
	controller.advance(0.016, sim.enemies, none, true)
	check(controller.live[enemy.id].clip == "recovery", "late recovery selects settle pose")
	check(sim.health == health and sim.enemy_projectiles.size() == 1, "presentation never changes damage or duplicates a shot")
	check(controller.for_enemy(enemy) != null, "real pose texture resolves")
	enemy.flash = 0.0
	enemy.recovery = 0.0
	controller.advance(0.3, sim.enemies, none, true)
	enemy.flash = 0.08
	controller.advance(0.016, sim.enemies, none, true)
	check(controller.live[enemy.id].clip == "hit", "ordinary hit reaction")
	controller.advance(0.016, sim.enemies, none, true)
	check(controller.live[enemy.id].hit_age > 0.0, "hit does not restart every tick")
	sim.events.clear()
	sim.damage_enemy(enemy,10000.0)
	controller.advance(0.016, sim.enemies, sim.events, true)
	check(controller.live.is_empty() and controller.deaths.size() == 1, "one directional fall on death")
	controller.advance(0.6, sim.enemies, none, true)
	check(float(controller.deaths[0].age) == Spitter.DEATH_DURATION, "fall holds final pose")
	check(Spitter.texture("death",Vector2.RIGHT,100.0) == Spitter.texture("death",Vector2.RIGHT,0.49), "death cannot loop to standing")
	controller.advance(0.016, sim.enemies, none, false)
	check(controller.deaths.is_empty(), "gore option removes finished remains")
	var deaths: Array[Dictionary] = [{"type":"death","kind":"spitter","position":enemy.position,"direction":Vector2.RIGHT}]
	for i in range(60):
		controller.advance(0.01, sim.enemies, deaths, true)
	check(controller.deaths.size() == Spitter.MAX_CORPSES, "bounded cosmetic remains")
	for i in range(10):
		controller.reset()
		check(controller.live.is_empty() and controller.deaths.is_empty(), "clean spitter reset")
	print("SPITTER_TESTS: %d passed, %d failed" % [passed, failed])
	quit(0 if failed == 0 else 1)
