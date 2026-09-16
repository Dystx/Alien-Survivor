extends RefCounted
## Original procedural PLACEHOLDER art. No ripped art, fonts or external downloads.
## Replace the returned textures later; simulation never depends on these pixels.

var player_frames: Array[Texture2D] = []
var runner_frames: Array[Texture2D] = []
var floor_tiles: Array[Texture2D] = []

func _init() -> void:
	for direction in range(8):
		for frame in range(4):
			player_frames.append(_actor(direction, frame, true))
			runner_frames.append(_actor(direction, frame, false))
	for index in range(4):
		floor_tiles.append(_floor(index))

static func _pixel(image: Image, x: int, y: int, color: Color) -> void:
	if x >= 0 and y >= 0 and x < image.get_width() and y < image.get_height():
		image.set_pixel(x, y, color)

static func _ellipse(image: Image, center: Vector2, radii: Vector2, color: Color) -> void:
	for y in range(floori(center.y - radii.y), ceili(center.y + radii.y) + 1):
		for x in range(floori(center.x - radii.x), ceili(center.x + radii.x) + 1):
			var distance := (Vector2(x, y) - center) / radii
			if distance.length_squared() <= 1.0:
				_pixel(image, x, y, color)

static func _line(image: Image, start: Vector2, end: Vector2, width: float, color: Color) -> void:
	var count := maxi(1, ceili(start.distance_to(end)))
	for index in range(count + 1):
		_ellipse(image, start.lerp(end, float(index) / float(count)), Vector2(width, width), color)

func _actor(direction: int, frame: int, soldier: bool) -> Texture2D:
	var image := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	image.fill(Color.TRANSPARENT)
	var forward := Vector2.from_angle(float(direction) * TAU / 8.0)
	var side := forward.orthogonal()
	var stride := sin(float(frame) * PI / 2.0)
	var base := Vector2(32, 42)
	var body := base + Vector2(0, -11)
	var projected := Vector2(forward.x, forward.y * 0.64)
	var sideways := Vector2(side.x, side.y * 0.64)
	var ink := Color("111916")
	_ellipse(image, base + Vector2(1, 2), Vector2(16, 6), Color(0, 0, 0, 0.36))
	if soldier:
		for sign_value: float in [-1.0, 1.0]:
			var foot := base + sideways * sign_value * 6.0 + projected * stride * sign_value * 3.0
			_line(image, body + sideways * sign_value * 4.0 + Vector2(0, 5), foot, 3.0, ink)
			_line(image, body + sideways * sign_value * 4.0 + Vector2(0, 5), foot - Vector2(0, 2), 2.0, Color("596353"))
			_ellipse(image, foot + projected * 2.0, Vector2(4, 2), Color("192421"))
		_ellipse(image, body + Vector2(-2, 0), Vector2(10, 11), ink)
		_ellipse(image, body + Vector2(-2, -1), Vector2(8, 9), Color("727965"))
		_ellipse(image, body + Vector2(-3, -3), Vector2(6, 6), Color("97977a"))
		_line(image, body + Vector2(-7, 2), body + Vector2(5, 2), 1, Color("38463e"))
		var gun_start := body + projected * 4.0 + sideways * 5.0 + Vector2(0, 1)
		var gun_end := gun_start + projected * 21.0
		_line(image, body - sideways * 7.0, gun_start + projected * 6.0, 3.0, ink)
		_line(image, body - sideways * 7.0, gun_start + projected * 6.0, 2.0, Color("7c826b"))
		_line(image, gun_start, gun_end, 3.0, ink)
		_line(image, gun_start + Vector2(0, -1), gun_end + Vector2(0, -1), 1.5, Color("7c8a87"))
		_line(image, gun_end - projected * 4.0, gun_end, 2.0, Color("212b29"))
		var head := body + Vector2(0, -9)
		_ellipse(image, head, Vector2(7, 7), ink)
		_ellipse(image, head + Vector2(-1, -1), Vector2(6, 5), Color("aaa789"))
		_ellipse(image, head + projected * 3.0 + Vector2(0, 1), Vector2(4, 2), Color("203c3c"))
		_pixel(image, int(head.x - 2), int(head.y - 4), Color("dad3a5"))
	else:
		body += Vector2(0, 4)
		for pair in range(3):
			for sign_value: float in [-1.0, 1.0]:
				var root := body + projected * (float(pair) * 7.0 - 7.0)
				var swing := sin(float(frame) * PI / 2.0 + float(pair) * 1.8) * sign_value
				var knee := root + sideways * sign_value * 13.0 - projected * (2.0 + swing * 3.0)
				var tip := knee + sideways * sign_value * 5.0 - projected * 7.0 + Vector2(0, 3)
				_line(image, root, knee, 2.5, ink)
				_line(image, knee, tip, 2.0, ink)
				_line(image, root + Vector2(0, -1), knee + Vector2(0, -1), 1.0, Color("728756"))
				_line(image, knee, tip - Vector2(0, 1), 0.7, Color("a6a075"))
		for segment in range(4):
			var center := body + projected * (float(segment) * 5.0 - 9.0) + Vector2(0, -3)
			var width := 8.0 - float(segment) * 0.7
			_ellipse(image, center, Vector2(width, 6), ink)
			_ellipse(image, center + Vector2(-1, -1), Vector2(width - 1, 4), Color("576d42"))
			_ellipse(image, center + Vector2(-2, -2), Vector2(width - 3, 2), Color("869158"))
		var head := body + projected * 12.0 + Vector2(0, -3)
		_ellipse(image, head, Vector2(5, 4), Color("27392a"))
		for sign_value: float in [-1.0, 1.0]:
			var eye := head + sideways * sign_value * 3.0 + projected * 2.0
			_ellipse(image, eye, Vector2(1, 1), Color("efba62"))
			_line(image, head + sideways * sign_value * 3.0, head + projected * 6.0 + sideways * sign_value * 3.0, 1, Color("beb184"))
	return ImageTexture.create_from_image(image)

func _floor(index: int) -> Texture2D:
	var image := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	var rng := RandomNumberGenerator.new()
	rng.seed = 8211 + index
	for y in range(64):
		for x in range(64):
			var noise := rng.randf_range(-0.018, 0.018)
			var c := Color(0.125 + noise, 0.153 + noise, 0.145 + noise)
			if x <= 1 or y <= 1:
				c = Color("171f1e")
			elif x == 2 or y == 2:
				c = Color("303b35")
			if index == 3 and x > 9 and x < 55 and y > 9 and y < 55 and y % 5 <= 1:
				c = Color("131c1a")
			image.set_pixel(x, y, c)
	for corner: Vector2 in [Vector2(5, 5), Vector2(58, 5), Vector2(5, 58), Vector2(58, 58)]:
		_ellipse(image, corner, Vector2(1, 1), Color("566052"))
	return ImageTexture.create_from_image(image)

func frame_for(soldier: bool, direction: Vector2, age: float) -> Texture2D:
	var facing := posmod(roundi(direction.angle() / (TAU / 8.0)), 8)
	var frame := posmod(int(age * 9.0), 4)
	return player_frames[facing * 4 + frame] if soldier else runner_frames[facing * 4 + frame]
