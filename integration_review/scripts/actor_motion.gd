extends RefCounted
## Presentation state only. Movement phases follow actual displacement, not held input.
const SCALE: float = 0.86
var player_clip: String = "idle"
var player_time: float = 0.0
var player_progress: float = -1.0
var gait_phase: float = 0.0
var shot_age: float = 99.0
var hurt_age: float = 99.0
var death_age: float = -1.0
var previous_player := Vector2.ZERO
var states: Dictionary = {}

func reset(position: Vector2) -> void:
	previous_player = position
	player_clip = "idle"
	player_time = 0.0
	player_progress = -1.0
	gait_phase = 0.0
	shot_age = 99.0
	hurt_age = 99.0
	death_age = -1.0
	states.clear()

func advance_player(dt: float, position: Vector2, facing: Vector2, hp: float, fire_interval: float, events: Array[Dictionary]) -> void:
	shot_age += dt
	hurt_age += dt
	for event in events:
		if event.type == "shot":
			shot_age = 0.0
		elif event.type == "hurt":
			hurt_age = 0.0
	var delta := position - previous_player
	previous_player = position
	if hp <= 0.0:
		if death_age < 0.0:
			death_age = 0.0
		set_player("death", death_age, -1.0)
		return
	if delta.length_squared() > 0.0001:
		gait_phase = fposmod(gait_phase + delta.length() / (64.0 * SCALE * 0.55), 1.0)
		var forward := facing.normalized()
		var motion := delta.normalized()
		var dot := forward.dot(motion)
		var name: String
		if dot < -0.55:
			name = "walk_back"
		elif absf(dot) < 0.55:
			name = "strafe_right" if forward.cross(motion) > 0.0 else "strafe_left"
		else:
			name = "walk_fire" if shot_age < fire_interval + dt else "walk"
		set_player(name, player_time + dt, gait_phase)
	elif shot_age < fire_interval:
		set_player("shoot", shot_age, shot_age / maxf(0.01, fire_interval))
	elif hurt_age < 0.16:
		set_player("hit", hurt_age, hurt_age / 0.16)
	else:
		set_player("idle", player_time + dt if player_clip == "idle" else 0.0, -1.0)

func set_player(clip: String, seconds: float, progress: float) -> void:
	player_clip = clip
	player_time = seconds
	player_progress = progress

func advance_result(dt: float) -> void:
	if death_age >= 0.0:
		death_age += dt
		set_player("death", death_age, -1.0)

func advance_enemy(enemy, dt: float, player: Vector2) -> void:
	var id: int = enemy.id
	if not states.has(id):
		states[id] = {"clip": "idle", "time": 0.0, "progress": -1.0, "previous": enemy.position, "cycle": float(id % 7) / 7.0, "total": 1.0}
	var state: Dictionary = states[id]
	var delta: Vector2 = enemy.position - Vector2(state.previous)
	state.previous = enemy.position
	var clip: String = "idle"
	var progress: float = -1.0
	var remaining: float = 0.0
	if enemy.warning > 0.0:
		clip = "idle"
	elif enemy.windup > 0.0:
		if enemy.kind == "boss":
			clip = "charge_windup" if enemy.action_kind == "charge" else ("pulse_attack" if enemy.action_kind == "pulse" else "acid_attack")
		else:
			clip = "windup"
		remaining = enemy.windup
	elif enemy.action_timer > 0.0:
		clip = "charge"
	elif enemy.recovery > 0.0:
		var total: float = 0.35 if enemy.kind == "spitter" else (0.8 if enemy.action_kind == "pulse" else 0.6)
		var attack_name: String = "attack"
		if enemy.kind == "boss":
			attack_name = "pulse_attack" if enemy.action_kind == "pulse" else "acid_attack"
		if enemy.action_kind != "charge" and enemy.recovery > total * 0.5:
			clip = attack_name
			progress = (total - enemy.recovery) / (total * 0.5)
		else:
			clip = "recovery"
			progress = 1.0 - enemy.recovery / (total if enemy.action_kind == "charge" else total * 0.5)
	elif enemy.position.distance_to(player) < enemy.radius + 24.0:
		clip = "attack" if enemy.kind in ["runner", "brute"] else "idle"
		progress = fposmod(enemy.age * 1.8, 1.0) if clip == "attack" else -1.0
	elif delta.length_squared() > 0.0001:
		clip = "move"
	if clip != String(state.clip):
		state.time = 0.0
		state.clip = clip
		state.total = maxf(0.01, remaining)
	else:
		state.time = float(state.time) + dt
	if remaining > 0.0:
		progress = 1.0 - remaining / float(state.total)
	if clip == "move" or clip == "charge":
		var physical_scale: float = {"runner": 1.0, "spitter": 1.14, "charger": 1.22, "brute": 1.65, "boss": 2.25}.get(enemy.kind, 1.0)
		state.cycle = fposmod(float(state.cycle) + delta.length() / (64.0 * SCALE * physical_scale * (0.255 / 0.62)), 1.0)
		progress = float(state.cycle)
	state.progress = progress

func prune(live_ids: Dictionary) -> void:
	for id in states.keys():
		if not live_ids.has(id):
			states.erase(id)
