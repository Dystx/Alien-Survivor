extends SceneTree
const Warden = preload("res://scripts/warden_animation.gd")
const Sim = preload("res://scripts/simulation.gd")
var passed: int = 0
var failed: int = 0
func check(ok: bool, label: String) -> void:
	if ok:
		passed += 1
		print("PASS ", label)
	else:
		failed += 1
		push_error(label)
func _initialize() -> void:
	var counts := {"idle":4,"move":6,"charge_windup":8,"charge":6,"acid_attack":6,"pulse_attack":8,"recovery":4,"hit":2,"phase_transition":6,"death":10}
	check(Warden.Frames.get_animation_names().size() == 40, "40 real boss clips")
	var total: int = 0
	for clip: String in counts:
		for d: String in ["e","s","w","n"]:
			var key := StringName(clip + "_" + d)
			check(Warden.Frames.get_frame_count(key) == int(counts[clip]), "complete " + String(key))
			total += Warden.Frames.get_frame_count(key)
	check(total == 240, "240 actual frame slots")
	var sim := Sim.new()
	sim.start_boss_preview()
	var boss = sim.boss
	boss.warning = 0.0
	var visual := Warden.new()
	visual.advance(0.016, boss)
	check(visual.active and visual.clip == "idle", "single boss binds at its ground pivot")
	boss.position.x += 4.0
	visual.advance(0.016, boss)
	check(visual.clip == "move" and visual.cycle > 0.0, "actual displacement advances gait")
	var cycle: float = visual.cycle
	visual.advance(0.016, boss)
	check(visual.clip == "idle" and visual.cycle == cycle, "blocked movement stops feet")
	var health: float = sim.health
	var boss_health: float = boss.health
	for action: String in ["fan", "charge", "pulse"]:
		boss.action_timer = 0.0
		boss.recovery = 0.0
		boss.windup = 0.0
		boss.flash = 0.0
		visual.reset()
		visual.advance(0.016, boss)
		sim._arm_attack(boss, action, Vector2.LEFT, 0.95)
		visual.advance(0.016, boss)
		var expected: String = {"fan":"acid_attack","charge":"charge_windup","pulse":"pulse_attack"}[action]
		check(visual.clip == expected and visual.age == 0.0, action + " begins its warning pose")
		boss.windup = 0.1
		boss.direction = Vector2.UP
		boss.flash = 0.08
		visual.advance(0.016, boss)
		check(visual.clip == expected, action + " warning not replaced by hit")
		check(visual.direction == Warden.Iso.project(Vector2.LEFT), action + " keeps locked aim")
		var index := Warden.frame_index(visual.clip, visual.direction, visual.age)
		check(index < 3 if action == "fan" else (index < 4 if action == "pulse" else index < 8), action + " cannot show release before simulation")
		var frozen: float = visual.age
		visual.advance(0.0, boss)
		check(visual.age == frozen, action + " pause freezes visual")
		boss.windup = 0.0
		var projectiles_before: int = sim.enemy_projectiles.size()
		var hazards_before: int = sim.hazards.size()
		sim._execute_attack(boss)
		visual.advance(0.016, boss)
		check(visual.clip == ("charge" if action == "charge" else expected), action + " release selected by simulation")
		if action == "fan":
			check(sim.enemy_projectiles.size() == projectiles_before + 5 and Warden.frame_index(visual.clip,visual.direction,visual.age) == 3, "five projectiles and matching first emission frame")
		elif action == "pulse":
			check(sim.hazards.size() == hazards_before + 1 and Warden.frame_index(visual.clip,visual.direction,visual.age) == 4, "pulse hazard and matching release frame")
		else:
			check(boss.recovery > 0.0 and visual.clip == "charge", "recovery timer cannot preempt live dash")
			var dash: float = visual.charge_cycle
			visual.advance(0.016,boss)
			check(visual.charge_cycle == dash, "blocked charging feet hold")
			boss.position.y += 5.0
			visual.advance(0.016,boss)
			check(visual.charge_cycle != dash, "dash gait follows actual displacement")
			boss.action_timer = 0.0
			visual.advance(0.016,boss)
			check(visual.clip == "recovery", "dash end selects recovery")
		check(sim.health == health and boss.health == boss_health, action + " animation deals no damage")
		var shots: int = sim.enemy_projectiles.size()
		visual.advance(0.016,boss)
		check(sim.enemy_projectiles.size() == shots, action + " animation never duplicates projectiles")
	boss.windup = 0.0
	boss.action_timer = 0.0
	boss.recovery = 0.0
	boss.flash = 0.0
	visual.reset()
	boss.enraged = true
	sim._arm_attack(boss, "fan", Vector2.DOWN, 0.95)
	visual.advance(0.016,boss)
	check(visual.phase_pending and visual.clip == "acid_attack", "phase flare waits behind live attack")
	boss.windup = 0.0
	visual.advance(0.3,boss)
	check(visual.clip == "phase_transition" and not visual.phase_pending, "stationary safe gap starts phase flare once")
	visual.advance(0.7,boss)
	check(visual.clip != "phase_transition" and visual.phase_seen, "phase flare finishes without replaying")
	visual.advance(0.3,boss)
	check(not visual.phase_pending, "enrage state cannot repeatedly retrigger flare")
	visual.phase_age = 0.2
	sim._arm_attack(boss, "charge", Vector2.LEFT, 0.95)
	visual.advance(0.016,boss)
	check(visual.clip == "charge_windup" and visual.phase_age < 0.0, "new warning preempts cosmetic phase pose")
	boss.health = 0.0
	visual.advance(0.016,boss)
	check(visual.dead and visual.waiting_for_death() and visual.clip == "death", "death overrides every attack")
	visual.advance_death(0.0)
	check(visual.death_age == 0.0, "paused death remains fixed")
	visual.advance_death(0.6)
	check(visual.waiting_for_death(), "fall still playing before ten frames complete")
	visual.advance_death(2.0)
	check(not visual.waiting_for_death() and Warden.frame_index(visual.clip, visual.direction,visual.age) == 9, "final corpse pose holds")
	boss.health = boss_health
	visual.advance(0.2,boss)
	check(visual.dead, "no resurrection without explicit run reset")
	for i in range(10):
		visual.reset()
		check(not visual.active and not visual.dead and not visual.phase_seen and not visual.waiting_for_death(), "complete boss presentation reset")
	print("WARDEN_TESTS: %d passed, %d failed" % [passed, failed])
	quit(0 if failed == 0 else 1)
