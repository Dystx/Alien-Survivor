extends SceneTree
## Exit status and PASS marker are checked by tools/check.py; no silent skips.
const Simulation = preload("res://scripts/simulation.gd")
const Arena = preload("res://scripts/arena.gd")
const Settings = preload("res://scripts/settings.gd")
var passes: int = 0
var failures: int = 0
const DT: float = 1.0 / 60.0

func _init() -> void:
	_run.call_deferred()

func check(condition: bool, label: String) -> void:
	if condition:
		passes += 1
		print("[PASS] " + label)
	else:
		failures += 1
		print("[FAIL] " + label)

func fresh() -> Simulation:
	var sim := Simulation.new()
	sim.reset(1709)
	sim.spawning_enabled = false
	return sim

func _run() -> void:
	if OS.get_cmdline_user_args().has("--self-test-failure"):
		check(false, "intentional runner self-check")
		quit(1)
		return
	_test_movement()
	_test_geometry()
	_test_combat()
	_test_progression()
	_test_pause_and_results()
	_test_restart_and_randomness()
	_test_settings()
	print("ALIEN_SURVIVOR_TESTS: %d passed, %d failed" % [passes, failures])
	quit(0 if failures == 0 else 1)

func _test_movement() -> void:
	var straight := fresh()
	var diagonal := fresh()
	var origin := straight.player
	for tick in range(30):
		straight.step(DT, Vector2.RIGHT)
		diagonal.step(DT, Vector2.ONE)
	check(absf(straight.player.distance_to(origin) - diagonal.player.distance_to(origin)) < 0.02, "no diagonal movement advantage")
	var sim := fresh()
	sim.player = Vector2(55, 576)
	for tick in range(90):
		sim.step(DT, Vector2.LEFT)
	check(sim.arena.is_clear(sim.player, sim.balance.player_radius), "player remains inside arena boundary")
	var p := Vector2(350, 300)
	for tick in range(120):
		p = sim.arena.move_body(p, Vector2(3, 0), 13)
	check(p.x < 372.0 and sim.arena.is_clear(p, 13), "solid blocker stops horizontal movement")
	p = Vector2(350, 300)
	for tick in range(90):
		p = sim.arena.move_body(p, Vector2(2, 2), 13)
	check(p.y > 450.0 and sim.arena.is_clear(p, 13), "movement slides around a blocker")
	var enemy := sim.add_enemy(Vector2(470, 180))
	sim.player = Vector2(470, 490)
	sim.health = 10000
	sim.cooldown = 1000
	var clear: bool = true
	for tick in range(700):
		sim.step(DT, Vector2.ZERO)
		clear = clear and sim.arena.is_clear(enemy.position, sim.balance.enemy_radius)
	check(clear, "shared navigation never moves an enemy into solid geometry")
	check(enemy.position.y > 365.0, "shared navigation routes around a blocker")

func _test_geometry() -> void:
	check(is_equal_approx(Simulation.circle_hit_t(Vector2.ZERO, Vector2(100, 0), Vector2(50, 0), 10), 0.4), "swept circle finds first impact")
	check(Simulation.circle_hit_t(Vector2.ZERO, Vector2(100, 0), Vector2(50, 30), 10) > 1.0, "swept circle rejects miss")
	check(Simulation.circle_hit_t(Vector2.ZERO, Vector2.ZERO, Vector2.ZERO, 10) == 0.0, "zero-length segment inside circle is safe")
	check(is_equal_approx(Arena.box_hit_t(Vector2.ZERO, Vector2(100, 0), Rect2(40, -10, 20, 20)), 0.4), "wall segment hits first face")
	check(Arena.box_hit_t(Vector2.ZERO, Vector2(0, 100), Rect2(40, 40, 20, 20)) > 1.0, "parallel segment outside wall misses")

func _test_combat() -> void:
	var sim := fresh()
	for tick in range(120):
		sim.step(DT, Vector2.ZERO, Vector2.RIGHT)
	check(sim.shot_count >= 10 and sim.shot_count <= 12, "manual aim cannot bypass rifle cooldown")
	sim = fresh()
	var enemy := sim.add_enemy(sim.player + Vector2(150, 0))
	enemy.speed = 0.0
	for tick in range(90):
		sim.step(DT, Vector2.ZERO)
	check(sim.kills == 1 and sim.enemies.is_empty(), "automatic target fire kills one enemy")
	check(sim.pickups.size() == 1, "enemy kill creates exactly one XP pickup")
	check(not sim.damage_enemy(enemy, 500) and sim.kills == 1, "repeated damage cannot duplicate death rewards")
	sim = fresh()
	sim.player = Vector2(470, 180)
	enemy = sim.add_enemy(Vector2(470, 450))
	enemy.speed = 0.0
	for tick in range(90):
		sim.step(DT, Vector2.ZERO, Vector2.DOWN)
	check(is_equal_approx(enemy.health, sim.balance.enemy_health), "manual bullets cannot shoot through blockers")
	sim = fresh()
	enemy = sim.add_enemy(sim.player + Vector2(20, 0))
	enemy.speed = 0.0
	sim.cooldown = 1000
	for tick in range(30):
		sim.step(DT, Vector2.ZERO)
	check(is_equal_approx(sim.health, sim.max_health - sim.balance.contact_damage), "contact damage observes shared hurt cooldown")
	sim = fresh()
	enemy = sim.add_enemy(sim.player, 2.0)
	for tick in range(30):
		sim.step(DT, Vector2.ZERO)
	check(sim.health == sim.max_health and sim.shot_count == 0, "spawn warning cannot attack or become an auto target")
	check(sim.bullets.size() <= sim.balance.bullet_limit, "bullet count remains bounded")

func _test_progression() -> void:
	var sim := fresh()
	var base_damage := sim.balance.rifle_damage
	sim.xp = sim.xp_needed()
	sim.step(DT, Vector2.ZERO)
	check(sim.phase == Simulation.Phase.UPGRADE and sim.level == 2, "XP opens paused level-up choice")
	check(sim.offers.size() == 3 and sim.offers[0] != sim.offers[1] and sim.offers[1] != sim.offers[2] and sim.offers[0] != sim.offers[2], "upgrade offers are distinct")
	check(not sim.choose_upgrade("unknown"), "unknown upgrade cannot be selected")
	check(sim.choose_upgrade("damage") and sim.rifle_damage() > base_damage, "damage choice changes per-run stats")
	check(sim.balance.rifle_damage == base_damage, "upgrades leave shared Resource immutable")
	check(not sim.choose_upgrade("damage"), "one offer cannot be applied twice")
	sim.xp = sim.xp_needed()
	sim.step(DT, Vector2.ZERO)
	sim.health = 30
	sim.choose_upgrade("health")
	check(sim.max_health == sim.balance.player_health + 20 and sim.health == 65, "field repair applies maximum and current health correctly")
	sim.ranks = {"damage": 5, "rate": 5, "health": 5}
	sim.xp = sim.xp_needed()
	sim.step(DT, Vector2.ZERO)
	check(sim.offers.size() == 1 and sim.offers[0] == "supply", "fully capped catalogue has a valid fallback")
	check(sim.choose_upgrade("supply"), "fallback can be selected")
	sim = fresh()
	sim.xp = 100
	sim.step(DT, Vector2.ZERO)
	var selections: int = 0
	while sim.phase == Simulation.Phase.UPGRADE and selections < 20:
		sim.choose_upgrade(sim.offers[0])
		selections += 1
	check(selections > 1 and sim.phase == Simulation.Phase.RUNNING, "batched XP preserves every earned level")

func _test_pause_and_results() -> void:
	var sim := fresh()
	sim.add_enemy(sim.player + Vector2(80, 0))
	sim.step(DT, Vector2.ZERO)
	var before_time := sim.elapsed
	var before_position: Vector2 = sim.enemies[0].position
	var before_health := sim.health
	sim.pause()
	for tick in range(180):
		sim.step(DT, Vector2.ONE, Vector2.RIGHT)
	check(sim.elapsed == before_time and sim.enemies[0].position == before_position and sim.health == before_health, "pause freezes clock, AI and damage")
	sim.resume()
	check(sim.phase == Simulation.Phase.RUNNING, "resume restores running state")
	sim = fresh()
	sim.xp = sim.xp_needed()
	sim.step(DT, Vector2.ZERO)
	sim.pause()
	sim.resume()
	check(sim.phase == Simulation.Phase.UPGRADE, "pausing an upgrade restores the choice rather than skipping it")
	sim = fresh()
	sim.time_limit = DT
	sim.step(DT, Vector2.ZERO)
	check(sim.phase == Simulation.Phase.RESULTS and sim.result == "EXTRACTION READY", "time limit ends run exactly once")
	var final_time := sim.elapsed
	sim.step(DT, Vector2.RIGHT)
	check(sim.elapsed == final_time, "results do not advance gameplay")
	sim = fresh()
	sim.time_limit = DT
	sim.health = 0.0
	sim.step(DT, Vector2.ZERO)
	check(sim.result == "CONTAINMENT LOST", "death wins over simultaneous extraction")

func _test_restart_and_randomness() -> void:
	var sim := fresh()
	var clean: bool = true
	for restart in range(10):
		var enemy := sim.add_enemy(sim.player)
		sim.damage_enemy(enemy, 10000)
		sim.ranks.damage = 5
		sim.reset(1709)
		clean = clean and sim.enemies.is_empty() and sim.bullets.is_empty() and sim.pickups.is_empty()
		clean = clean and sim.kills == 0 and sim.level == 1 and sim.next_enemy_id == 1 and sim.elapsed == 0.0 and sim.ranks.damage == 0
	check(clean, "ten restarts clear all run state and live objects")
	var a := fresh()
	var b := fresh()
	a.spawning_enabled = true
	b.spawning_enabled = true
	for tick in range(120):
		a.step(DT, Vector2.ZERO)
		b.step(DT, Vector2.ZERO)
	var equal := a.enemies.size() == b.enemies.size()
	for index in range(mini(a.enemies.size(), b.enemies.size())):
		equal = equal and a.enemies[index].position.is_equal_approx(b.enemies[index].position)
	check(equal and not a.enemies.is_empty(), "same seed and inputs repeat spawn state on this engine")
	var ids: Dictionary = {}
	for enemy in a.enemies:
		ids[enemy.id] = true
	check(ids.size() == a.enemies.size(), "live enemy IDs are unique")
	a.seed_benchmark(100)
	check(a.enemies.size() == 100 and not a.spawning_enabled, "diagnostic scenario actually creates requested live actors")
	var all_clear := true
	for enemy in a.enemies:
		all_clear = all_clear and a.arena.is_clear(enemy.position, a.balance.enemy_radius)
	check(all_clear, "diagnostic spawn positions respect geometry")

func _test_settings() -> void:
	var path := "user://automated_test_settings.cfg"
	for suffix in ["", ".tmp", ".bak"]:
		if FileAccess.file_exists(path + suffix):
			DirAccess.remove_absolute(path + suffix)
	var settings := Settings.new(path)
	check(settings.values.muted == false, "missing settings use defaults")
	check(settings.set_value("muted", true) == OK, "settings write succeeds")
	var loaded := Settings.new(path)
	check(loaded.values.muted == true, "settings survive reload")
	check(loaded.set_value("touch_radius", 1000.0) == OK and loaded.values.touch_radius == 100.0, "touch radius is clamped")
	check(loaded.set_value("unknown", true) == ERR_INVALID_PARAMETER, "unknown settings are rejected")
	var invalid := ConfigFile.new()
	invalid.set_value("meta", "version", 999)
	invalid.save(path)
	loaded = Settings.new(path)
	check(loaded.recovered_backup and loaded.values.muted, "unsupported primary schema recovers previous-good backup")
	for suffix in ["", ".tmp", ".bak"]:
		if FileAccess.file_exists(path + suffix):
			DirAccess.remove_absolute(path + suffix)
