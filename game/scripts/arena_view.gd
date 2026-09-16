extends Node2D
## Cosmetic-only view; effects have a separate random stream and hard caps.

const Simulation = preload("res://scripts/simulation.gd")
const Sprites = preload("res://scripts/sprite_factory.gd")
var sim: Simulation
var sprites: Sprites
var camera := Vector2(896, 576)
var fx: Array[Dictionary] = []
var corpses: Array[Dictionary] = []
var cosmetic_rng := RandomNumberGenerator.new()
var gore: bool = true
var shake_enabled: bool = false
var shake: float = 0.0
var player_animation: float = 0.0
var offset := Vector2.ZERO

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprites = Sprites.new()
	cosmetic_rng.seed = 777

func reset() -> void:
	fx.clear()
	corpses.clear()
	shake = 0.0
	player_animation = 0.0
	camera = sim.player
	offset = Vector2.ZERO
	queue_redraw()

func screen_to_world(point: Vector2) -> Vector2:
	return point + camera - Vector2(480, 270) - offset

func advance(dt: float, moving: bool, events: Array[Dictionary]) -> void:
	if moving:
		player_animation += dt
	camera = sim.player.clamp(Vector2(480, 270), sim.arena.SIZE - Vector2(480, 270))
	for event in events:
		var type: String = event.type
		if type == "death" and gore:
			corpses.append({"position": event.position, "direction": event.direction})
			if corpses.size() > 80:
				corpses.pop_front()
		if type in ["shot", "hit", "hurt", "spark"]:
			fx.append({"type": type, "position": event.position, "direction": event.get("direction", Vector2.RIGHT), "life": 0.13})
			if fx.size() > 80:
				fx.pop_front()
		if type == "hurt" and shake_enabled:
			shake = 2.5
	for index in range(fx.size() - 1, -1, -1):
		fx[index].life -= dt
		if fx[index].life <= 0.0:
			fx.remove_at(index)
	shake = maxf(0.0, shake - dt * 18.0)
	offset = Vector2(cosmetic_rng.randf_range(-shake, shake), cosmetic_rng.randf_range(-shake, shake)) if shake > 0.0 else Vector2.ZERO
	queue_redraw()

func _draw() -> void:
	if sim == null or sprites == null:
		return
	draw_set_transform(Vector2(480, 270) - camera + offset)
	var corner := camera - Vector2(480, 270)
	for y in range(maxi(0, floori(corner.y / 64.0)), mini(18, ceili((corner.y + 540.0) / 64.0) + 1)):
		for x in range(maxi(0, floori(corner.x / 64.0)), mini(28, ceili((corner.x + 960.0) / 64.0) + 1)):
			var tile := posmod(x * 17 + y * 13, 13)
			draw_texture(sprites.floor_tiles[3 if tile == 0 else tile % 3], Vector2(x, y) * 64)
	draw_rect(sim.arena.bounds, Color("54614a"), false, 3)
	draw_rect(sim.arena.bounds.grow(12), Color("090e0c"), false, 22)
	# Painted maintenance lanes and landing pad, never collision geometry.
	draw_rect(Rect2(736, 456, 320, 240), Color(0.5, 0.55, 0.37, 0.06))
	draw_rect(Rect2(736, 456, 320, 240), Color("56604a"), false, 2)
	draw_circle(Vector2(896, 576), 54, Color("4a5847"), false, 2)
	draw_line(Vector2(870, 576), Vector2(922, 576), Color("68725b"), 2)
	draw_line(Vector2(896, 550), Vector2(896, 602), Color("68725b"), 2)
	for corpse in corpses:
		var p: Vector2 = corpse.position
		draw_circle(p, 13, Color(0.26, 0.17, 0.13, 0.55))
		draw_texture(sprites.frame_for(false, corpse.direction, 0), p - Vector2(32, 42), Color(0.4, 0.38, 0.27, 0.72))
	for pickup in sim.pickups:
		var p: Vector2 = pickup.position
		var pulse := 0.7 + sin(pickup.age * 4.0) * 0.15
		draw_colored_polygon(PackedVector2Array([p + Vector2(0, -5), p + Vector2(4, 0), p + Vector2(0, 5), p + Vector2(-4, 0)]), Color(0.48, pulse, 0.81))
		draw_line(p + Vector2(0, -3), p + Vector2(2, 0), Color("d2eed3"), 1)
	var actors: Array[Dictionary] = []
	for rect in sim.arena.blockers:
		actors.append({"y": rect.end.y, "rect": rect})
	for enemy in sim.enemies:
		if absf(enemy.position.x - camera.x) > 540 or absf(enemy.position.y - camera.y) > 330:
			continue
		if enemy.warning > 0.0:
			draw_circle(enemy.position, 19, Color(0.8, 0.42, 0.16, 0.5), false, 2)
			draw_line(enemy.position - Vector2(5, 0), enemy.position + Vector2(5, 0), Color("d59453"), 2)
		else:
			actors.append({"y": enemy.position.y, "enemy": enemy})
	actors.append({"y": sim.player.y, "player": true})
	actors.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a.y) < float(b.y))
	for actor in actors:
		if actor.has("rect"):
			_draw_blocker(actor.rect)
		elif actor.has("enemy"):
			var enemy = actor.enemy
			var tint := Color(1.7, 1.5, 1.15) if enemy.flash > 0.0 else Color.WHITE
			draw_texture(sprites.frame_for(false, enemy.direction, enemy.age), enemy.position - Vector2(32, 42), tint)
		else:
			draw_arc(sim.player + Vector2(0, 2), 16, 0.1, PI - 0.1, 12, Color("95b8a2"), 1)
			var tint := Color(1.5, 0.8, 0.6) if sim.hurt_timer > 0.5 else Color.WHITE
			draw_texture(sprites.frame_for(true, sim.facing, player_animation), sim.player - Vector2(32, 42), tint)
	for bullet in sim.bullets:
		var tail := bullet.position - bullet.velocity.normalized() * 12
		draw_line(tail, bullet.position, Color("a6874d"), 2)
		draw_line(bullet.position - bullet.velocity.normalized() * 4, bullet.position, Color("fff0b0"), 2)
	for effect in fx:
		var p: Vector2 = effect.position
		if effect.type == "shot":
			p += Vector2(effect.direction.x, effect.direction.y * 0.64) * 26 + Vector2(0, -10)
			draw_circle(p, 4, Color("f6d391"))
			draw_line(p - Vector2(8, 0), p + Vector2(8, 0), Color("b8a678"), 1)
		elif effect.type == "hit" and gore:
			for index in range(5):
				var end := p + Vector2.from_angle(float(index) * 1.9) * (8.0 + (0.13 - float(effect.life)) * 70.0)
				draw_line(p, end, Color("857747"), 1)
		elif effect.type == "spark":
			draw_line(p - Vector2(4, 4), p + Vector2(4, 4), Color("e6ba75"), 1)
	draw_set_transform(Vector2.ZERO)

func _draw_blocker(rect: Rect2) -> void:
	var top := Rect2(rect.position - Vector2(0, 18), rect.size)
	draw_rect(Rect2(rect.position + Vector2(6, 7), rect.size + Vector2(4, 2)), Color(0, 0, 0, 0.35))
	draw_rect(rect, Color("19211f"))
	draw_rect(top, Color("424b42"))
	draw_rect(top.grow(-4), Color("343d36"))
	draw_line(top.position, top.position + Vector2(top.size.x, 0), Color("7a8065"), 2)
	for x in range(int(top.position.x) + 8, int(top.end.x) - 6, 12):
		draw_line(Vector2(x, top.position.y + 8), Vector2(x, top.end.y - 8), Color("272f2b"), 3)
	draw_rect(Rect2(rect.position.x, rect.end.y - 5, rect.size.x, 5), Color("746b3e"))
	for x in range(int(rect.position.x), int(rect.end.x) - 6, 16):
		draw_line(Vector2(x, rect.end.y - 5), Vector2(x + 6, rect.end.y), Color("282b24"), 4)
