extends RefCounted
## Human sprite review, not a complete production character family.
const FRAMES: SpriteFrames = preload("res://assets/human_survivor/sprite_frames.tres")
const PIVOT := Vector2(64, 110)
const DIRECTIONS: Array[String] = ["e", "s", "w", "n"]
const MUZZLES: Dictionary = {"e": Vector2(92.2, 65.6), "s": Vector2(78.4, 75.8), "w": Vector2(38.2, 69.2), "n": Vector2(64, 52.4)}
var direction: String = "e"
var clip: String = "idle"
var time: float = 0.0
var walk_time: float = 0.0
var hit_remaining: float = 0.0
var shot_remaining: float = 0.0
var dead: bool = false
var death_time: float = 0.0

func reset() -> void:
	direction = "e"
	clip = "idle"
	time = 0.0
	walk_time = 0.0
	hit_remaining = 0.0
	shot_remaining = 0.0
	dead = false
	death_time = 0.0

static func direction_for(aim: Vector2) -> String:
	if aim.length_squared() < 0.001:
		return "e"
	return DIRECTIONS[posmod(roundi(aim.angle() / (PI * 0.5)), 4)]

func advance(dt: float, moving: bool, aim: Vector2, hurt: bool, fired: bool, alive: bool) -> void:
	if dt <= 0.0:
		return
	if not alive:
		if not dead:
			dead = true
			death_time = 0.0
			shot_remaining = 0.0
			clip = "death"
		else:
			death_time += dt
		return
	if dead:
		return
	if aim.length_squared() > 0.001:
		direction = direction_for(aim)
	hit_remaining = maxf(0.0, hit_remaining - dt)
	shot_remaining = maxf(0.0, shot_remaining - dt)
	if hurt:
		hit_remaining = 2.0 / 12.0
	if fired:
		shot_remaining = 0.075
	var wanted: String = "hit" if hit_remaining > 0.0 else ("walk" if moving else "idle")
	if wanted != clip or hurt:
		clip = wanted
		time = 0.0
	else:
		time += dt
	if moving:
		walk_time += dt

func animation_name() -> StringName:
	return StringName("death_none" if dead else clip + "_" + direction)

func frame_index() -> int:
	var name := animation_name()
	var count := FRAMES.get_frame_count(name)
	if count <= 0:
		return 0
	var clock: float = death_time if dead else (walk_time if clip == "walk" else time)
	var index: int = floori(clock * FRAMES.get_animation_speed(name))
	return posmod(index, count) if FRAMES.get_animation_loop(name) else mini(count - 1, index)

func texture() -> Texture2D:
	return FRAMES.get_frame_texture(animation_name(), frame_index())

func muzzle_offset() -> Vector2:
	return (MUZZLES[direction] as Vector2) - PIVOT

func death_finished() -> bool:
	return dead and death_time >= float(FRAMES.get_frame_count(&"death_none")) / FRAMES.get_animation_speed(&"death_none")
