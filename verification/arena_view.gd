extends Node2D
const Simulation = preload("res://scripts/simulation.gd")
const Sprites = preload("res://scripts/sprite_factory.gd")
const Projection = preload("res://scripts/projection.gd")
const CENTER := Vector2(480, 290)
var sim: Simulation
var sprites: Sprites
var camera := Vector2.ZERO
var offset := Vector2.ZERO
var fx: Array[Dictionary] = []
var corpses: Array[Dictionary] = []
var gore: bool = true
var shake_enabled: bool = false
var shake: float = 0.0
var player_animation: float = 0.0
var cosmetic_rng := RandomNumberGenerator.new()
var moving_now: bool = false
var last_shot: float = 0.0
func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	sprites = Sprites.new()
	cosmetic_rng.seed = 777
func reset() -> void:
	fx.clear()
	corpses.clear()
	shake = 0.0
	last_shot = 0.0
	player_animation = 0.0
	camera = Projection.project(sim.player)
	offset = Vector2.ZERO
	queue_redraw()
func screen_to_world(point: Vector2) -> Vector2:
	return Projection.unproject(point + Vector2(0, 18) + camera - CENTER - offset)
func screen(point: Vector2) -> Vector2:
	return Projection.project(point) - camera + CENTER + offset
func advance(dt: float, moving: bool, events: Array[Dictionary]) -> void:
	moving_now = moving
	if moving:
		player_animation += dt
	camera = Projection.project(sim.player)
	last_shot = maxf(0.0, last_shot - dt)
	for event in events:
		var type: String = event.type
		if type == "death":
			if gore:
				corpses.append({"position": event.position, "variant": cosmetic_rng.randi_range(0, 2), "boss": event.get("kind", "") == "boss"})
				if corpses.size() > 70:
					corpses.pop_front()
			if event.get("kind", "") == "boss":
				_add_fx("blast", event.position, Vector2.RIGHT, 0.7)
		elif type in ["shot", "hit", "spark", "spit", "acid_hit", "blast", "boss_phase"]:
			_add_fx(type, event.position, event.get("direction", Vector2.RIGHT), 0.46 if type in ["blast", "boss_phase"] else 0.16)
			if type == "shot":
				last_shot = 0.08
		if type == "hurt" and shake_enabled:
			shake = 2.5
	for i in range(fx.size() - 1, -1, -1):
		fx[i].life = float(fx[i].life) - dt
		if float(fx[i].life) <= 0.0:
			fx.remove_at(i)
	shake = maxf(0.0, shake - dt * 18.0)
	offset = Vector2(cosmetic_rng.randf_range(-shake, shake), cosmetic_rng.randf_range(-shake, shake)) if shake > 0.0 else Vector2.ZERO
	queue_redraw()
func _add_fx(type: String, point: Vector2, direction: Vector2, duration: float) -> void:
	if fx.size() >= 96:
		fx.pop_front()
	fx.append({"type": type, "position": point, "direction": direction, "life": duration, "duration": duration})
func _draw() -> void:
	if sim == null or sprites == null:
		return
	draw_rect(Rect2(0, 0, 960, 540), Color("101215"))
	_draw_floor()
	_draw_boundary()
	for corpse in corpses:
		var p := screen(corpse.position)
		_center(sprites.tex("fx/blood_pool"), p, Vector2(52, 28), Color(0.8, 0.75, 0.75, 0.7))
		var scale := 1.4 if bool(corpse.boss) else 0.62
		_center(sprites.tex("fx/corpse_%d" % int(corpse.variant)), p, Vector2(104, 64) * scale)
	for h in sim.hazards:
		var color := Color(0.45, 0.95, 0.18, 0.38) if h.kind == "acid" else Color(1, 0.47, 0.16, 0.30)
		_ground_circle(h.position, float(h.radius), color, true)
		_ground_circle(h.position, float(h.radius), Color(color, 0.95), false)
		if h.kind == "acid":
			_center(sprites.tex("fx/acid_pool"), screen(h.position), Vector2(60, 34))
	for pickup in sim.pickups:
		_center(sprites.tex("fx/xp"), screen(pickup.position) + Vector2(0, -4), Vector2(23, 23))
	var actors: Array[Dictionary] = []
	for i in range(sim.arena.blockers.size()):
		var rect: Rect2 = sim.arena.blockers[i]
		actors.append({"depth": Projection.project(rect.end).y, "rect": rect, "index": i})
	for enemy in sim.enemies:
		var p := screen(enemy.position)
		if not Rect2(-140, -180, 1240, 850).has_point(p):
			continue
		if enemy.warning > 0.0:
			_ground_circle(enemy.position, enemy.radius + 15.0, Color(1, 0.55, 0.22, 0.75), false)
			var d := Vector2(7, 0)
			draw_line(p-d, p+d, Color("f1ad57"), 2.0)
			if enemy.kind != "boss":
				continue
		_draw_telegraph(enemy)
		actors.append({"depth": Projection.project(enemy.position).y, "enemy": enemy})
	actors.append({"depth": Projection.project(sim.player).y, "player": true})
	actors.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a.depth) < float(b.depth))
	for actor in actors:
		if actor.has("rect"):
			_draw_blocker(actor.rect, int(actor.index))
		elif actor.has("enemy"):
			_draw_enemy(actor.enemy)
		else:
			var p := screen(sim.player)
			_ground_circle(sim.player, 15.0, Color(0.64, 0.85, 0.97, 0.65), false)
			var recoil := -Projection.project(sim.facing).normalized() * (2.0 if last_shot > 0.0 else 0.0)
			var tint := Color(1.0, 0.55, 0.45) if sim.hurt_timer > 0.5 else Color.WHITE
			_foot(sprites.player_frame(Projection.project(sim.facing)), p + recoil, 0.88, tint)
	for bullet in sim.bullets:
		var p := screen(bullet.position) + Vector2(0, -18)
		var direction := Projection.project(bullet.velocity).normalized()
		draw_line(p - direction * 13.0, p, Color("bca56e"), 1.5)
		draw_line(p - direction * 5.0, p, Color("fff1b2"), 2.0)
	for shot in sim.enemy_projectiles:
		var p := screen(shot.position) + Vector2(0, -15)
		var angle := Projection.project(shot.velocity).angle() + PI
		_rotated(sprites.tex("fx/acid_bolt"), p, Vector2(31, 26), angle)
		_ground_circle(shot.position, shot.radius, Color(0.55, 0.9, 0.18, 0.28), true)
	for effect in fx:
		var p := screen(effect.position) + Vector2(0, -18)
		var t := 1.0 - float(effect.life) / float(effect.duration)
		match String(effect.type):
			"shot":
				var direction := Projection.project(effect.direction).normalized()
				p += direction * 25.0 + Vector2(0, -7)
				_rotated(sprites.tex("fx/muzzle_1"), p, Vector2(34, 24), direction.angle())
			"hit":
				_center(sprites.tex("fx/blood_0" if gore else "fx/spark"), p, Vector2(27, 28))
			"spark":
				_center(sprites.tex("fx/spark"), p, Vector2(24, 24))
			"acid_hit", "spit":
				_center(sprites.tex("fx/acid_pool"), p, Vector2(32, 25))
			"blast", "boss_phase":
				_center(sprites.tex("fx/explosion_%d" % clampi(int(t * 5.0), 0, 4)), p, Vector2(116, 116))
func _draw_floor() -> void:
	for y in range(sim.arena.ROWS):
		for x in range(sim.arena.COLS):
			var point := screen(Vector2(x, y) * 64.0)
			if not Rect2(-100, -80, 1160, 720).has_point(point):
				continue
			var tile: int = 0
			if x % 7 == 0:
				tile = 4
			elif (x * 17 + y * 13) % 29 == 0:
				tile = 2
			elif y == 2 or y == 15:
				tile = 3 if x % 5 == 0 else 0
			draw_texture_rect(sprites.tex("environment/floor/tile_%d" % tile), Rect2(point + Vector2(-48, 0), Vector2(96, 48)), false, Color(0.76, 0.79, 0.82))
	var pad := Rect2(736, 456, 320, 240)
	_outline(_rect_points(pad), Color(0.70, 0.66, 0.42, 0.42), 1.5)
	_ground_circle(Vector2(896, 576), 65.0, Color(0.62, 0.74, 0.76, 0.22), false)
	for i in range(5):
		var pos := Vector2(230 + i * 327, 105 if i % 2 == 0 else 1050)
		_foot(sprites.tex("environment/props/infestation_%d" % (i % 2)), screen(pos), 0.75, Color(0.8, 0.8, 0.8, 0.8))
func _draw_boundary() -> void:
	var b: Rect2 = sim.arena.bounds
	_outline(_rect_points(b), Color("a28c52"), 2.0)
	for x in range(0, 14):
		var p := screen(Vector2(70 + x * 123, b.position.y - 10))
		_foot(sprites.tex("environment/props/wall_light" if x % 4 == 0 else "environment/props/wall_plain"), p, 0.69)
	for y in range(0, 9):
		var p := screen(Vector2(b.position.x - 10, 80 + y * 120))
		_foot(sprites.tex("environment/props/wall_pipe"), p, 0.69, Color.WHITE, true)
func _draw_blocker(rect: Rect2, index: int) -> void:
	var feet := _rect_points(rect)
	var top := PackedVector2Array()
	for p in feet:
		top.append(p + Vector2(0, -24))
	draw_colored_polygon(PackedVector2Array([feet[1], feet[2], top[2], top[1]]), Color("333940"))
	draw_colored_polygon(PackedVector2Array([feet[2], feet[3], top[3], top[2]]), Color("20272b"))
	draw_colored_polygon(top, Color("41484b"))
	_outline(top, Color("777a75"), 1.0)
	_outline(feet, Color("a98f49"), 1.5)
	var names: Array[String] = ["crate_steel", "crate_hazard", "crate_green", "crate_steel", "console", "terminal"]
	_foot(sprites.tex("environment/props/" + names[index % names.size()]), screen(rect.get_center()) + Vector2(0, -8), 0.61)
func _draw_enemy(enemy: Simulation.Enemy) -> void:
	var p := screen(enemy.position)
	_ground_circle(enemy.position, enemy.radius + 3.0, Color(0, 0, 0, 0.32), true)
	var scale: float = {"runner": 0.64, "spitter": 0.70, "charger": 0.75, "brute": 0.82, "boss": 0.86}.get(enemy.kind, 0.64)
	var tint := Color(1.40, 1.22, 0.96) if enemy.flash > 0.0 else Color.WHITE
	if enemy.warning > 0.0:
		tint.a = 0.5
	_foot(sprites.enemy_frame(enemy.kind, Projection.project(enemy.direction)), p, scale, tint)
	if enemy.kind == "spitter":
		draw_circle(p + Vector2(0, -60), 3.0, Color("a9e770"))
	elif enemy.kind == "charger":
		draw_polyline(PackedVector2Array([p+Vector2(-4,-60),p+Vector2(0,-64),p+Vector2(4,-60)]), Color("f4bc65"), 2.0)
	elif enemy.kind == "brute":
		draw_rect(Rect2(p + Vector2(-3, -69), Vector2(6, 6)), Color("d3d7df"), false, 1.5)
func _draw_telegraph(enemy: Simulation.Enemy) -> void:
	if enemy.windup <= 0.0:
		return
	var color := Color("eaae55")
	if enemy.action_kind == "charge":
		var end := enemy.position + enemy.action_direction * (158.0 if enemy.kind == "boss" else 120.0)
		var side := enemy.action_direction.orthogonal() * (enemy.radius + 5.0)
		var polygon := PackedVector2Array([screen(enemy.position-side),screen(end-side),screen(end+side),screen(enemy.position+side)])
		draw_colored_polygon(polygon, Color(1,0.62,0.19,0.18))
		_outline(polygon, color, 2.0)
		draw_line(screen(enemy.position), screen(end), color, 2.0)
	elif enemy.action_kind in ["spit", "fan"]:
		var count: int = (7 if enemy.enraged else 5) if enemy.action_kind == "fan" else 1
		for i in range(count):
			var direction := enemy.action_direction.rotated((float(i)-float(count-1)*0.5)*0.19)
			draw_line(screen(enemy.position), screen(enemy.position+direction*150.0), Color(0.63,0.96,0.25,0.78), 1.5)
		_ground_circle(enemy.position, enemy.radius+6, Color("b3ec73"), false)
	elif enemy.action_kind == "pulse":
		var radius: float = 124.0 if enemy.enraged else 108.0
		_ground_circle(enemy.position, radius, Color(1,0.47,0.16,0.12), true)
		_ground_circle(enemy.position, radius, color, false)
func _rect_points(rect: Rect2) -> PackedVector2Array:
	return PackedVector2Array([screen(rect.position), screen(rect.position+Vector2(rect.size.x,0)),screen(rect.end),screen(rect.position+Vector2(0,rect.size.y))])
func _outline(points: PackedVector2Array, color: Color, width: float) -> void:
	var closed := points.duplicate()
	closed.append(points[0])
	draw_polyline(closed, color, width, true)
func _ground_circle(point: Vector2, radius: float, color: Color, filled: bool) -> void:
	var polygon := PackedVector2Array()
	for i in range(28):
		polygon.append(screen(point + Vector2.from_angle(TAU * float(i) / 28.0) * radius))
	if filled:
		draw_colored_polygon(polygon, color)
	else:
		_outline(polygon, color, 1.6)
func _foot(texture: Texture2D, point: Vector2, scale: float, color: Color = Color.WHITE, flip: bool = false) -> void:
	if texture == null:
		return
	var size := texture.get_size() * scale
	var rect := Rect2(point - Vector2(size.x*0.5, size.y-6.0*scale), size)
	if flip:
		rect.position.x += size.x
		rect.size.x = -size.x
	draw_texture_rect(texture, rect, false, color)
func _center(texture: Texture2D, point: Vector2, size: Vector2, color: Color = Color.WHITE) -> void:
	if texture != null:
		draw_texture_rect(texture, Rect2(point-size*0.5,size), false, color)
func _rotated(texture: Texture2D, point: Vector2, size: Vector2, angle: float) -> void:
	if texture == null:
		return
	draw_set_transform(point, angle)
	draw_texture_rect(texture, Rect2(-size*0.5,size), false)
	draw_set_transform(Vector2.ZERO)
