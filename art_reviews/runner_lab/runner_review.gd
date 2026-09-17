extends Control
## Standalone review of the existing runner candidate. No gameplay or approvals.
const CLIPS: Array[String] = ["idle", "move", "attack", "hit", "death"]
const DIRECTIONS: Array[String] = ["e", "s", "w", "n"]
const CELL := Vector2(96, 96)
const PIVOT := Vector2(48, 78)
const EXPECTED := {"idle": 4, "move": 6, "attack": 4, "hit": 2, "death": 5}
var atlas: Texture2D
var sequences: Dictionary = {}
var clips: Dictionary = {}
var clip: String = "move"
var clock: float = 0.0
var paused: bool = false
var half_speed: bool = false
var bright: bool = false
var show_pivots: bool = true
var loaded: bool = false
var frames_total: int = 0
var frame_slider: HSlider
var status: Label

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_build_ui()
	loaded = _load_art()
	if loaded:
		play_clip("move")
	queue_redraw()

func _load_art() -> bool:
	atlas = load("res://assets/runner_review/atlas.png") as Texture2D
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://assets/runner_review/animation_index.json"))
	if atlas == null or not parsed is Dictionary:
		return _fail("Runner atlas or metadata is missing.")
	var data: Dictionary = parsed
	if data.get("asset_id") != "runner" or data.get("status") != "review":
		return _fail("Expected the runner review candidate, not another asset.")
	if data.get("cell") != [96, 96] or data.get("pivot") != [48, 78]:
		return _fail("Runner frame size or pivot differs from the current contract.")
	clips = data.get("clips", {})
	for name in CLIPS:
		if not clips.has(name) or int(clips[name].get("frames", 0)) != int(EXPECTED[name]):
			return _fail("Missing or incorrect clip: " + name)
		if float(clips[name].get("fps", 0.0)) <= 0.0:
			return _fail("Invalid playback rate: " + name)
		for direction in DIRECTIONS:
			var ordered: Array = []
			ordered.resize(int(EXPECTED[name]))
			sequences[name + "_" + direction] = ordered
	for item in data.get("frames", []):
		var key: String = String(item.get("clip", "")) + "_" + String(item.get("direction", ""))
		var number: int = int(item.get("frame", -1))
		if not sequences.has(key) or number < 0 or number >= sequences[key].size():
			return _fail("Unexpected frame ID.")
		if sequences[key][number] != null:
			return _fail("Duplicate frame ID.")
		var region: Array = item.get("region", [])
		if region.size() != 4:
			return _fail("Missing atlas rectangle.")
		var rect := Rect2(float(region[0]), float(region[1]), float(region[2]), float(region[3]))
		if rect.size != CELL or not Rect2(Vector2.ZERO, atlas.get_size()).encloses(rect):
			return _fail("Frame outside the actual atlas.")
		sequences[key][number] = rect
		frames_total += 1
	for sequence in sequences.values():
		if sequence.has(null):
			return _fail("Incomplete runner sequence.")
	return frames_total == 84

func _fail(message: String) -> bool:
	status.text = message
	push_error(message)
	return false

func _build_ui() -> void:
	_text("RUNNER / ANIMATION REVIEW", Vector2(24, 16), 25)
	_text("84 candidate frames | same source model | human and gameplay untouched", Vector2(24, 50), 15)
	for i in range(4):
		_text(["EAST", "SOUTH", "WEST", "NORTH"][i], Vector2(93 + i * 228, 87), 15)
	_text("1x", Vector2(25, 167), 13)
	_text("2x", Vector2(25, 291), 13)
	var clip_row := HBoxContainer.new()
	clip_row.position = Vector2(24, 385)
	clip_row.add_theme_constant_override("separation", 8)
	add_child(clip_row)
	for name in CLIPS:
		var button := Button.new()
		button.text = name.capitalize()
		button.custom_minimum_size = Vector2(125, 35)
		button.pressed.connect(play_clip.bind(name))
		clip_row.add_child(button)
	var controls := HBoxContainer.new()
	controls.position = Vector2(24, 431)
	controls.add_theme_constant_override("separation", 8)
	add_child(controls)
	for name: String in ["Play/Pause", "0.5x", "Background", "Pivots", "Restart"]:
		var button := Button.new()
		button.text = name
		button.custom_minimum_size = Vector2(116, 35)
		button.pressed.connect(_action.bind(name))
		controls.add_child(button)
	frame_slider = HSlider.new()
	frame_slider.position = Vector2(704, 430)
	frame_slider.size = Vector2(227, 35)
	frame_slider.step = 1.0
	frame_slider.value_changed.connect(_scrub)
	add_child(frame_slider)
	status = _text("Loading actual PNG atlas...", Vector2(24, 480), 15)
	_text("Review only: not final artwork approval. Non-looping attacks and deaths hold their last frame.", Vector2(24, 510), 13)

func _text(value: String, point: Vector2, size: int) -> Label:
	var label := Label.new()
	label.text = value
	label.position = point
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", Color("d8d9cd"))
	add_child(label)
	return label

func play_clip(name: String) -> void:
	if not loaded or not clips.has(name):
		return
	clip = name
	clock = 0.0
	paused = false
	frame_slider.set_value_no_signal(0.0)
	frame_slider.max_value = float(int(clips[clip].frames) - 1)
	_refresh()

func frame_index() -> int:
	if not loaded:
		return 0
	var count: int = int(clips[clip].frames)
	var frame: int = floori(clock * float(clips[clip].fps) + 0.00001)
	return posmod(frame, count) if bool(clips[clip].loop) else mini(frame, count - 1)

func advance(dt: float) -> void:
	if not loaded or paused or dt <= 0.0:
		return
	var duration: float = float(clips[clip].frames) / float(clips[clip].fps)
	clock += dt * (0.5 if half_speed else 1.0)
	if bool(clips[clip].loop):
		clock = fmod(clock, duration)
	else:
		clock = minf(clock, duration)
	_refresh()

func _process(dt: float) -> void:
	advance(dt)

func _refresh() -> void:
	frame_slider.set_value_no_signal(float(frame_index()))
	status.text = "%s | frame %d / %d | %s | %s | review candidate" % [clip.to_upper(), frame_index()+1, int(clips[clip].frames), "0.5x" if half_speed else "1x", "paused" if paused else "playing"]
	queue_redraw()

func _scrub(value: float) -> void:
	if not loaded:
		return
	paused = true
	clock = value / float(clips[clip].fps)
	_refresh()

func _action(name: String) -> void:
	if not loaded:
		return
	match name:
		"Play/Pause": paused = not paused
		"0.5x": half_speed = not half_speed
		"Background": bright = not bright
		"Pivots": show_pivots = not show_pivots
		"Restart": play_clip(clip)
	_refresh()

func _draw() -> void:
	draw_rect(Rect2(0, 0, 960, 550), Color("192124"))
	if not loaded:
		return
	for i in range(4):
		var panel := Rect2(47 + i * 228, 115, 202, 251)
		draw_rect(panel, Color("c5c3b7") if bright else Color("242e31"))
		var region: Rect2 = sequences[clip + "_" + DIRECTIONS[i]][frame_index()]
		for row in range(2):
			var scale_value: float = 1.0 if row == 0 else 2.0
			var origin := Vector2(144 + i * 228, 198 if row == 0 else 348)
			if show_pivots:
				draw_line(origin - Vector2(39, 0), origin + Vector2(39, 0), Color("72847f"), 1.0)
			draw_texture_rect_region(atlas, Rect2(origin - PIVOT * scale_value, CELL * scale_value), region)
			if show_pivots:
				draw_circle(origin, 2.0, Color("d4a55e"))
