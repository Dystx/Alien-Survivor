extends Control
## Inspect the actual imported human pixels; no fixture textures in this viewer.
const Human = preload("res://scripts/human_animation.gd")
var actors: Array[AnimatedSprite2D] = []
var slow: bool = false
var paused: bool = false
var info: Label

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var background := ColorRect.new()
	background.color = Color("1b2225")
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(background)
	_label("HUMAN SURVIVOR / ANIMATION REVIEW", Vector2(28, 22), 25)
	_label("Review candidate. Not the complete or approved official pack.", Vector2(28, 63), 15)
	for i in range(4):
		var actor := AnimatedSprite2D.new()
		actor.sprite_frames = Human.FRAMES
		actor.offset = Vector2(0, -46)
		actor.position = Vector2(126 + i * 232, 329)
		actor.scale = Vector2(1.7, 1.7)
		actor.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		add_child(actor)
		actors.append(actor)
		_label(Human.DIRECTIONS[i].to_upper(), Vector2(118+i*232, 347), 18)
	var row := HBoxContainer.new()
	row.position = Vector2(28, 407)
	row.add_theme_constant_override("separation", 8)
	add_child(row)
	for id: String in ["idle", "walk", "hit", "death"]:
		var button := Button.new()
		button.text = id.to_upper()
		button.custom_minimum_size = Vector2(104, 42)
		button.pressed.connect(func() -> void: _play(id))
		row.add_child(button)
	var pause := Button.new()
	pause.text = "PLAY / PAUSE"
	pause.custom_minimum_size = Vector2(132, 42)
	pause.pressed.connect(_toggle_pause)
	row.add_child(pause)
	var speed := Button.new()
	speed.text = "1x / 0.5x"
	speed.custom_minimum_size = Vector2(109, 42)
	speed.pressed.connect(_toggle_speed)
	row.add_child(speed)
	var back := Button.new()
	back.text = "RETURN"
	back.custom_minimum_size = Vector2(105, 42)
	back.pressed.connect(_return)
	row.add_child(back)
	info = _label("", Vector2(28, 472), 14)
	info.custom_minimum_size.x = 890
	info.size.x = 890
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_play("walk")

func _toggle_pause() -> void:
	paused = not paused
	_sync_speed()

func _toggle_speed() -> void:
	slow = not slow
	_sync_speed()

func _sync_speed() -> void:
	for actor in actors:
		actor.speed_scale = 0.0 if paused else (0.5 if slow else 1.0)

func _return() -> void:
	get_tree().change_scene_to_file("res://scenes/main.tscn")

func _play(id: String) -> void:
	for i in range(actors.size()):
		var name := StringName("death_none" if id == "death" else id + "_" + Human.DIRECTIONS[i])
		actors[i].stop()
		actors[i].play(name)
	_sync_speed()
	info.text = "DEATH: one shared fall sequence, not four directional deaths." if id == "death" else "Walk: 6 distinct leg poses per direction. Idle holds a pose. Firing recoil is procedural; strafes remain unfinished."

func _label(text: String, point: Vector2, size: int) -> Label:
	var label := Label.new()
	label.text = text
	label.position = point
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", Color("dddacb"))
	add_child(label)
	return label

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		_return()
