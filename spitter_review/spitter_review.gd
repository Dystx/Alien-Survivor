extends Control
## The spitter art and frame lookup are exactly those used by combat.
const Spitter = preload("res://scripts/spitter_animation.gd")
var clip: String = "move"
var clock: float = 0.0
var paused: bool = false
var speed: float = 1.0
var bright: bool = false
var status: Label

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var title := Label.new()
	title.text = "SPITTER ANIMATION REVIEW / 108 FRAMES / CANDIDATE"
	title.position = Vector2(28, 20)
	title.add_theme_font_size_override("font_size", 20)
	add_child(title)
	var bar := HBoxContainer.new()
	bar.position = Vector2(28, 68)
	add_child(bar)
	for text: String in ["Idle", "Move", "Windup", "Attack", "Recovery", "Hit", "Death", "Pause", "0.5x", "Return"]:
		var button := Button.new()
		button.text = text
		button.custom_minimum_size = Vector2(86, 38)
		button.pressed.connect(_action.bind(text))
		bar.add_child(button)
	status = Label.new()
	status.position = Vector2(28, 490)
	status.add_theme_font_size_override("font_size", 14)
	add_child(status)
	queue_redraw()

func _action(value: String) -> void:
	match value:
		"Pause": paused = not paused
		"0.5x": speed = 0.5 if speed == 1.0 else 1.0
		"Background": bright = not bright
		"Return": get_tree().change_scene_to_file("res://scenes/main.tscn")
		_:
			clip = value.to_lower()
			clock = 0.0
	queue_redraw()

func _process(dt: float) -> void:
	if not paused:
		clock += dt * speed
	status.text = "%s | %.1fx | %s | Seven clips. Simulation owns release timing. No damage from animation frames." % [clip.to_upper(), speed, "PAUSED" if paused else "PLAYING"]
	queue_redraw()

func _draw() -> void:
	draw_rect(Rect2(0,0,960,540), Color("a8aba3") if bright else Color("181e21"))
	var directions: Array[Vector2] = [Vector2.RIGHT, Vector2.DOWN, Vector2.LEFT, Vector2.UP]
	for i in range(4):
		var point := Vector2(125 + i * 235, 233)
		var key := StringName(clip + "_" + Spitter.facing(directions[i]))
		var length := Spitter.Frames.get_frame_count(key) / Spitter.Frames.get_animation_speed(key)
		var time := fposmod(clock, length + 0.7) if not Spitter.Frames.get_animation_loop(key) else clock
		var texture: Texture2D = Spitter.texture(clip, directions[i], time)
		draw_texture_rect(texture, Rect2(point - Spitter.PIVOT, Spitter.CELL), false)
		point.y = 453
		draw_texture_rect(texture, Rect2(point - Spitter.PIVOT * 2.0, Spitter.CELL * 2.0), false)
		draw_line(point - Vector2(5,0), point + Vector2(5,0), Color("e1ba72"), 1.0)
