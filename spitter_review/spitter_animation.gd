extends RefCounted
## Presentation only. Simulation timers control wind-up and projectile release.
const Frames: SpriteFrames = preload("res://assets/spitter_review/sprite_frames.tres")
const Iso = preload("res://scripts/projection.gd")
const CELL := Vector2(128, 128)
const PIVOT := Vector2(64, 104)
const CYCLE_DISTANCE: float = 24.07225806451613
const DEATH_DURATION: float = 0.5
const MAX_CORPSES: int = 40
var live: Dictionary = {}
var deaths: Array[Dictionary] = []

class State extends RefCounted:
	var position := Vector2.ZERO
	var direction := Vector2.RIGHT
	var cycle: float = 0.0
	var idle_age: float = 0.0
	var previous_windup: float = 0.0
	var windup_total: float = 0.65
	var previous_recovery: float = 0.0
	var recovery_total: float = 0.35
	var previous_flash: float = 0.0
	var hit_age: float = -1.0
	var clip: String = "idle"
	var age: float = 0.0

func reset() -> void:
	live.clear()
	deaths.clear()

static func facing(direction: Vector2) -> String:
	if absf(direction.x) >= absf(direction.y):
		return "e" if direction.x >= 0.0 else "w"
	return "s" if direction.y >= 0.0 else "n"

static func texture(clip: String, direction: Vector2, age: float) -> Texture2D:
	var key := StringName(clip + "_" + facing(direction))
	var count := Frames.get_frame_count(key)
	var index := maxi(0, floori(age * Frames.get_animation_speed(key) + 0.00001))
	index = index % count if Frames.get_animation_loop(key) else mini(index, count - 1)
	return Frames.get_frame_texture(key, index)

func advance(dt: float, enemies: Array, events: Array[Dictionary], keep_corpses: bool) -> void:
	if dt <= 0.0:
		return
	for i in range(deaths.size() - 1, -1, -1):
		deaths[i].age = minf(float(deaths[i].age) + dt, DEATH_DURATION)
		if not keep_corpses and float(deaths[i].age) >= DEATH_DURATION:
			deaths.remove_at(i)
	var present: Dictionary = {}
	for enemy in enemies:
		if enemy.kind != "spitter" or enemy.health <= 0.0:
			continue
		present[enemy.id] = true
		var state: State = live.get(enemy.id) as State
		if state == null:
			state = State.new()
			state.position = enemy.position
			live[enemy.id] = state
		var travelled: float = state.position.distance_to(enemy.position)
		state.position = enemy.position
		state.idle_age += dt
		state.direction = Iso.project(enemy.action_direction if enemy.windup > 0.0 or enemy.recovery > 0.0 else enemy.direction)
		if travelled < 70.0:
			state.cycle = fposmod(state.cycle + travelled / CYCLE_DISTANCE, 1.0)
		if state.hit_age >= 0.0:
			state.hit_age += dt
			if state.hit_age >= 2.0 / 12.0:
				state.hit_age = -1.0
		if enemy.flash > state.previous_flash + 0.001 and state.hit_age < 0.0:
			state.hit_age = 0.0
		if enemy.windup > state.previous_windup + 0.001:
			state.windup_total = maxf(0.001, enemy.windup)
		if enemy.recovery > state.previous_recovery + 0.001:
			state.recovery_total = maxf(0.001, enemy.recovery)
		if enemy.warning > 0.0:
			state.clip = "idle"
			state.age = state.idle_age
		elif enemy.windup > 0.0:
			state.clip = "windup"
			state.age = clampf(1.0 - enemy.windup / state.windup_total, 0.0, 1.0) * (4.0 / 8.0 - 0.0001)
		elif enemy.recovery > 0.0 and enemy.action_kind == "spit":
			var progress := clampf(1.0 - enemy.recovery / state.recovery_total, 0.0, 1.0)
			state.clip = "attack" if progress < 0.6 else "recovery"
			state.age = progress / 0.6 * (4.0 / 12.0 - 0.0001) if progress < 0.6 else (progress - 0.6) / 0.4 * (2.0 / 8.0 - 0.0001)
		elif state.hit_age >= 0.0:
			state.clip = "hit"
			state.age = state.hit_age
		elif travelled > 0.001:
			state.clip = "move"
			state.age = state.cycle * 0.6
		else:
			state.clip = "idle"
			state.age = state.idle_age
		state.previous_flash = enemy.flash
		state.previous_windup = enemy.windup
		state.previous_recovery = enemy.recovery
	for id in live.keys():
		if not present.has(id):
			live.erase(id)
	for event in events:
		if event.type == "death" and event.get("kind", "") == "spitter":
			deaths.append({"position": event.position, "direction": Iso.project(event.get("direction", Vector2.RIGHT)), "age": 0.0})
			if deaths.size() > MAX_CORPSES:
				deaths.pop_front()

func for_enemy(enemy) -> Texture2D:
	var state: State = live.get(enemy.id) as State
	if state == null:
		return texture("idle", Iso.project(enemy.direction), 0.0)
	return texture(state.clip, state.direction, state.age)
