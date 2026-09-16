extends RefCounted
## Authoritative fixed-step game. No input polling, drawing, audio or platform APIs.

const Balance = preload("res://scripts/balance.gd")
const Arena = preload("res://scripts/arena.gd")
const SpatialGrid = preload("res://scripts/spatial_grid.gd")
const DEFAULT_BALANCE = preload("res://data/default_balance.tres")
enum Phase { MENU, RUNNING, PAUSED, UPGRADE, RESULTS }

class Enemy extends RefCounted:
	var id: int = 0
	var position := Vector2.ZERO
	var direction := Vector2.DOWN
	var health: float = 35.0
	var speed: float = 58.0
	var warning: float = 0.75
	var flash: float = 0.0
	var age: float = 0.0
	var rewarded: bool = false

class Bullet extends RefCounted:
	var position := Vector2.ZERO
	var previous := Vector2.ZERO
	var velocity := Vector2.ZERO
	var damage: float = 0.0
	var remaining: float = 450.0

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
var pickups: Array[Pickup] = []
var events: Array[Dictionary] = []
var spawn_rng := RandomNumberGenerator.new()
var offer_rng := RandomNumberGenerator.new()
var spawning_enabled: bool = true

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
	# Call at 60 Hz. Pausing does not accumulate a catch-up debt.
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
	_collect_pickups(dt)
	# Resolve death before victory and before a level-up on the same step.
	if health <= 0.0:
		_finish("CONTAINMENT LOST")
		return
	if elapsed >= time_limit:
		elapsed = time_limit
		_finish("EXTRACTION READY")
		return
	if xp >= xp_needed():
		_open_upgrade()
		return
	if spawning_enabled:
		spawn_timer -= dt
		if spawn_timer <= 0.0:
			spawn_timer = maxf(0.12, 0.65 - elapsed * 0.00145)
			if enemies.size() < enemy_cap:
				_spawn_random()

func _move_enemies(dt: float) -> void:
	grid.rebuild(enemies)
	for enemy in enemies:
		enemy.age += dt
		enemy.flash = maxf(0.0, enemy.flash - dt)
		if enemy.warning > 0.0:
			enemy.warning = maxf(0.0, enemy.warning - dt)
			continue
		if enemy.health <= 0.0:
			continue
		var direction := arena.direction_to(enemy.position, player, balance.enemy_radius)
		var separation := Vector2.ZERO
		for index in grid.query(enemy.position, 30.0):
			var other: Enemy = enemies[index]
			var offset := enemy.position - other.position
			var distance_sq := offset.length_squared()
			if other.id != enemy.id and distance_sq < 26.0 * 26.0 and distance_sq > 0.01:
				separation += offset.normalized() * (1.0 - sqrt(distance_sq) / 26.0)
		var velocity := (direction + separation * 1.2).limit_length() * enemy.speed
		enemy.position = arena.move_body(enemy.position, velocity * dt, balance.enemy_radius)
		if velocity.length_squared() > 1.0:
			enemy.direction = velocity.normalized()
		if enemy.position.distance_squared_to(player) < pow(balance.player_radius + balance.enemy_radius, 2):
			if hurt_timer <= 0.0:
				health = maxf(0.0, health - balance.contact_damage)
				hurt_timer = balance.hurt_interval
				events.append({"type": "hurt", "position": player})

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
		for index in grid.query(center, travel * 0.5 + balance.enemy_radius + 3.0):
			var enemy: Enemy = enemies[index]
			if enemy.health <= 0.0 or enemy.warning > 0.0:
				continue
			var t := circle_hit_t(bullet.position, end, enemy.position, balance.enemy_radius + 2.0)
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
	# Keep grid indices stable for the entire bullet loop; remove dead actors after it.
	for index in range(enemies.size() - 1, -1, -1):
		if enemies[index].health <= 0.0:
			enemies.remove_at(index)

func damage_enemy(enemy: Enemy, amount: float) -> bool:
	if enemy.rewarded or enemy.health <= 0.0 or amount <= 0.0:
		return false
	enemy.health = maxf(0.0, enemy.health - amount)
	enemy.flash = 0.08
	events.append({"type": "hit", "position": enemy.position})
	if enemy.health <= 0.0:
		enemy.rewarded = true
		kills += 1
		_add_pickup(enemy.position)
		events.append({"type": "death", "position": enemy.position, "direction": enemy.direction})
	return true

func _add_pickup(point: Vector2) -> void:
	if pickups.size() >= balance.pickup_limit:
		# Merge, don't delete earned XP or silently collect it across the arena.
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
	for attempt in range(40):
		var angle := spawn_rng.randf_range(0.0, TAU)
		var candidate := player + Vector2.from_angle(angle) * spawn_rng.randf_range(560.0, 680.0)
		if arena.is_clear(candidate, balance.enemy_radius + 5.0):
			add_enemy(candidate, balance.spawn_warning)
			return

func add_enemy(point: Vector2, warning: float = 0.0) -> Enemy:
	var enemy := Enemy.new()
	enemy.id = next_enemy_id
	next_enemy_id += 1
	enemy.position = point
	enemy.health = balance.enemy_health * (1.0 + floorf(elapsed / 60.0) * 0.1)
	enemy.speed = balance.enemy_speed + minf(30.0, elapsed * 0.085)
	enemy.warning = warning
	enemies.append(enemy)
	return enemy

func seed_benchmark(count: int) -> void:
	reset(1709)
	spawning_enabled = false
	for index in range(clampi(count, 0, 500)):
		_spawn_random()

func _open_upgrade() -> void:
	xp -= xp_needed()
	level += 1
	offers.clear()
	for key: String in UPGRADES:
		if int(ranks[key]) < int(UPGRADES[key].cap):
			offers.append(key)
	# Dedicated RNG: cosmetic settings and spawn volume don't change upgrade order.
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
	# Process stored XP without requiring another pickup or dropping an earned level.
	if xp >= xp_needed():
		_open_upgrade()
	return true

func _finish(message: String) -> void:
	if phase == Phase.RESULTS:
		return
	result = message
	phase = Phase.RESULTS
	events.append({"type": "result", "position": player})
