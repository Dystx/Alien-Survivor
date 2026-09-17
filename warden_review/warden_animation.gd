extends RefCounted
## Single-boss presentation. Never writes to simulation, HP, hazards or aiming.
const Frames: SpriteFrames = preload("res://assets/warden_review/sprite_frames.tres")
const Iso = preload("res://scripts/projection.gd")
const CELL := Vector2(256, 256)
const PIVOT := Vector2(128, 204)
const MOVE_DISTANCE: float = 46.08
const CHARGE_DISTANCE: float = 70.60645161290323
const DEATH_DURATION: float = 1.25
const PHASE_DURATION: float = 0.6
var active: bool = false
var dead: bool = false
var entity_id: int = -1
var position := Vector2.ZERO
var direction := Vector2.RIGHT
var clip: String = "idle"
var age: float = 0.0
var cycle: float = 0.0
var charge_cycle: float = 0.0
var idle_age: float = 0.0
var death_age: float = 0.0
var phase_pending: bool = false
var phase_seen: bool = false
var phase_age: float = -1.0
var hit_age: float = -1.0
var previous_flash: float = 0.0
var previous_windup: float = 0.0
var windup_total: float = 0.95
var previous_recovery: float = 0.0
var recovery_total: float = 0.6

func reset() -> void:
	active = false
	dead = false
	entity_id = -1
	position = Vector2.ZERO
	direction = Vector2.RIGHT
	clip = "idle"
	age = 0.0
	cycle = 0.0
	charge_cycle = 0.0
	idle_age = 0.0
	death_age = 0.0
	phase_pending = false
	phase_seen = false
	phase_age = -1.0
	hit_age = -1.0
	previous_flash = 0.0
	previous_windup = 0.0
	windup_total = 0.95
	previous_recovery = 0.0
	recovery_total = 0.6

static func facing(aim: Vector2) -> String:
	if absf(aim.x) >= absf(aim.y):
		return "e" if aim.x >= 0.0 else "w"
	return "s" if aim.y >= 0.0 else "n"

static func frame_index(action: String, aim: Vector2, clock: float) -> int:
	var key := StringName(action + "_" + facing(aim))
	var count := Frames.get_frame_count(key)
	var frame := maxi(0, floori(clock * Frames.get_animation_speed(key) + 0.00001))
	return frame % count if Frames.get_animation_loop(key) else mini(frame, count - 1)

static func texture(action: String, aim: Vector2, clock: float) -> Texture2D:
	var key := StringName(action + "_" + facing(aim))
	return Frames.get_frame_texture(key, frame_index(action, aim, clock))

func current_texture() -> Texture2D:
	return texture(clip, direction, age)

func advance_death(dt: float) -> void:
	if not dead or dt <= 0.0:
		return
	death_age = minf(DEATH_DURATION, death_age + dt)
	clip = "death"
	age = death_age

func waiting_for_death() -> bool:
	return dead and death_age < DEATH_DURATION

func advance(dt: float, boss) -> void:
	if dt <= 0.0:
		return
	if dead:
		advance_death(dt)
		return
	if boss == null or boss.kind != "boss":
		return
	if not active:
		active = true
		entity_id = boss.id
		position = boss.position
	if entity_id != boss.id:
		return # A new run must explicitly reset this controller.
	var travel: float = position.distance_to(boss.position)
	position = boss.position
	var critical: bool = boss.windup > 0.0 or boss.action_timer > 0.0 or boss.recovery > 0.0
	direction = Iso.project(boss.action_direction if critical else boss.direction)
	if boss.health <= 0.0:
		dead = true
		death_age = 0.0
		phase_pending = false
		phase_age = -1.0
		hit_age = -1.0
		clip = "death"
		age = 0.0
		return
	idle_age += dt
	if travel < 100.0:
		cycle = fposmod(cycle + travel / MOVE_DISTANCE, 1.0)
		charge_cycle = fposmod(charge_cycle + travel / CHARGE_DISTANCE, 1.0)
	if boss.enraged and not phase_seen:
		phase_seen = true
		phase_pending = true
	if hit_age >= 0.0:
		hit_age += dt
		if hit_age >= 0.2:
			hit_age = -1.0
	if boss.flash > previous_flash + 0.001 and hit_age < 0.0:
		hit_age = 0.0
	if boss.windup > previous_windup + 0.001:
		windup_total = maxf(0.001, boss.windup)
	if boss.recovery > previous_recovery + 0.001:
		recovery_total = maxf(0.001, boss.recovery)
	# A phase flare is queued until stationary and non-attacking. It never masks
	# a live warning, burst or damaging dash; it grants no pause/invulnerability.
	if critical or travel > 0.001:
		if phase_age >= 0.0:
			phase_age = -1.0
	elif phase_age >= 0.0:
		phase_age += dt
		if phase_age >= PHASE_DURATION:
			phase_age = -1.0
	elif phase_pending and boss.warning <= 0.0:
		phase_pending = false
		phase_age = 0.0
	if boss.warning > 0.0:
		clip = "idle"
		age = idle_age
	elif boss.windup > 0.0:
		var progress := clampf(1.0 - boss.windup / windup_total, 0.0, 1.0)
		match String(boss.action_kind):
			"charge":
				clip = "charge_windup"
				age = progress * (0.8 - 0.0001)
			"fan":
				clip = "acid_attack"
				age = progress * (0.3 - 0.0001)
			_:
				clip = "pulse_attack"
				age = progress * (4.0 / 12.0 - 0.0001)
	elif boss.action_timer > 0.0:
		clip = "charge"
		age = charge_cycle * (6.0 / 14.0)
	elif boss.recovery > 0.0:
		var progress := clampf(1.0 - boss.recovery / recovery_total, 0.0, 1.0)
		match String(boss.action_kind):
			"fan":
				clip = "acid_attack"
				age = 0.3 + progress * (0.3 - 0.0001)
			"pulse":
				clip = "pulse_attack"
				age = 4.0 / 12.0 + progress * (4.0 / 12.0 - 0.0001)
			_:
				clip = "recovery"
				age = progress * (0.5 - 0.0001)
	elif phase_age >= 0.0:
		clip = "phase_transition"
		age = phase_age
	elif hit_age >= 0.0:
		clip = "hit"
		age = hit_age
	elif travel > 0.001:
		clip = "move"
		age = cycle * 0.75
	else:
		clip = "idle"
		age = idle_age
	previous_flash = boss.flash
	previous_windup = boss.windup
	previous_recovery = boss.recovery
