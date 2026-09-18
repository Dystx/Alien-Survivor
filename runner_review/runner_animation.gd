extends RefCounted
## Cosmetic runner state. Never mutates simulation, damage, targeting or the human.
const Frames: SpriteFrames = preload("res://assets/runner_review/sprite_frames.tres")
const Iso = preload("res://scripts/projection.gd")
const PIVOT := Vector2(48, 78)
const CELL := Vector2(96, 96)
const CYCLE_DISTANCE: float = 22.5445161290323
const DEATH_DURATION: float = 0.5
const MAX_CORPSES: int = 60
var live: Dictionary = {}
var deaths: Array[Dictionary] = []

class State extends RefCounted:
	var position := Vector2.ZERO
	var direction := Vector2.RIGHT
	var cycle: float = 0.0
	var idle_age: float = 0.0
	var attack_age: float = -1.0
	var attack_cooldown: float = 0.0
	var hit_age: float = -1.0
	var previous_flash: float = 0.0
	var clip: String = "idle"
	var age: float = 0.0

func reset() -> void:
	live.clear()
	deaths.clear()

static func facing(direction: Vector2) -> String:
	if direction.length_squared() < 0.0001:
		return "e"
	return "e" if absf(direction.x) >= absf(direction.y) and direction.x >= 0.0 else ("w" if absf(direction.x) >= absf(direction.y) else ("s" if direction.y >= 0.0 else "n"))

static func texture(clip: String, direction: Vector2, age: float) -> Texture2D:
	var key := StringName(clip + "_" + facing(direction))
	var count := Frames.get_frame_count(key)
	var index := maxi(0, int(age * Frames.get_animation_speed(key)))
	index = index % count if Frames.get_animation_loop(key) else mini(index, count - 1)
	return Frames.get_frame_texture(key, index)

func advance(dt: float, enemies: Array, events: Array[Dictionary], player: Vector2, keep_corpses: bool) -> void:
	if dt <= 0.0:
		return
	for i in range(deaths.size() - 1, -1, -1):
		deaths[i].age = minf(float(deaths[i].age) + dt, DEATH_DURATION)
		if not keep_corpses and float(deaths[i].age) >= DEATH_DURATION:
			deaths.remove_at(i)
	var present: Dictionary = {}
	for enemy in enemies:
		if enemy.kind != "runner" or enemy.health <= 0.0:
			continue
		present[enemy.id] = true
		var state: State = live.get(enemy.id) as State
		if state == null:
			state = State.new()
			state.position = enemy.position
			live[enemy.id] = state
		var travelled: float = state.position.distance_to(enemy.position)
		state.position = enemy.position
		state.direction = Iso.project(enemy.direction)
		state.idle_age += dt
		# Distance accumulation gives planted gait speed, not feet cycling against a wall.
		if travelled < 70.0:
			state.cycle = fposmod(state.cycle + travelled / CYCLE_DISTANCE, 1.0)
		state.attack_cooldown = maxf(0.0, state.attack_cooldown - dt)
		if state.attack_age >= 0.0:
			state.attack_age += dt
			if state.attack_age >= 4.0 / 12.0:
				state.attack_age = -1.0
		if state.hit_age >= 0.0:
			state.hit_age += dt
			if state.hit_age >= 2.0 / 12.0:
				state.hit_age = -1.0
		# The original runner uses continuous contact damage. This claw gesture is
		# presentation only; no animation callback authorizes or delays damage.
		if enemy.warning <= 0.0 and enemy.position.distance_to(player) <= enemy.radius + 19.0 and state.attack_cooldown <= 0.0:
			state.attack_age = 0.0
			state.attack_cooldown = 0.55
		if enemy.flash > state.previous_flash + 0.001 and state.hit_age < 0.0:
			state.hit_age = 0.0
		state.previous_flash = enemy.flash
		if enemy.warning > 0.0:
			state.clip = "idle"
			state.age = state.idle_age
		elif state.hit_age >= 0.0:
			state.clip = "hit"
			state.age = state.hit_age
		elif state.attack_age >= 0.0:
			state.clip = "attack"
			state.age = state.attack_age
		elif travelled > 0.001:
			state.clip = "move"
			state.age = state.cycle * 0.5
		else:
			state.clip = "idle"
			state.age = state.idle_age
	for id in live.keys():
		if not present.has(id):
			live.erase(id)
	for event in events:
		if event.type == "death" and event.get("kind", "") == "runner":
			deaths.append({"position": event.position, "direction": Iso.project(event.get("direction", Vector2.RIGHT)), "age": 0.0})
			if deaths.size() > MAX_CORPSES:
				deaths.pop_front()

func for_enemy(enemy) -> Texture2D:
	var state: State = live.get(enemy.id) as State
	if state == null:
		return texture("idle", Iso.project(enemy.direction), 0.0)
	return texture(state.clip, state.direction, state.age)
