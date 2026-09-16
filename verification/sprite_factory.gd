extends RefCounted
const ROOT: String = "res://assets/sprites/"
var textures: Dictionary = {}
var fixture_mode: bool = OS.get_cmdline_user_args().has("--ci-art-fixtures")
var missing: Array[String] = []
func _init() -> void:
	if fixture_mode:
		print("ART_FIXTURES: temporary solid textures; rendered artwork is NOT tested")
	for i in range(8):
		_register("player/facing_%d" % i, Vector2i(96, 112))
		for kind: String in ["runner", "spitter", "charger", "brute"]:
			_register("enemies/%s/facing_%d" % [kind, i], Vector2i(112, 104))
	_register("boss/warden", Vector2i(224, 208))
	for i in range(6):
		_register("environment/floor/tile_%d" % i, Vector2i(128, 64))
	for name: String in ["wall_light", "wall_pipe", "wall_plain", "corner", "barrier", "fence", "crate_green", "crate_steel", "crate_hazard", "door_red", "door_green", "terminal", "console", "grate", "vent", "infestation_0", "infestation_1"]:
		_register("environment/props/" + name, Vector2i(192, 192))
	for name: String in ["muzzle_0", "muzzle_1", "spark", "acid_bolt", "acid_pool", "blood_0", "blood_1", "blood_pool"]:
		_register("fx/" + name, Vector2i(96, 80))
	for name: String in ["xp", "health", "drone", "mine", "icon_damage", "icon_rate", "icon_health", "icon_flame"]:
		_register("fx/" + name, Vector2i(64, 64))
	for i in range(5):
		_register("fx/explosion_%d" % i, Vector2i(128, 128))
	for i in range(3):
		_register("fx/corpse_%d" % i, Vector2i(104, 64))
	for i in range(4):
		_register("weapons/primary_%d" % i, Vector2i(160, 72))
func _register(id: String, size: Vector2i) -> void:
	if fixture_mode:
		var image := Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)
		image.fill(Color(0.45, 0.48, 0.52, 1.0))
		textures[id] = ImageTexture.create_from_image(image)
		return
	var path: String = ROOT + id + ".png"
	if not ResourceLoader.exists(path):
		missing.append(path)
		push_error("MISSING REQUIRED ART: " + path)
		return
	var texture := load(path) as Texture2D
	if texture == null:
		missing.append(path)
		push_error("INVALID REQUIRED ART: " + path)
		return
	textures[id] = texture
func tex(id: String) -> Texture2D:
	return textures.get(id) as Texture2D
func facing(direction: Vector2) -> int:
	return posmod(roundi(direction.angle() / (TAU / 8.0)), 8)
func player_frame(screen_direction: Vector2) -> Texture2D:
	return tex("player/facing_%d" % facing(screen_direction))
func enemy_frame(kind: String, screen_direction: Vector2) -> Texture2D:
	if kind == "boss":
		return tex("boss/warden")
	return tex("enemies/%s/facing_%d" % [kind, facing(screen_direction)])
