extends Control
## Actual combat atlas and selector. No gameplay simulation runs in this viewer.
const Warden = preload("res://scripts/warden_animation.gd")
const CLIPS: Array[String] = ["idle", "move", "charge_windup", "charge", "acid_attack", "pulse_attack", "recovery", "hit", "phase_transition", "death"]
var clip: String = "move"
var clock: float = 0.0
var paused: bool = false
var speed: float = 1.0
var bright: bool = false
var status: Label
var slider: HSlider
var focus_direction: int = -1
var view_button: Button

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var title := Label.new()
	title.text = "BROOD WARDEN / 240 FRAMES / ANIMATION REVIEW"
	title.position = Vector2(24, 16)
	title.add_theme_font_size_override("font_size", 22)
	add_child(title)
	var selector := OptionButton.new()
	selector.position = Vector2(24, 55)
	selector.size = Vector2(250, 34)
	for name in CLIPS:
		selector.add_item(name.capitalize())
	selector.select(1)
	selector.item_selected.connect(func(index: int) -> void: play_clip(CLIPS[index]))
	add_child(selector)
	var note := Label.new()
	note.text = "Same combat atlas | four views 0.8x | View button: each direction at native size"
	note.position = Vector2(290, 62)
	note.add_theme_font_size_override("font_size", 13)
	add_child(note)
	var controls := HBoxContainer.new()
	controls.position = Vector2(24, 442)
	add_child(controls)
	for name: String in ["Pause", "0.5x", "Background", "Replay", "View", "Return"]:
		var button := Button.new()
		button.text = name
		button.custom_minimum_size = Vector2(94, 34)
		button.pressed.connect(_action.bind(name))
		controls.add_child(button)
		if name == "View": view_button = button
	slider = HSlider.new()
	slider.position = Vector2(622, 442)
	slider.size = Vector2(307, 34)
	slider.step = 1.0
	slider.value_changed.connect(_scrub)
	add_child(slider)
	status = Label.new()
	status.position = Vector2(24, 490)
	status.add_theme_font_size_override("font_size", 14)
	add_child(status)
	play_clip("move")

func play_clip(name: String) -> void:
	if not CLIPS.has(name):
		return
	clip = name
	clock = 0.0
	paused = false
	slider.max_value = Warden.Frames.get_frame_count(StringName(clip + "_e")) - 1
	slider.set_value_no_signal(0.0)
	queue_redraw()

func _scrub(frame: float) -> void:
	paused = true
	clock = frame / Warden.Frames.get_animation_speed(StringName(clip + "_e"))
	queue_redraw()

func _action(name: String) -> void:
	match name:
		"Pause": paused = not paused
		"0.5x": speed = 0.5 if speed == 1.0 else 1.0
		"Background": bright = not bright
		"Replay": play_clip(clip)
		"View":
			focus_direction = (focus_direction + 2) % 5 - 1
			view_button.text = "View: " + (["E", "S", "W", "N"][focus_direction] if focus_direction >= 0 else "All")
		"Return": get_tree().change_scene_to_file("res://scenes/main.tscn")
	queue_redraw()

func _process(dt: float) -> void:
	var key := StringName(clip + "_e")
	var fps := Warden.Frames.get_animation_speed(key)
	var count := Warden.Frames.get_frame_count(key)
	if not paused:
		clock += dt * speed
		clock = fposmod(clock, count / fps) if Warden.Frames.get_animation_loop(key) else minf(clock, count / fps)
	var frame := mini(count - 1, maxi(0, floori(clock * fps + 0.00001)))
	slider.set_value_no_signal(frame)
	status.text = "%s | FRAME %d/%d | %.1fx | %s | 4-view 0.8x / single native | review candidate, not final approval" % [clip.to_upper(), frame+1, count, speed, "PAUSED" if paused else "PLAYING"]
	queue_redraw()

func _draw() -> void:
	draw_rect(Rect2(0,0,960,540), Color("181f22"))
	var directions: Array[Vector2] = [Vector2.RIGHT, Vector2.DOWN, Vector2.LEFT, Vector2.UP]
	for i in range(4):
		if focus_direction >= 0 and i != focus_direction:
			continue
		var native: bool = focus_direction >= 0
		var panel := Rect2(260, 105, 440, 324) if native else Rect2(22+i*235,105,210,324)
		draw_rect(panel, Color("aaa99d") if bright else Color("273134"))
		var point := Vector2(480, 378) if native else Vector2(124+i*235, 349)
		var scale_value: float = 1.0 if native else 0.8
		var image: Texture2D = Warden.texture(clip, directions[i], clock)
		draw_texture_rect(image, Rect2(point-Warden.PIVOT*scale_value, Warden.CELL*scale_value), false)
		draw_line(point-Vector2(6,0),point+Vector2(6,0),Color("d7b377"),1.0)
