extends RefCounted
## Cosmetic-only charger animation. Existing simulation owns movement and damage.
const Frames: SpriteFrames = preload("res://assets/charger_review/sprite_frames.tres")
const Iso = preload("res://scripts/projection.gd")
const CELL := Vector2(128, 128)
const PIVOT := Vector2(64, 104)
const MOVE_DISTANCE: float = 0.235 / 0.62 * 64.0 * 1.06
const CHARGE_DISTANCE: float = 0.35 / 0.62 * 64.0 * 1.06
const DEATH_DURATION: float = 0.5
const MAX_CORPSES: int = 36
var live: Dictionary = {}
var deaths: Array[Dictionary] = []

class State extends RefCounted:
	var position := Vector2.ZERO
	var direction := Vector2.RIGHT
	var move_cycle: float = 0.0
	var charge_cycle: float = 0.0
	var idle_age: float = 0.0
	var hit_age: float = -1.0
	var previous_flash: float = 0.0
	var previous_windup: float = 0.0
	var windup_total: float = 0.75
	var previous_action: float = 0.0
	var previous_recovery: float = 0.0
	var recovery_total: float = 0.6
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
		if enemy.kind != "charger" or enemy.health <= 0.0:
			continue
		present[enemy.id] = true
		var state: State = live.get(enemy.id) as State
		if state == null:
			state = State.new()
			state.position = enemy.position
			live[enemy.id] = state
		var distance: float = state.position.distance_to(enemy.position)
		state.position = enemy.position
		state.idle_age += dt
		var attack_locked: bool = enemy.action_kind == "charge" and (enemy.windup > 0.0 or enemy.action_timer > 0.0 or enemy.recovery > 0.0)
		state.direction = Iso.project(enemy.action_direction if attack_locked else enemy.direction)
		if enemy.windup > state.previous_windup + 0.001:
			state.windup_total = maxf(0.001, enemy.windup)
			state.charge_cycle = 0.0
		if enemy.recovery > state.previous_recovery + 0.001:
			state.recovery_total = maxf(0.001, enemy.recovery)
		if distance < 70.0:
			if enemy.action_timer > 0.0 or state.previous_action > 0.0:
				state.charge_cycle = fposmod(state.charge_cycle + distance / CHARGE_DISTANCE, 1.0)
			else:
				state.move_cycle = fposmod(state.move_cycle + distance / MOVE_DISTANCE, 1.0)
		if state.hit_age >= 0.0:
			state.hit_age += dt
			if state.hit_age >= 2.0 / 12.0:
				state.hit_age = -1.0
		if enemy.flash > state.previous_flash + 0.001 and state.hit_age < 0.0:
			state.hit_age = 0.0
		if enemy.warning > 0.0:
			state.clip = "idle"
			state.age = state.idle_age
		elif enemy.windup > 0.0:
			state.clip = "windup"
			state.age = clampf(1.0 - enemy.windup / state.windup_total, 0.0, 1.0) * (4.0 / 8.0 - 0.0001)
		elif enemy.action_timer > 0.0 and enemy.action_kind == "charge":
			state.clip = "charge"
			state.age = state.charge_cycle * (6.0 / 16.0)
		elif enemy.recovery > 0.0 and enemy.action_kind == "charge":
			state.clip = "recovery"
			state.age = clampf(1.0 - enemy.recovery / state.recovery_total, 0.0, 1.0) * (4.0 / 10.0 - 0.0001)
		elif state.hit_age >= 0.0:
			state.clip = "hit"
			state.age = state.hit_age
		elif distance > 0.001:
			state.clip = "move"
			state.age = state.move_cycle * 0.5
		else:
			state.clip = "idle"
			state.age = state.idle_age
		state.previous_flash = enemy.flash
		state.previous_windup = enemy.windup
		state.previous_action = enemy.action_timer
		state.previous_recovery = enemy.recovery
	for id in live.keys():
		if not present.has(id):
			live.erase(id)
	for event in events:
		if event.type == "death" and event.get("kind", "") == "charger":
			deaths.append({"position": event.position, "direction": Iso.project(event.get("direction", Vector2.RIGHT)), "age": 0.0})
			if deaths.size() > MAX_CORPSES:
				deaths.pop_front()

func for_enemy(enemy) -> Texture2D:
	var state: State = live.get(enemy.id) as State
	if state == null:
		return texture("idle", Iso.project(enemy.direction), 0.0)
	return texture(state.clip, state.direction, state.age)
