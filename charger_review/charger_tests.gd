extends SceneTree
const Charger = preload("res://scripts/charger_animation.gd")
const Sim = preload("res://scripts/simulation.gd")
var passed: int = 0
var failed: int = 0
func check(ok: bool, label: String) -> void:
	if ok:
		passed += 1
		print("PASS ",label)
	else:
		failed += 1
		push_error(label)
func _initialize() -> void:
	var counts := {"idle":4,"move":6,"windup":4,"charge":6,"recovery":4,"hit":2,"death":5}
	check(Charger.Frames.get_animation_names().size() == 28,"28 real charger clips")
	var total: int = 0
	for clip: String in counts:
		for d: String in ["e","s","w","n"]:
			var key := StringName(clip+"_"+d)
			check(Charger.Frames.get_frame_count(key) == counts[clip],"complete "+String(key))
			total += Charger.Frames.get_frame_count(key)
	check(total == 124,"124 real frames")
	var sim := Sim.new()
	sim.reset()
	sim.spawning_enabled = false
	sim.finale_enabled = false
	var enemy = sim.add_enemy(sim.player+Vector2(140,50),0.0,"charger")
	var controller := Charger.new()
	var none: Array[Dictionary] = []
	controller.advance(0.016,sim.enemies,none,true)
	check(controller.live[enemy.id].clip == "idle","spawn starts idle")
	enemy.position.x += 4.0
	controller.advance(0.016,sim.enemies,none,true)
	check(controller.live[enemy.id].clip == "move","movement from displacement")
	var cycle: float = controller.live[enemy.id].move_cycle
	controller.advance(0.016,sim.enemies,none,true)
	check(controller.live[enemy.id].clip == "idle" and controller.live[enemy.id].move_cycle == cycle,"blocked gait stops")
	sim._arm_attack(enemy,"charge",Vector2.LEFT,0.75)
	controller.advance(0.016,sim.enemies,sim.events,true)
	check(controller.live[enemy.id].clip == "windup" and controller.live[enemy.id].age == 0.0,"warning starts braced sequence")
	var locked_direction: Vector2 = controller.live[enemy.id].direction
	enemy.direction = Vector2.UP
	controller.advance(0.016,sim.enemies,none,true)
	check(controller.live[enemy.id].direction == locked_direction,"warning uses locked action direction")
	enemy.windup = 0.4
	controller.advance(0.016,sim.enemies,none,true)
	check(controller.live[enemy.id].age > 0.0,"warning follows timer")
	var freeze: float = controller.live[enemy.id].age
	controller.advance(0.0,sim.enemies,none,true)
	check(controller.live[enemy.id].age == freeze,"pause holds warning")
	enemy.flash = 0.08
	controller.advance(0.016,sim.enemies,none,true)
	check(controller.live[enemy.id].clip == "windup","hit cannot hide telegraph")
	enemy.windup = 0.0
	sim._execute_attack(enemy)
	var health_before: float = sim.health
	var position_before: Vector2 = enemy.position
	var duration_before: float = enemy.action_timer
	controller.advance(0.016,sim.enemies,none,true)
	check(controller.live[enemy.id].clip == "charge","simulation dash selects charge")
	check(enemy.position == position_before and enemy.action_timer == duration_before and sim.health == health_before,"view cannot move enemy or alter damage and timers")
	enemy.position.x -= 5.0
	controller.advance(0.016,sim.enemies,none,true)
	check(controller.live[enemy.id].charge_cycle > 0.0,"real dash distance drives charge gait")
	cycle = controller.live[enemy.id].charge_cycle
	controller.advance(0.016,sim.enemies,none,true)
	check(controller.live[enemy.id].charge_cycle == cycle,"wall-blocked charge has no skating feet")
	check(controller.live[enemy.id].direction == locked_direction,"charge heading stays locked")
	check(controller.live[enemy.id].clip == "charge","prearmed recovery cannot preempt a dash")
	enemy.action_timer = 0.0
	controller.advance(0.016,sim.enemies,none,true)
	check(controller.live[enemy.id].clip == "recovery" and controller.live[enemy.id].age == 0.0,"recovery starts only after dash")
	enemy.recovery = 0.25
	controller.advance(0.016,sim.enemies,none,true)
	check(controller.live[enemy.id].age > 0.0,"recovery tracks remaining simulation time")
	enemy.recovery = 0.0
	enemy.flash = 0.0
	controller.advance(0.3,sim.enemies,none,true)
	enemy.flash = 0.08
	controller.advance(0.016,sim.enemies,none,true)
	check(controller.live[enemy.id].clip == "hit","nonattacking hit pose")
	controller.advance(0.016,sim.enemies,none,true)
	check(controller.live[enemy.id].hit_age > 0.0,"held flash does not restart hit")
	check(controller.for_enemy(enemy) != null,"actual texture resolves")
	sim.events.clear()
	sim.damage_enemy(enemy,10000.0)
	controller.advance(0.016,sim.enemies,sim.events,true)
	check(controller.live.is_empty() and controller.deaths.size() == 1,"one fall removes live state")
	controller.advance(0.6,sim.enemies,none,true)
	check(float(controller.deaths[0].age) == Charger.DEATH_DURATION,"corpse holds final frame")
	check(Charger.texture("death",Vector2.RIGHT,100.0) == Charger.texture("death",Vector2.RIGHT,0.49),"death cannot loop")
	controller.advance(0.016,sim.enemies,none,false)
	check(controller.deaths.is_empty(),"corpse setting removes completed fall")
	var deaths: Array[Dictionary] = [{"type":"death","kind":"charger","position":enemy.position,"direction":Vector2.LEFT}]
	for i in range(55):
		controller.advance(0.01,sim.enemies,deaths,true)
	check(controller.deaths.size() == Charger.MAX_CORPSES,"bounded remains")
	for i in range(10):
		controller.reset()
		check(controller.live.is_empty() and controller.deaths.is_empty(),"clean restart")
	print("CHARGER_TESTS: %d passed, %d failed" % [passed,failed])
	quit(0 if failed == 0 else 1)
