extends Control
## Same Human/Firing objects as gameplay. No damage or approval changes here.
const Human = preload("res://scripts/human_animation.gd")
const Firing = preload("res://scripts/firing_presentation.gd")
const MUZZLE: Texture2D = preload("res://assets/sprites/fx/muzzle_0.png")
var humans: Array[Human] = []
var guns: Array[Firing] = []
var clock: float = 0.0
var next_shot: float = 0.0
var walking: bool = false
var shooting: bool = true
var turning: bool = false
var paused: bool = false
var slow: bool = false
var sockets: bool = false
var hurt_next: bool = false
var info: Label

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_label("LOCKED HUMAN / FIRING ATTACHMENT", Vector2(25, 18), 24)
	_label("Same body pixels. Short muzzle-root flash. Rear-facing flash is occluded by the body.", Vector2(25, 54), 15)
	for i in range(4):
		humans.append(Human.new())
		guns.append(Firing.new())
		_label(["EAST", "SOUTH", "WEST", "NORTH"][i], Vector2(85 + i * 224, 86), 16)
	_label("GAME SCALE", Vector2(25, 228), 13)
	_label("2x INSPECTION", Vector2(25, 389), 13)
	var row := HBoxContainer.new()
	row.position = Vector2(25, 420)
	row.add_theme_constant_override("separation", 8)
	add_child(row)
	for name: String in ["Walk", "Fire", "Turn", "Hit", "Pause", "0.5x", "Sockets", "Return"]:
		var button := Button.new()
		button.text = name
		button.custom_minimum_size = Vector2(100, 38)
		button.pressed.connect(func() -> void: _action(name))
		row.add_child(button)
	info = _label("", Vector2(25, 475), 14)
	info.size = Vector2(900, 56)
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.text = "Inspect standing, walking, turns and hit poses. No whole-body recoil. Free gameplay aim is unchanged; four fixed gun drawings still limit angular accuracy."

func _process(dt: float) -> void:
	if paused:
		return
	var step := dt * (0.5 if slow else 1.0)
	clock += step
	next_shot -= step
	var fired := shooting and next_shot <= 0.0
	if fired:
		next_shot = 0.30
	for i in range(4):
		var facing := (i + floori(clock * 1.4)) % 4 if turning else i
		humans[i].advance(step, walking, Vector2.from_angle(float(facing) * PI * 0.5), hurt_next, fired, true)
		guns[i].advance(step, humans[i], fired, [], 450.0, 0.96)
	hurt_next = false
	queue_redraw()

func _draw() -> void:
	draw_rect(Rect2(0, 0, 960, 540), Color("1b2225"))
	for i in range(humans.size()):
		for row in range(2):
			var scale: float = 0.96 if row == 0 else 1.65
			var x: float = float(124 + i * 224) + (sin(clock * 2.0) * 16.0 if walking else 0.0)
			var ground := Vector2(x, 220.0 if row == 0 else 385.0)
			draw_line(ground - Vector2(47, 0), ground + Vector2(47, 0), Color("556064"), 1.0)
			guns[i].draw_flash(self, humans[i], ground, scale, MUZZLE, true)
			draw_texture_rect(humans[i].texture(), Rect2(ground - Human.PIVOT * scale, Vector2(128, 128) * scale), false)
			guns[i].draw_flash(self, humans[i], ground, scale, MUZZLE, false)
			if sockets:
				var muzzle := ground + Firing.muzzle_offset(humans[i], scale)
				draw_circle(muzzle, 2.5, Color("70BFDC"))
				draw_line(muzzle, muzzle + Firing.barrel_axis(humans[i]) * 16.0, Color("70BFDC"), 1.0)

func _action(name: String) -> void:
	match name:
		"Walk": walking = not walking
		"Fire": shooting = not shooting
		"Turn": turning = not turning
		"Hit": hurt_next = true
		"Pause": paused = not paused
		"0.5x": slow = not slow
		"Sockets": sockets = not sockets
		"Return": get_tree().change_scene_to_file("res://scenes/main.tscn")
	queue_redraw()

func _label(text: String, position_value: Vector2, font_size: int) -> Label:
	var label := Label.new()
	label.text = text
	label.position = position_value
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", Color("dddacb"))
	add_child(label)
	return label

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		_action("Return")
