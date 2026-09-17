extends RefCounted
## Cosmetic-only rifle presentation around the owner's byte-locked human atlas.
## No damage, cooldown, aim quantization, actor translation or simulation writes.
## Pure geometry inputs align the simulation muzzle with the unchanged body.
const Human = preload("res://scripts/human_animation.gd")
const Iso = preload("res://scripts/projection.gd")
const FLASH_SECONDS: float = 0.055
const TRACER_HEIGHT := Vector2(0, -18)
# Calibrated from the locked 128px cells, not the older procedural model.
# North's weapon is behind the torso: its attachment is deliberately occluded.
const SOCKETS: Dictionary = {
	"idle": {"e": Vector2(92, 58), "s": Vector2(80, 74), "w": Vector2(39, 66), "n": Vector2(67, 49)},
	"walk": {"e": Vector2(92, 58), "s": Vector2(80, 74), "w": Vector2(39, 66), "n": Vector2(67, 49)},
	"hit": {"e": [Vector2(86, 53), Vector2(85, 54)], "s": [Vector2(81, 72), Vector2(79, 74)], "w": [Vector2(42, 51), Vector2(41, 62)], "n": [Vector2(68, 49), Vector2(69, 50)]}
}
const AXES: Dictionary = {"e": Vector2(1, 0.37), "s": Vector2(0.63, 0.78), "w": Vector2(-0.80, 0.60), "n": Vector2(0, -1)}
var flash_age: float = FLASH_SECONDS
var flash_facing: String = "e"
var shot_serial: int = 0
var flash_axis := Vector2.ZERO
var flash_mount := Vector2.INF
var muzzle_blocked: bool = false
var traces: Dictionary = {}

func reset() -> void:
	flash_age = FLASH_SECONDS
	flash_facing = "e"
	shot_serial = 0
	flash_axis = Vector2.ZERO
	flash_mount = Vector2.INF
	muzzle_blocked = false
	traces.clear()

static func muzzle_cell(human: Human) -> Vector2:
	if human.dead:
		return Human.PIVOT
	var bank: Dictionary = SOCKETS.get(human.clip, SOCKETS.idle)
	var entry: Variant = bank.get(human.direction, SOCKETS.idle.e)
	if entry is Array:
		return entry[mini(human.frame_index(), entry.size() - 1)] as Vector2
	return entry as Vector2

static func muzzle_offset(human: Human, scale: float) -> Vector2:
	return (muzzle_cell(human) - Human.PIVOT) * scale

static func barrel_axis(human: Human) -> Vector2:
	return (AXES.get(human.direction, Vector2.RIGHT) as Vector2).normalized()

func advance(dt: float, human: Human, fired: bool, bullets: Array, rifle_range: float, scale: float, events: Array[Dictionary] = []) -> void:
	if dt <= 0.0:
		return
	flash_age = minf(FLASH_SECONDS, flash_age + dt)
	# An old shot must not rotate with a new facing, hit pose or dead character.
	if human.dead or human.direction != flash_facing:
		flash_age = FLASH_SECONDS
	if fired and not human.dead:
		flash_age = 0.0
		flash_facing = human.direction
		shot_serial += 1
		flash_axis = Vector2.ZERO
		flash_mount = Vector2.INF
		muzzle_blocked = false
		for event in events:
			if event.type == "shot" and bool(event.get("mounted", false)):
				flash_axis = Iso.project(event.direction).normalized()
				flash_mount = (Iso.project(event.origin - event.position) + TRACER_HEIGHT) / scale
			if event.type == "rifle_impact" and bool(event.get("wall", false)):
				muzzle_blocked = true
	var live: Dictionary = {}
	for bullet in bullets:
		var id: int = bullet.get_instance_id()
		live[id] = true
		if not traces.has(id):
			traces[id] = {"muzzle": TRACER_HEIGHT if bullet.muzzle_launched else muzzle_offset(human, scale),
				"range": bullet.path_length if bullet.muzzle_launched else rifle_range}
	for id in traces.keys():
		if not live.has(id):
			traces.erase(id)

func visible(human: Human) -> bool:
	return not human.dead and flash_age < FLASH_SECONDS and human.direction == flash_facing

func behind_body(human: Human) -> bool:
	return human.direction == "n"

func opacity() -> float:
	return clampf(1.0 - flash_age / FLASH_SECONDS, 0.0, 1.0)

func flash_scale() -> float:
	# Short, stable flare. Never scale the actor or move its feet for recoil.
	return 0.22 * (1.0 if shot_serial % 2 == 0 else 0.90)

func trace_points(bullet) -> PackedVector2Array:
	var id: int = bullet.get_instance_id()
	if not traces.has(id):
		return PackedVector2Array()
	var record: Dictionary = traces[id]
	var travelled := maxf(0.0, float(record.range) - float(bullet.remaining))
	var unit: Vector2 = bullet.velocity.normalized()
	var head: Vector2 = Iso.project(bullet.position) + _trace_offset(record, travelled)
	var tail_distance := minf(travelled, 11.0 / maxf(0.001, Iso.project(unit).length()))
	var tail: Vector2 = Iso.project(bullet.position - unit * tail_distance) + _trace_offset(record, travelled - tail_distance)
	return PackedVector2Array([tail, head])

static func _trace_offset(record: Dictionary, _travelled: float) -> Vector2:
	# A constant translation preserves the exact straight ray. The previous
	# 110-unit blend changed its slope mid-flight and looked like homing.
	return record.muzzle as Vector2

static func launch_geometry(human: Human, dt: float, scale: float) -> Dictionary:
	# Predict only the non-moving upper-body socket for this physics tick.
	# Idle/walk share the approved gun pixels; a new hit has its own first pose.
	var predicted := Human.new()
	predicted.clip = human.clip
	predicted.time = human.time
	predicted.hit_remaining = human.hit_remaining
	predicted.advance(dt, false, Vector2.RIGHT, false, false, true)
	var offsets: Array[Vector2] = []
	var hurt_offsets: Array[Vector2] = []
	var struck := Human.new()
	struck.clip = "hit"
	for direction in Human.DIRECTIONS:
		predicted.direction = direction
		struck.direction = direction
		offsets.append(Iso.unproject(muzzle_offset(predicted, scale) - TRACER_HEIGHT))
		hurt_offsets.append(Iso.unproject(muzzle_offset(struck, scale) - TRACER_HEIGHT))
	return {"basis": Iso.BASIS, "offsets": offsets, "hurt_offsets": hurt_offsets}

func draw_flash(canvas: CanvasItem, human: Human, ground: Vector2, actor_scale: float, texture: Texture2D, behind: bool) -> void:
	if texture == null or not visible(human) or behind != behind_body(human):
		return
	# A same-tick hit can change the visible pose after launch. Do not redraw a
	# flash at a different socket; let the already-fired bullet remain independent.
	if flash_mount.is_finite() and (flash_mount * actor_scale).distance_to(muzzle_offset(human, actor_scale)) > 2.0:
		return
	var attachment := ground + muzzle_offset(human, actor_scale)
	var effect_scale := flash_scale() * actor_scale
	# Existing effect crop excludes the dark barrel fragment at its left edge.
	# Source x=24 is the emission root, not the centre of the whole flash.
	var source := Rect2(24, 4, 68, 72)
	var size := source.size * effect_scale
	canvas.draw_set_transform(attachment, (flash_axis if flash_axis != Vector2.ZERO else barrel_axis(human)).angle())
	canvas.draw_texture_rect_region(texture, Rect2(Vector2(0, -36) * effect_scale, size), source, Color(1, 1, 1, opacity()))
	canvas.draw_set_transform(Vector2.ZERO)
