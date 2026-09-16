extends RefCounted
const Balance = preload("res://scripts/balance.gd")
const Arena = preload("res://scripts/arena.gd")
const SpatialGrid = preload("res://scripts/spatial_grid.gd")
const DEFAULT_BALANCE = preload("res://data/default_balance.tres")
enum Phase { MENU, RUNNING, PAUSED, UPGRADE, RESULTS }
const ENEMY_TYPES := {
	"runner": {"health": 1.0, "speed": 1.0, "radius": 13.0, "touch": 1.0},
	"spitter": {"health": 1.15, "speed": 0.84, "radius": 14.0, "touch": 0.8},
	"charger": {"health": 1.35, "speed": 0.92, "radius": 15.0, "touch": 1.2},
	"brute": {"health": 2.2, "speed": 0.66, "radius": 18.0, "touch": 1.5},
	"boss": {"health": 1.0, "speed": 0.72, "radius": 31.0, "touch": 1.8}
}
class Enemy extends RefCounted:
	var id: int = 0
	var kind: String = "runner"
	var max_health: float = 35.0
	var windup: float = 0.0
	var recovery: float = 0.0
	var action_kind: String = ""
	var attack_index: int = 0
	var enraged: bool = false
	var position := Vector2.ZERO
	var direction := Vector2.DOWN
	var health: float = 35.0
	var speed: float = 58.0
	var radius: float = 13.0
	var touch_damage: float = 10.0
	var warning: float = 0.75
	var flash: float = 0.0
	var age: float = 0.0
	var rewarded: bool = false
	var skill_cooldown: float = 0.0
	var action_timer: float = 0.0
	var action_direction := Vector2.ZERO
class Bullet extends RefCounted:
	var position := Vector2.ZERO
	var previous := Vector2.ZERO
	var velocity := Vector2.ZERO
	var damage: float = 0.0
	var remaining: float = 450.0
class EnemyProjectile extends RefCounted:
	var position := Vector2.ZERO
	var velocity := Vector2.ZERO
	var damage: float = 0.0
	var remaining: float = 0.0
	var radius: float = 8.0
	var kind: String = "acid"
class Pickup extends RefCounted:
	var position := Vector2.ZERO
	var amount: int = 1
	var age: float = 0.0
const UPGRADES: Dictionary = {
	"damage": {"name": "HARDENED ROUNDS", "detail": "+25% base rifle damage", "tag": "BALLISTICS", "cap": 5},
	"rate": {"name": "OVERCLOCKED FEED", "detail": "+18% base firing speed", "tag": "MECHANISM", "cap": 5},
	"health": {"name": "FIELD REPAIR", "detail": "+20 maximum health. Restore 35 health.", "tag": "SURVIVAL", "cap": 5}
}
var balance: Balance = DEFAULT_BALANCE
var arena: Arena = Arena.new()
var grid: SpatialGrid = SpatialGrid.new()
var phase: Phase = Phase.MENU
var return_phase: Phase = Phase.RUNNING
var player := Arena.SIZE / 2.0
var facing := Vector2.RIGHT
var health: float = 100.0
var max_health: float = 100.0
var elapsed: float = 0.0
var cooldown: float = 0.0
var hurt_timer: float = 0.0
var spawn_timer: float = 0.25
var time_limit: float = 300.0
var level: int = 1
var xp: int = 0
var kills: int = 0
var shot_count: int = 0
var seed_value: int = 1709
var next_enemy_id: int = 1
var enemy_cap: int = 150
var result: String = ""
var ranks: Dictionary = {"damage": 0, "rate": 0, "health": 0}
var offers: Array[String] = []
var enemies: Array[Enemy] = []
var bullets: Array[Bullet] = []
var enemy_projectiles: Array[EnemyProjectile] = []
var pickups: Array[Pickup] = []
var events: Array[Dictionary] = []
var spawn_rng := RandomNumberGenerator.new()
var offer_rng := RandomNumberGenerator.new()
var spawning_enabled: bool = true
var finale_enabled: bool = true
var finale_started: bool = false
var boss: Enemy
var hazards: Array[Dictionary] = []
const HOSTILE_SHOT_CAP: int = 96
const HAZARD_CAP: int = 20
func reset(run_seed: int = 1709) -> void:
	phase = Phase.RUNNING
	return_phase = Phase.RUNNING
	player = Arena.SIZE / 2.0
	facing = Vector2.RIGHT
	health = balance.player_health
	max_health = balance.player_health
	elapsed = 0.0
	cooldown = 0.0
	hurt_timer = 0.0
	spawn_timer = 0.25
	time_limit = balance.duration
	level = 1
	xp = 0
	kills = 0
	shot_count = 0
	seed_value = run_seed
	next_enemy_id = 1
	enemy_cap = balance.enemy_limit
	result = ""
	ranks = {"damage": 0, "rate": 0, "health": 0}
	offers.clear()
	enemies.clear()
	bullets.clear()
	enemy_projectiles.clear()
	hazards.clear()
	finale_started = false
	finale_enabled = true
	boss = null
	pickups.clear()
	events.clear()
	spawn_rng.seed = run_seed
	offer_rng.seed = run_seed ^ 0x73b1
	spawning_enabled = true
	arena.goal_cell = Vector2i(-1, -1)
	arena.update_field(player)
	grid.rebuild(enemies)
func rifle_damage() -> float:
	return balance.rifle_damage * (1.0 + 0.25 * int(ranks.damage))
func rifle_interval() -> float:
	return balance.rifle_interval / (1.0 + 0.18 * int(ranks.rate))
func xp_needed() -> int:
	return 8 + (level - 1) * 5
func pause() -> void:
	if phase == Phase.RUNNING or phase == Phase.UPGRADE:
		return_phase = phase
		phase = Phase.PAUSED
func resume() -> void:
	if phase == Phase.PAUSED:
		phase = return_phase
func step(dt: float, move: Vector2, manual_aim: Vector2 = Vector2.ZERO) -> void:
	events.clear()
	if phase != Phase.RUNNING or dt <= 0.0:
		return
	elapsed += dt
	hurt_timer = maxf(0.0, hurt_timer - dt)
	player = arena.move_body(player, move.limit_length() * balance.player_speed * dt, balance.player_radius)
	arena.update_field(player)
	_move_enemies(dt)
	grid.rebuild(enemies)
	cooldown = maxf(0.0, cooldown - dt)
	var aim := manual_aim.normalized() if manual_aim.length_squared() > 0.01 else _auto_aim()
	if aim != Vector2.ZERO:
		facing = aim
		if cooldown <= 0.000001 and bullets.size() < balance.bullet_limit:
			_fire(aim)
			cooldown = rifle_interval()
	_update_bullets(dt)
	_update_enemy_projectiles(dt)
	_update_hazards(dt)
	_collect_pickups(dt)
	if health <= 0.0:
		_finish("CONTAINMENT LOST")
		return
	if finale_started and boss != null and boss.health <= 0.0:
		_finish("BROOD WARDEN ELIMINATED")
		return
	if elapsed >= time_limit and not finale_started:
		if finale_enabled:
			_begin_finale()
		else:
			elapsed = time_limit
			_finish("EXTRACTION READY")
			return
	if xp >= xp_needed():
		_open_upgrade()
		return
	if spawning_enabled:
		spawn_timer -= dt
		if spawn_timer <= 0.0:
			spawn_timer = 1.9 if finale_started else maxf(0.15, 0.65 - elapsed * 0.00145)
			var cap := mini(enemy_cap, 24) if finale_started else enemy_cap
			if enemies.size() < cap:
				_spawn_random()
func _move_enemies(dt: float) -> void:
	grid.rebuild(enemies)
	for enemy in enemies:
		enemy.age += dt
		enemy.flash = maxf(0.0, enemy.flash - dt)
		enemy.skill_cooldown = maxf(0.0, enemy.skill_cooldown - dt)
		if enemy.warning > 0.0:
			enemy.warning = maxf(0.0, enemy.warning - dt)
			continue
		if enemy.health <= 0.0:
			continue
		var to_player := enemy.position.direction_to(player)
		var distance := enemy.position.distance_to(player)
		var flow := arena.direction_to(enemy.position, player, enemy.radius)
		var separation := Vector2.ZERO
		for index in grid.query(enemy.position, enemy.radius + 34.0):
			var other: Enemy = enemies[index]
			var offset := enemy.position - other.position
			var combined := enemy.radius + other.radius
			var distance_sq := offset.length_squared()
			if other.id != enemy.id and distance_sq < combined * combined and distance_sq > 0.01:
				separation += offset.normalized() * (1.0 - sqrt(distance_sq) / combined)
		var velocity := _enemy_velocity(enemy, flow, to_player, distance, separation, dt)
		var delta := velocity * dt
		var substeps := maxi(1, ceili(delta.length() / maxf(4.0, enemy.radius * 0.5)))
		for substep in range(substeps):
			enemy.position = arena.move_body(enemy.position, delta / float(substeps), enemy.radius)
		if velocity.length_squared() > 1.0:
			enemy.direction = velocity.normalized()
		if enemy.position.distance_squared_to(player) < pow(balance.player_radius + enemy.radius, 2):
			if hurt_timer <= 0.0:
				health = maxf(0.0, health - enemy.touch_damage)
				hurt_timer = balance.hurt_interval
				events.append({"type": "hurt", "position": player})
func _enemy_velocity(enemy: Enemy, flow: Vector2, to_player: Vector2, distance: float, separation: Vector2, dt: float) -> Vector2:
	if enemy.kind == "boss" and not enemy.enraged and enemy.health <= enemy.max_health * 0.5:
		enemy.enraged = true
		events.append({"type": "boss_phase", "position": enemy.position})
	if enemy.windup > 0.0:
		enemy.windup = maxf(0.0, enemy.windup - dt)
		enemy.direction = enemy.action_direction
		if enemy.windup <= 0.0:
			_execute_attack(enemy)
		return Vector2.ZERO
	if enemy.action_timer > 0.0:
		enemy.action_timer = maxf(0.0, enemy.action_timer - dt)
		if enemy.action_kind == "charge":
			return enemy.action_direction * (330.0 if enemy.kind == "boss" else 285.0)
		return Vector2.ZERO
	if enemy.recovery > 0.0:
		enemy.recovery = maxf(0.0, enemy.recovery - dt)
		return Vector2.ZERO
	var clear := arena.wall_hit_t(enemy.position, player, enemy.radius) > 1.0
	match enemy.kind:
		"spitter":
			if distance < 130.0 and clear:
				return (-to_player + separation).limit_length() * enemy.speed
			if distance <= 340.0 and clear:
				if enemy.skill_cooldown <= 0.0:
					_arm_attack(enemy, "spit", to_player, 0.65)
				return separation.limit_length() * enemy.speed * 0.3
		"charger":
			if distance > 60.0 and distance <= 290.0 and clear and enemy.skill_cooldown <= 0.0:
				_arm_attack(enemy, "charge", to_player, 0.75)
				return Vector2.ZERO
		"boss":
			if distance <= 360.0 and clear and enemy.skill_cooldown <= 0.0:
				var attacks: Array[String] = ["fan", "charge", "pulse"]
				var action: String = attacks[enemy.attack_index % attacks.size()]
				enemy.attack_index += 1
				if action == "pulse" and distance > 190.0:
					action = "fan"
				_arm_attack(enemy, action, to_player, 1.05 if action == "pulse" else 0.95)
				return Vector2.ZERO
	var force := 1.4 if enemy.kind == "brute" else 1.2
	return (flow + separation * force).limit_length() * enemy.speed
func _arm_attack(enemy: Enemy, action: String, aim: Vector2, duration: float) -> void:
	enemy.action_kind = action
	enemy.action_direction = aim.normalized()
	enemy.direction = enemy.action_direction
	enemy.windup = duration
	enemy.skill_cooldown = 2.8 if enemy.kind == "boss" else 2.2
	if enemy.enraged:
		enemy.skill_cooldown *= 0.75
	events.append({"type": "warning", "position": enemy.position, "kind": action})
func _execute_attack(enemy: Enemy) -> void:
	match enemy.action_kind:
		"charge":
			enemy.action_timer = 0.48 if enemy.kind == "boss" else 0.42
			enemy.recovery = 0.6
		"spit":
			_spawn_enemy_projectile(enemy.position, enemy.action_direction)
			enemy.recovery = 0.35
			events.append({"type": "spit", "position": enemy.position, "direction": enemy.action_direction})
		"fan":
			var count: int = 7 if enemy.enraged else 5
			for i in range(count):
				var angle := (float(i) - float(count - 1) * 0.5) * 0.19
				_spawn_enemy_projectile(enemy.position, enemy.action_direction.rotated(angle), true)
			enemy.recovery = 0.6
			events.append({"type": "spit", "position": enemy.position, "direction": enemy.action_direction})
		"pulse":
			_add_hazard(enemy.position, 124.0 if enemy.enraged else 108.0, "pulse", 0.32, 18.0)
			enemy.recovery = 0.8
			events.append({"type": "blast", "position": enemy.position})
func _spawn_enemy_projectile(point: Vector2, direction: Vector2, boss_shot: bool = false) -> void:
	if enemy_projectiles.size() >= HOSTILE_SHOT_CAP:
		return
	var shot := EnemyProjectile.new()
	shot.position = point
	shot.velocity = direction.normalized() * (220.0 if boss_shot else 205.0)
	shot.damage = 12.0 if boss_shot else 8.0
	shot.remaining = 440.0 if boss_shot else 375.0
	shot.radius = 6.0
	enemy_projectiles.append(shot)
func _update_enemy_projectiles(dt: float) -> void:
	for index in range(enemy_projectiles.size() - 1, -1, -1):
		var shot: EnemyProjectile = enemy_projectiles[index]
		var travel := minf(shot.remaining, shot.velocity.length() * dt)
		var end := shot.position + shot.velocity.normalized() * travel
		var wall_t := arena.wall_hit_t(shot.position, end, shot.radius)
		var player_t := circle_hit_t(shot.position, end, player, balance.player_radius + shot.radius)
		if player_t <= 1.0 and player_t < wall_t:
			shot.position = shot.position.lerp(end, player_t)
			_hurt_player(shot.damage)
			events.append({"type": "acid_hit", "position": shot.position})
			enemy_projectiles.remove_at(index)
		elif wall_t <= 1.0:
			shot.position = shot.position.lerp(end, wall_t)
			events.append({"type": "acid_hit", "position": shot.position})
			enemy_projectiles.remove_at(index)
		else:
			shot.position = end
			shot.remaining -= travel
			if shot.remaining <= 0.0 or not arena.bounds.has_point(end):
				if arena.is_clear(end, 30.0):
					_add_hazard(end, 28.0, "acid", 2.8, 6.0)
				enemy_projectiles.remove_at(index)
func _hurt_player(amount: float) -> void:
	if hurt_timer <= 0.0 and health > 0.0:
		health = maxf(0.0, health - amount)
		hurt_timer = balance.hurt_interval
		events.append({"type": "hurt", "position": player})
func _add_hazard(point: Vector2, radius: float, kind: String, life: float, damage: float) -> void:
	if hazards.size() >= HAZARD_CAP:
		return
	hazards.append({"position": point, "radius": radius, "kind": kind, "life": life, "damage": damage})
func _update_hazards(dt: float) -> void:
	for i in range(hazards.size() - 1, -1, -1):
		var h: Dictionary = hazards[i]
		h.life = float(h.life) - dt
		if float(h.life) <= 0.0:
			hazards.remove_at(i)
			continue
		if player.distance_to(h.position) < float(h.radius) + balance.player_radius:
			if arena.wall_hit_t(h.position, player, 1.0) > 1.0:
				_hurt_player(float(h.damage))
func _begin_finale() -> void:
	if finale_started:
		return
	var point := Vector2.ZERO
	var found := false
	for radius: float in [325.0, 410.0, 240.0]:
		for i in range(16):
			var candidate := player + Vector2.from_angle(TAU * float(i) / 16.0) * radius
			if arena.is_clear(candidate, 38.0):
				point = candidate
				found = true
				break
		if found:
			break
	if not found:
		return
	finale_started = true
	boss = add_enemy(point, 1.8, "boss")
	spawn_timer = 2.0
	events.append({"type": "boss_intro", "position": point})
func start_boss_preview() -> void:
	reset(1709)
	ranks = {"damage": 3, "rate": 2, "health": 3}
	max_health = 160.0
	health = max_health
	elapsed = time_limit
	_begin_finale()
func _auto_aim() -> Vector2:
	var nearest_sq := balance.rifle_range * balance.rifle_range
	var target := Vector2.ZERO
	for index in grid.query(player, balance.rifle_range):
		var enemy: Enemy = enemies[index]
		var distance_sq := player.distance_squared_to(enemy.position)
		if distance_sq < nearest_sq and enemy.health > 0.0 and enemy.warning <= 0.0:
			if arena.wall_hit_t(player, enemy.position, 2.0) > 1.0:
				nearest_sq = distance_sq
				target = player.direction_to(enemy.position)
	return target
func _fire(direction: Vector2) -> void:
	var bullet := Bullet.new()
	bullet.position = player
	bullet.previous = player
	bullet.velocity = direction * balance.bullet_speed
	bullet.damage = rifle_damage()
	bullet.remaining = balance.rifle_range
	bullets.append(bullet)
	shot_count += 1
	events.append({"type": "shot", "position": player, "direction": direction})
static func circle_hit_t(a: Vector2, b: Vector2, center: Vector2, radius: float) -> float:
	var offset := a - center
	var delta := b - a
	if offset.length_squared() <= radius * radius:
		return 0.0
	var length_sq := delta.length_squared()
	if length_sq < 0.000001:
		return 2.0
	var projection := offset.dot(delta)
	var discriminant := projection * projection - length_sq * (offset.length_squared() - radius * radius)
	if discriminant < 0.0:
		return 2.0
	var fraction := (-projection - sqrt(discriminant)) / length_sq
	return fraction if fraction >= 0.0 and fraction <= 1.0 else 2.0
func _update_bullets(dt: float) -> void:
	for bi in range(bullets.size() - 1, -1, -1):
		var bullet: Bullet = bullets[bi]
		bullet.previous = bullet.position
		var travel := minf(bullet.remaining, bullet.velocity.length() * dt)
		var end := bullet.position + bullet.velocity.normalized() * travel
		var closest_t := arena.wall_hit_t(bullet.position, end, 2.0)
		var hit_index: int = -1
		var center := (bullet.position + end) * 0.5
		for index in grid.query(center, travel * 0.5 + 35.0):
			var enemy: Enemy = enemies[index]
			if enemy.health <= 0.0 or enemy.warning > 0.0:
				continue
			var t := circle_hit_t(bullet.position, end, enemy.position, enemy.radius + 2.0)
			if t < closest_t:
				closest_t = t
				hit_index = index
		if closest_t <= 1.0:
			bullet.position = bullet.position.lerp(end, closest_t)
			if hit_index >= 0:
				damage_enemy(enemies[hit_index], bullet.damage)
			else:
				events.append({"type": "spark", "position": bullet.position})
			bullets.remove_at(bi)
		else:
			bullet.position = end
			bullet.remaining -= travel
			if bullet.remaining <= 0.001 or not arena.bounds.has_point(end):
				bullets.remove_at(bi)
	for index in range(enemies.size() - 1, -1, -1):
		if enemies[index].health <= 0.0:
			enemies.remove_at(index)
func damage_enemy(enemy: Enemy, amount: float) -> bool:
	if enemy.rewarded or enemy.health <= 0.0 or amount <= 0.0:
		return false
	var armour := 0.8 if enemy.kind == "brute" else 1.0
	enemy.health = maxf(0.0, enemy.health - amount * armour)
	enemy.flash = 0.08
	events.append({"type": "hit", "position": enemy.position, "kind": enemy.kind})
	if enemy.health <= 0.0:
		enemy.rewarded = true
		kills += 1
		_add_pickup(enemy.position)
		events.append({"type": "death", "position": enemy.position, "direction": enemy.direction, "kind": enemy.kind})
	return true
func _add_pickup(point: Vector2) -> void:
	if pickups.size() >= balance.pickup_limit:
		var best: Pickup = pickups[0]
		for candidate in pickups:
			if candidate.position.distance_squared_to(point) < best.position.distance_squared_to(point):
				best = candidate
		best.amount += 1
		return
	var pickup := Pickup.new()
	pickup.position = point
	pickups.append(pickup)
func _collect_pickups(dt: float) -> void:
	for index in range(pickups.size() - 1, -1, -1):
		var pickup: Pickup = pickups[index]
		pickup.age += dt
		var distance := player.distance_to(pickup.position)
		if distance < 82.0 and arena.wall_hit_t(pickup.position, player, 1.0) > 1.0:
			pickup.position = pickup.position.move_toward(player, 270.0 * dt)
		if player.distance_to(pickup.position) < 16.0:
			xp += pickup.amount
			pickups.remove_at(index)
			events.append({"type": "pickup", "position": player})
func _spawn_random() -> void:
	var kind := _choose_spawn_kind()
	for attempt in range(40):
		var angle := spawn_rng.randf_range(0.0, TAU)
		var candidate := player + Vector2.from_angle(angle) * spawn_rng.randf_range(560.0, 680.0)
		var radius := float(ENEMY_TYPES[kind].radius)
		if arena.is_clear(candidate, radius + 5.0):
			add_enemy(candidate, balance.spawn_warning, kind)
			return
func _choose_spawn_kind() -> String:
	var roll := spawn_rng.randf()
	if elapsed < 45.0:
		return "runner"
	if elapsed < 110.0:
		return "spitter" if roll < 0.20 else "runner"
	if elapsed < 180.0:
		if roll < 0.15:
			return "charger"
		if roll < 0.35:
			return "spitter"
		return "runner"
	if elapsed < 240.0:
		if roll < 0.12:
			return "brute"
		if roll < 0.28:
			return "charger"
		if roll < 0.46:
			return "spitter"
		return "runner"
	if roll < 0.18:
		return "brute"
	if roll < 0.36:
		return "charger"
	if roll < 0.56:
		return "spitter"
	return "runner"
func add_enemy(point: Vector2, warning: float = 0.0, kind: String = "runner") -> Enemy:
	var enemy := Enemy.new()
	enemy.id = next_enemy_id
	next_enemy_id += 1
	enemy.kind = kind if ENEMY_TYPES.has(kind) else "runner"
	var spec: Dictionary = ENEMY_TYPES[enemy.kind]
	enemy.position = point
	enemy.health = balance.enemy_health * float(spec.health) * (1.0 + floorf(elapsed / 60.0) * 0.1)
	enemy.max_health = enemy.health
	if enemy.kind == "boss":
		enemy.health = 1800.0
		enemy.max_health = enemy.health
	enemy.speed = (balance.enemy_speed + minf(30.0, elapsed * 0.085)) * float(spec.speed)
	enemy.radius = float(spec.radius)
	enemy.touch_damage = balance.contact_damage * float(spec.touch)
	enemy.warning = warning
	enemy.skill_cooldown = 0.8
	enemies.append(enemy)
	return enemy
func seed_benchmark(count: int) -> void:
	reset(1709)
	spawning_enabled = false
	elapsed = 210.0
	for index in range(clampi(count, 0, 500)):
		_spawn_random()
	elapsed = 0.0
	finale_enabled = false
func _open_upgrade() -> void:
	xp -= xp_needed()
	level += 1
	offers.clear()
	for key: String in UPGRADES:
		if int(ranks[key]) < int(UPGRADES[key].cap):
			offers.append(key)
	for index in range(offers.size() - 1, 0, -1):
		var other := offer_rng.randi_range(0, index)
		var temp: String = offers[index]
		offers[index] = offers[other]
		offers[other] = temp
	if offers.is_empty():
		offers.append("supply")
	phase = Phase.UPGRADE
	events.append({"type": "level", "position": player})
func choose_upgrade(id: String) -> bool:
	if phase != Phase.UPGRADE or not offers.has(id):
		return false
	if id == "supply":
		health = minf(max_health, health + 25.0)
	elif UPGRADES.has(id) and int(ranks[id]) < int(UPGRADES[id].cap):
		ranks[id] = int(ranks[id]) + 1
		if id == "health":
			max_health = balance.player_health + int(ranks.health) * 20.0
			health = minf(max_health, health + 35.0)
	else:
		return false
	offers.clear()
	phase = Phase.RUNNING
	if xp >= xp_needed():
		_open_upgrade()
	return true
func _finish(message: String) -> void:
	if phase == Phase.RESULTS:
		return
	result = message
	phase = Phase.RESULTS
	events.append({"type": "result", "position": player})
