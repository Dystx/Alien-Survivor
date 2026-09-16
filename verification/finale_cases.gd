
func _test_finale() -> void:
	var sim := fresh()
	sim.finale_enabled = true
	sim.time_limit = DT
	sim.step(DT, Vector2.ZERO)
	check(sim.finale_started and sim.boss != null, "time limit begins a real boss finale")
	check(sim.phase == Simulation.Phase.RUNNING, "timer alone cannot win the finale")
	check(sim.arena.is_clear(sim.boss.position, sim.boss.radius), "boss spawns clear of world geometry")
	var boss_id: int = sim.boss.id
	for tick in range(30):
		sim.step(DT, Vector2.ZERO)
	check(sim.boss.id == boss_id and sim.enemies.size() == 1, "finale spawns exactly one boss")
	check(sim.boss.warning > 0.0 and sim.health == sim.max_health, "boss entry warning cannot attack")
	sim.boss.warning = 0.0
	sim.boss.health = sim.boss.max_health * 0.49
	sim.cooldown = 1000.0
	sim.step(DT, Vector2.ZERO)
	check(sim.boss.enraged, "half health enters phase two")
	sim.damage_enemy(sim.boss, 100000.0)
	sim.step(DT, Vector2.ZERO)
	check(sim.phase == Simulation.Phase.RESULTS and sim.result == "BROOD WARDEN ELIMINATED", "boss defeat produces victory")
	check(sim.kills == 1, "boss reward happens once")
	sim.reset()
	check(sim.boss == null and not sim.finale_started and sim.hazards.is_empty(), "restart clears boss and hazard state")
	sim.start_boss_preview()
	check(sim.finale_started and sim.ranks.damage == 3 and sim.health == 160, "boss preview uses its declared upgraded loadout")
	sim.damage_enemy(sim.boss, 100000.0)
	sim.health = 0.0
	sim.step(DT, Vector2.ZERO)
	check(sim.result == "CONTAINMENT LOST", "simultaneous boss and player death resolves as defeat")

func _test_telegraphs() -> void:
	var sim := fresh()
	sim.cooldown = 1000
	var charger := sim.add_enemy(sim.player + Vector2(200, 0), 0.0, "charger")
	charger.skill_cooldown = 0
	var origin := charger.position
	sim.step(DT, Vector2.ZERO)
	check(charger.windup > 0.70 and charger.position.is_equal_approx(origin), "charger warns before moving")
	var locked := charger.action_direction
	sim.player += Vector2(0, 70)
	for tick in range(15):
		sim.step(DT, Vector2.ZERO)
	check(charger.action_direction.is_equal_approx(locked), "charge aim stays locked during warning")
	for tick in range(70):
		sim.step(DT, Vector2.ZERO)
	check(charger.position.distance_to(origin) > 50, "charge executes after its wind-up")
	check(sim.arena.is_clear(charger.position, charger.radius), "charge respects blocker geometry")
	sim = fresh()
	sim.cooldown = 1000
	var spitter := sim.add_enemy(sim.player + Vector2(260, 0), 0.0, "spitter")
	spitter.skill_cooldown = 0
	sim.step(DT, Vector2.ZERO)
	check(spitter.windup > 0.60 and sim.enemy_projectiles.is_empty(), "spitter warns before producing a projectile")
	for tick in range(43):
		sim.step(DT, Vector2.ZERO)
	check(not sim.enemy_projectiles.is_empty(), "spitter fires when warning ends")
	sim.pause()
	var p: Vector2 = sim.enemy_projectiles[0].position
	for tick in range(20):
		sim.step(DT, Vector2.ZERO)
	check(sim.enemy_projectiles[0].position == p, "pause freezes hostile shots and warnings")

func _test_hostile_sweeps_and_limits() -> void:
	var sim := fresh()
	sim.cooldown = 1000
	sim._spawn_enemy_projectile(sim.player - Vector2(70, 0), Vector2.RIGHT)
	sim.enemy_projectiles[0].velocity = Vector2(12000, 0)
	sim.step(DT, Vector2.ZERO)
	check(sim.health < sim.max_health, "swept hostile collision catches a fast projectile")
	sim = fresh()
	sim.player = Vector2(470, 470)
	sim.cooldown = 1000
	sim._spawn_enemy_projectile(Vector2(470, 180), Vector2.DOWN)
	sim.enemy_projectiles[0].velocity = Vector2(0, 30000)
	sim.enemy_projectiles[0].remaining = 900
	sim.step(DT, Vector2.ZERO)
	check(sim.health == sim.max_health and sim.enemy_projectiles.is_empty(), "earlier wall impact protects from hostile shots")
	sim = fresh()
	for i in range(200):
		sim._spawn_enemy_projectile(sim.player, Vector2.RIGHT)
		sim._add_hazard(sim.player, 28, "acid", 2.0, 6)
	check(sim.enemy_projectiles.size() == Simulation.HOSTILE_SHOT_CAP, "hostile projectile count has a hard cap")
	check(sim.hazards.size() == Simulation.HAZARD_CAP, "damaging puddles have a hard cap")
	sim.pause()
	var life: float = sim.hazards[0].life
	sim.step(1.0, Vector2.ZERO)
	check(sim.hazards[0].life == life, "pause freezes hazard lifetime")
	sim.reset()
	check(sim.enemy_projectiles.is_empty() and sim.hazards.is_empty(), "restart clears all hostile attacks")
	var brute := sim.add_enemy(sim.player + Vector2(100, 0), 0.0, "brute")
	var hp := brute.health
	sim.damage_enemy(brute, 100)
	check(is_equal_approx(brute.health, maxf(0.0, hp-80)), "brute armour applies its documented reduction")

func _test_projection() -> void:
	var projection = load("res://scripts/projection.gd")
	var point := Vector2(1000, 680)
	check(projection.unproject(projection.project(point)).is_equal_approx(point), "isometric ground projection round-trips")
	var basis: Transform2D = projection.input_basis()
	var screen_right: Vector2 = projection.project(basis * Vector2.RIGHT)
	check(screen_right.is_equal_approx(Vector2.RIGHT), "screen-right controls remain screen-right in isometric view")
	var dx: Vector2 = projection.project(Vector2(64, 0))
	var dy: Vector2 = projection.project(Vector2(0, 64))
	check(dx == Vector2(48,24) and dy == Vector2(-48,24), "floor tile neighbors join on a precise 2-to-1 grid")
