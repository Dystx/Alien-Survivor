extends Control
## Native review screen. Does not approve art or modify gameplay state.
signal closed
const MotionBank = preload("res://scripts/motion_bank.gd")
var bank: MotionBank
var family: String = "player"
var clip: String = "walk"
var direction: Vector2 = Vector2.RIGHT
var clock: float = 0.0
var speed: float = 1.0
var playing: bool = true
var bright: bool = false
var clips: OptionButton
var slider: HSlider
var readout: Label

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var title := Label.new()
	title.text = "ANIMATION LAB / HUMAN SURVIVOR + ALIEN FAMILY"
	title.position = Vector2(24, 20)
	title.add_theme_font_size_override("font_size", 20)
	add_child(title)
	var kinds := OptionButton.new()
	kinds.position = Vector2(24, 72)
	kinds.size = Vector2(196, 36)
	for kind: String in bank.families:
		kinds.add_item(kind)
	kinds.item_selected.connect(func(i: int) -> void:
		family = kinds.get_item_text(i)
		_refresh_clips())
	add_child(kinds)
	clips = OptionButton.new()
	clips.position = Vector2(232, 72)
	clips.size = Vector2(220, 36)
	clips.item_selected.connect(func(i: int) -> void:
		clip = clips.get_item_text(i)
		clock = 0.0)
	add_child(clips)
	var dirs := OptionButton.new()
	dirs.position = Vector2(466, 72)
	dirs.size = Vector2(126, 36)
	for name: String in ["E / right", "S / front", "W / left", "N / rear"]:
		dirs.add_item(name)
	dirs.item_selected.connect(func(i: int) -> void: direction = Vector2.from_angle(float(i) * PI * 0.5))
	add_child(dirs)
	_button("0.5x / 1x", Vector2(610, 72), func() -> void: speed = 0.5 if speed == 1.0 else 1.0)
	_button("BACKGROUND", Vector2(752, 72), func() -> void: bright = not bright)
	_button("CLOSE", Vector2(820, 18), func() -> void: closed.emit())
	_button("PLAY / PAUSE", Vector2(24, 442), func() -> void: playing = not playing)
	_button("< FRAME", Vector2(210, 442), func() -> void: _step(-1))
	_button("FRAME >", Vector2(352, 442), func() -> void: _step(1))
	slider = HSlider.new()
	slider.position = Vector2(500, 450)
	slider.size = Vector2(400, 24)
	slider.min_value = 0.0
	slider.max_value = 1.0
	slider.step = 0.001
	slider.value_changed.connect(func(v: float) -> void:
		playing = false
		clock = v * maxf(0.0, bank.duration(family, clip) - 0.0001))
	add_child(slider)
	readout = Label.new()
	readout.position = Vector2(24, 492)
	readout.add_theme_font_size_override("font_size", 14)
	add_child(readout)
	_refresh_clips()

func _button(text: String, point: Vector2, callback: Callable) -> void:
	var button := Button.new()
	button.text = text
	button.position = point
	button.size = Vector2(132, 36)
	button.pressed.connect(callback)
	add_child(button)

func _refresh_clips() -> void:
	clips.clear()
	for name: String in bank.families[family].clips:
		clips.add_item(name)
	var preferred: String = "walk" if family == "player" else "move"
	for i in range(clips.item_count):
		if clips.get_item_text(i) == preferred:
			clips.select(i)
	clip = clips.get_item_text(clips.selected)
	clock = 0.0

func _step(delta: int) -> void:
	playing = false
	var c: Dictionary = bank.families[family].clips[clip]
	clock = fposmod(clock + float(delta) / float(c.fps), bank.duration(family, clip))

func _process(dt: float) -> void:
	if bank == null or readout == null:
		return
	var duration: float = bank.duration(family, clip)
	if playing:
		clock = fposmod(clock + dt * speed, duration)
	slider.set_value_no_signal(clock / duration)
	var c: Dictionary = bank.families[family].clips[clip]
	readout.text = "REVIEW CANDIDATE  |  %s / %s / %s  |  %.1fx  |  frame %d of %d" % [family, clip, MotionBank.direction_key(direction), speed, 1 + floori(clock * float(c.fps)), c.directions.e.size()]
	queue_redraw()

func _draw() -> void:
	draw_rect(Rect2(0, 0, 960, 540), Color("252a2c") if not bright else Color("c3c0b6"))
	if bank == null or not bank.has_clip(family, clip):
		return
	var f: Dictionary = bank.sample(family, clip, direction, clock)
	var off: Array = f.offset
	var texture: Texture2D = f.texture
	for spec in [[Vector2(195, 365), 0.86], [Vector2(580, 395), 1.8]]:
		var point: Vector2 = spec[0]
		var scale: float = spec[1]
		draw_line(point-Vector2(40,0), point+Vector2(40,0), Color("709181"), 1.0)
		draw_line(point-Vector2(0,8), point+Vector2(0,8), Color("709181"), 1.0)
		draw_texture_rect(texture, Rect2(point + Vector2(float(off[0]),float(off[1]))*scale,texture.get_size()*scale), false)
		if family == "player":
			var muzzle: Array = f.muzzle
			draw_circle(point+Vector2(float(muzzle[0]),float(muzzle[1]))*scale,2.0,Color("e2b45c"))
	draw_string(ThemeDB.fallback_font, Vector2(132, 410), "GAME SCALE", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color("9aafa4"))
