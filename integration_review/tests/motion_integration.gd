extends SceneTree
const Bank = preload("res://scripts/motion_bank.gd")
const Motion = preload("res://scripts/actor_motion.gd")
const Simulation = preload("res://scripts/simulation.gd")
var passed: int = 0
var failed: int = 0
func check(value: bool, label: String) -> void:
	if value:
		passed += 1
		print("[PASS] " + label)
	else:
		failed += 1
		print("[FAIL] " + label)
func _initialize() -> void:
	_run.call_deferred()
func _run() -> void:
	var bank := Bank.new()
	check(bank.missing.is_empty() and bank.families.size() == 6, "six real actor atlases load")
	var count: int = 0
	var valid: bool = true
	for kind: String in bank.families:
		for clip: String in bank.families[kind].clips:
			var data: Dictionary = bank.families[kind].clips[clip]
			for d: String in data.directions:
				for frame: Dictionary in data.directions[d]:
					count += 1
					valid = valid and frame.texture != null and frame.texture.get_size().x > 0.0 and frame.offset.size() == 2
	check(count == 892 and valid, "all 892 frame regions resolve to textures and pivots")
	check(bank.canonical("boss") == "brood_warden", "simulation boss maps to correct family")
	check(Bank.direction_key(Vector2.RIGHT) == "e" and Bank.direction_key(Vector2.DOWN) == "s" and Bank.direction_key(Vector2.LEFT) == "w" and Bank.direction_key(Vector2.UP) == "n", "screen facing mapping is explicit")
	var start := bank.sample("player", "walk", Vector2.RIGHT, 0.0)
	var next := bank.sample("player", "walk", Vector2.RIGHT, 0.10)
	check(start.texture != next.texture, "walk advances an actual animation frame")
	check(bank.sample("player", "walk", Vector2.RIGHT, bank.duration("player", "walk")).texture == start.texture, "walk loops without changing the anchor")
	var death := bank.sample("player", "death", Vector2.RIGHT, 999.0)
	check(death.texture == bank.families.player.clips.death.directions.e.back().texture, "death holds the last frame")
	check(bank.sample("runner", "move", Vector2.RIGHT, 0.0, 1.0).texture == bank.families.runner.clips.move.directions.e.back().texture, "explicit action progress is bounded")
	var motion := Motion.new()
	motion.reset(Vector2.ZERO)
	motion.advance_player(0.02, Vector2.ZERO, Vector2.RIGHT, 100.0, 0.18, [])
	check(motion.player_clip == "idle", "blocked or stationary player idles")
	motion.advance_player(0.02, Vector2(2,0), Vector2.RIGHT, 100.0, 0.18, [])
	check(motion.player_clip == "walk" and motion.gait_phase > 0.0, "gait follows actual forward displacement")
	motion.advance_player(0.02, Vector2.ZERO, Vector2.RIGHT, 100.0, 0.18, [])
	check(motion.player_clip == "walk_back", "backpedal clip selected")
	motion.advance_player(0.02, Vector2(0,2), Vector2.RIGHT, 100.0, 0.18, [])
	check(motion.player_clip == "strafe_right", "strafe clip selected")
	var events: Array[Dictionary] = [{"type":"shot"}]
	motion.advance_player(0.02, Vector2(0,2), Vector2.RIGHT, 100.0, 0.18, events)
	check(motion.player_clip == "shoot", "stationary shot selects firing clip")
	motion.advance_player(0.02, Vector2(0,2), Vector2.RIGHT, 0.0, 0.18, [])
	motion.advance_result(0.25)
	check(motion.player_clip == "death" and motion.death_age > 0.0, "death continues as presentation after simulation stops")
	var sim := Simulation.new()
	sim.reset()
	var enemy := sim.add_enemy(sim.player + Vector2(200,0), 0.0, "charger")
	sim._arm_attack(enemy,"charge",Vector2.LEFT,0.6)
	motion.advance_enemy(enemy,0.02,sim.player)
	check(motion.states[enemy.id].clip == "windup", "charger warning uses wind-up animation")
	enemy.windup = 0.0
	enemy.action_timer = 0.3
	motion.advance_enemy(enemy,0.02,sim.player)
	check(motion.states[enemy.id].clip == "charge", "charge action uses charge cycle")
	motion.prune({})
	check(motion.states.is_empty(), "dead entity presentation state is pruned")
	motion.reset(sim.player)
	check(motion.player_clip == "idle" and motion.death_age < 0.0 and motion.states.is_empty(), "restart resets presentation state")
	print("HUMAN_MOTION_TESTS: %d passed, %d failed" % [passed, failed])
	quit(0 if failed == 0 else 1)
