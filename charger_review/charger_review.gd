extends Control
## Actual combat atlas and selector. No gameplay simulation runs in this viewer.
const Charger = preload("res://scripts/charger_animation.gd")
const CLIPS: Array[String] = ["idle", "move", "windup", "charge", "recovery", "hit", "death"]
var clip: String = "move"
var clock: float = 0.0
var paused: bool = false
var speed: float = 1.0
var bright: bool = false
var status: Label
var slider: HSlider

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var title := Label.new()
	title.text = "CHARGER / 124 FRAMES / ANIMATION REVIEW"
	title.position = Vector2(24, 16)
	title.add_theme_font_size_override("font_size", 22)
	add_child(title)
	var actions := HBoxContainer.new()
	actions.position = Vector2(24, 55)
	add_child(actions)
	for name in CLIPS:
		var button := Button.new()
		button.text = name.capitalize()
		button.custom_minimum_size = Vector2(104, 34)
		button.pressed.connect(play_clip.bind(name))
		actions.add_child(button)
	var controls := HBoxContainer.new()
	controls.position = Vector2(24, 442)
	add_child(controls)
	for name: String in ["Pause", "0.5x", "Background", "Replay", "Return"]:
		var button := Button.new()
		button.text = name
		button.custom_minimum_size = Vector2(108, 34)
		button.pressed.connect(_action.bind(name))
		controls.add_child(button)
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
	slider.max_value = Charger.Frames.get_frame_count(StringName(clip + "_e")) - 1
	slider.set_value_no_signal(0.0)
	queue_redraw()

func _scrub(frame: float) -> void:
	paused = true
	clock = frame / Charger.Frames.get_animation_speed(StringName(clip + "_e"))
	queue_redraw()

func _action(name: String) -> void:
	match name:
		"Pause": paused = not paused
		"0.5x": speed = 0.5 if speed == 1.0 else 1.0
		"Background": bright = not bright
		"Replay": play_clip(clip)
		"Return": get_tree().change_scene_to_file("res://scenes/main.tscn")
	queue_redraw()

func _process(dt: float) -> void:
	var key := StringName(clip + "_e")
	var fps := Charger.Frames.get_animation_speed(key)
	var count := Charger.Frames.get_frame_count(key)
	if not paused:
		clock += dt * speed
		clock = fposmod(clock, count / fps) if Charger.Frames.get_animation_loop(key) else minf(clock, count / fps)
	var frame := mini(count - 1, maxi(0, floori(clock * fps + 0.00001)))
	slider.set_value_no_signal(frame)
	status.text = "%s | FRAME %d/%d | %.1fx | %s | native / 1.5x | review candidate, not final approval" % [clip.to_upper(), frame+1, count, speed, "PAUSED" if paused else "PLAYING"]
	queue_redraw()

func _draw() -> void:
	draw_rect(Rect2(0,0,960,540), Color("181f22"))
	var directions: Array[Vector2] = [Vector2.RIGHT, Vector2.DOWN, Vector2.LEFT, Vector2.UP]
	for i in range(4):
		draw_rect(Rect2(22+i*235,105,210,324), Color("aaa99d") if bright else Color("273134"))
		var point := Vector2(124+i*235, 229)
		var image: Texture2D = Charger.texture(clip,directions[i],clock)
		draw_texture_rect(image,Rect2(point-Charger.PIVOT,Charger.CELL),false)
		point.y = 398
		draw_texture_rect(image,Rect2(point-Charger.PIVOT*1.5,Charger.CELL*1.5),false)
		draw_line(point-Vector2(6,0),point+Vector2(6,0),Color("d7b377"),1.0)
