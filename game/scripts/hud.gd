extends CanvasLayer
## Native Godot UI, not world sprites. All menus support keyboard/gamepad focus.

signal action_requested(action: String)
signal upgrade_requested(id: String)
signal setting_requested(key: String, value: Variant)
const Simulation = preload("res://scripts/simulation.gd")
const PAPER := Color("dadcc7")
const MUTED := Color("8c9b8e")
const ACCENT := Color("b5c994")
const PANEL := Color("18221f")
var sim: Simulation
var settings
var controls
var root: Control
var overlay: Control
var health_label: Label
var health_bar: ProgressBar
var xp_bar: ProgressBar
var clock_label: Label
var kills_label: Label
var weapon_label: Label
var debug_label: Label
var pause_button: Button
var bottom_label: Label
var debug_visible: bool = false
var screen_override: String = ""
var signature: String = ""

class TouchOverlay extends Control:
	var router
	func _process(_dt: float) -> void:
		queue_redraw()
	func _draw() -> void:
		if router == null or not router.enabled or not router.touch_visible:
			return
		var left: Vector2 = router.move_origin if router.move_id >= 0 else Vector2(108, 414)
		var right: Vector2 = router.aim_origin if router.aim_id >= 0 else Vector2(852, 414)
		for point in [left, right]:
			draw_circle(point, router.touch_radius, Color(0.75, 0.84, 0.71, 0.1))
			draw_circle(point, router.touch_radius, Color(0.75, 0.84, 0.71, 0.28), false, 1)
		draw_circle(left + router.move_touch * router.touch_radius, 18, Color(0.75, 0.84, 0.71, 0.4))
		draw_circle(right + router.aim_touch * router.touch_radius, 18, Color(0.75, 0.84, 0.71, 0.25))

func _ready() -> void:
	root = Control.new()
	add_child(root)
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var theme := Theme.new()
	theme.default_font_size = 17
	theme.set_color("font_color", "Label", PAPER)
	theme.set_color("font_color", "Button", PAPER)
	theme.set_color("font_hover_color", "Button", Color.WHITE)
	theme.set_color("font_focus_color", "Button", Color.WHITE)
	theme.set_stylebox("normal", "Button", _style(PANEL, Color("4b5c4a"), 1))
	theme.set_stylebox("hover", "Button", _style(Color("2e3c31"), ACCENT, 1))
	theme.set_stylebox("pressed", "Button", _style(Color("42523c"), ACCENT, 1))
	theme.set_stylebox("focus", "Button", _style(Color.TRANSPARENT, ACCENT, 2))
	root.theme = theme
	var band := ColorRect.new()
	band.color = Color(0.035, 0.065, 0.052, 0.94)
	band.position = Vector2.ZERO
	band.size = Vector2(960, 78)
	band.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(band)
	_label_at("VITALS / 01", Vector2(20, 10), 12, MUTED)
	health_label = _label_at("100 / 100", Vector2(20, 28), 19, PAPER)
	health_bar = _bar(Vector2(20, 57), Vector2(180, 5), Color("adbb8a"))
	clock_label = _label_at("05:00", Vector2(425, 10), 29, PAPER)
	_label_at("UNTIL EXTRACTION", Vector2(425, 47), 10, MUTED)
	kills_label = _label_at("0 NEUTRALIZED", Vector2(680, 23), 16, PAPER)
	pause_button = _button("II", "pause")
	root.add_child(pause_button)
	pause_button.position = Vector2(892, 17)
	pause_button.size = Vector2(48, 43)
	pause_button.custom_minimum_size = Vector2(48, 43)
	xp_bar = _bar(Vector2(20, 501), Vector2(920, 5), Color("79b3aa"))
	weapon_label = _label_at("RIFLE / AUTO", Vector2(20, 513), 12, PAPER)
	bottom_label = _label_at("LV 01    MOVE: WASD / LEFT STICK    HOLD AIM: MOUSE / RIGHT STICK", Vector2(243, 513), 11, MUTED)
	debug_label = _label_at("", Vector2(20, 98), 12, ACCENT)
	debug_label.visible = false
	var touch := TouchOverlay.new()
	touch.router = controls
	touch.mouse_filter = Control.MOUSE_FILTER_IGNORE
	touch.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(touch)
	overlay = Control.new()
	root.add_child(overlay)
	overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

func _style(fill: Color, border: Color, width: int) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = border
	style.set_border_width_all(width)
	style.content_margin_left = 18
	style.content_margin_right = 18
	style.content_margin_top = 9
	style.content_margin_bottom = 9
	return style

func _label_at(text: String, point: Vector2, font_size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.position = point
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(label)
	return label

func _bar(point: Vector2, dimensions: Vector2, color: Color) -> ProgressBar:
	var bar := ProgressBar.new()
	bar.position = point
	bar.size = dimensions
	bar.show_percentage = false
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bar.add_theme_stylebox_override("background", _style(Color("2a352b"), Color.TRANSPARENT, 0))
	bar.add_theme_stylebox_override("fill", _style(color, Color.TRANSPARENT, 0))
	root.add_child(bar)
	return bar

func _button(text: String, action: String) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(0, 43)
	button.pressed.connect(func() -> void: action_requested.emit(action))
	return button

func _text(parent: Node, text: String, font_size: int = 17, color: Color = PAPER) -> Label:
	var label := Label.new()
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	parent.add_child(label)
	return label

func _container() -> VBoxContainer:
	for child in overlay.get_children():
		overlay.remove_child(child)
		child.queue_free()
	var dark := ColorRect.new()
	dark.color = Color(0.025, 0.045, 0.035, 0.92)
	overlay.add_child(dark)
	dark.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var center := CenterContainer.new()
	overlay.add_child(center)
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var box := VBoxContainer.new()
	box.custom_minimum_size = Vector2(548, 0)
	box.add_theme_constant_override("separation", 11)
	center.add_child(box)
	return box

func _add_button(box: VBoxContainer, text: String, action: String, focus: bool = false) -> Button:
	var button := _button(text, action)
	box.add_child(button)
	if focus:
		button.grab_focus.call_deferred()
	return button

func refresh(force: bool = false) -> void:
	var current := "%s/%s/%s" % [sim.phase, sim.level, screen_override]
	if current == signature and not force:
		return
	signature = current
	overlay.visible = sim.phase != Simulation.Phase.RUNNING or not screen_override.is_empty()
	pause_button.visible = sim.phase == Simulation.Phase.RUNNING
	if not overlay.visible:
		return
	var box := _container()
	if screen_override == "settings":
		_text(box, "FIELD SETTINGS", 29)
		_text(box, "Local preferences. No account or cloud connection.", 13, MUTED)
		for key in ["muted", "gore", "shake", "touch"]:
			var label: String = {"muted": "MUTE AUDIO", "gore": "BLOOD & CORPSES", "shake": "CAMERA SHAKE", "touch": "SHOW TOUCH CONTROLS"}[key]
			var button := Button.new()
			button.text = "%s  //  %s" % [label, "ON" if settings.values[key] else "OFF"]
			button.custom_minimum_size.y = 39
			button.pressed.connect(func() -> void: setting_requested.emit(key, not bool(settings.values[key])))
			box.add_child(button)
		_text(box, "TOUCH RADIUS  //  %d" % int(settings.values.touch_radius), 13, MUTED)
		var slider := HSlider.new()
		slider.min_value = 40
		slider.max_value = 100
		slider.step = 5
		slider.value = float(settings.values.touch_radius)
		slider.value_changed.connect(func(value: float) -> void: setting_requested.emit("touch_radius", value))
		box.add_child(slider)
		_add_button(box, "BACK", "back", true)
		return
	if screen_override == "diagnostics":
		_text(box, "REPEATABLE COMBAT TEST", 27)
		_text(box, "Fixed seed 1709. Real live actors, not an FPS promise.\nNo new spawns. F3 toggles live diagnostic counters.", 14, MUTED)
		for count in [25, 50, 100]:
			_add_button(box, "START WITH %d ALIENS" % count, "benchmark_%d" % count, count == 25)
		_add_button(box, "BACK", "back")
		return
	match sim.phase:
		Simulation.Phase.MENU:
			_text(box, "SECTOR 07  /  QUARANTINE BREACH", 13, ACCENT)
			_text(box, "ALIEN SURVIVOR", 48)
			_text(box, "Five minutes. One rifle. No way back.", 20)
			_text(box, "Keep moving. Fire automatically. Collect blue XP.\nChoose upgrades. Survive until extraction.", 15, MUTED)
			_add_button(box, "DEPLOY  /  FIVE-MINUTE RUN", "start", true)
			var row := HBoxContainer.new()
			row.add_theme_constant_override("separation", 10)
			box.add_child(row)
			for item in [["SETTINGS", "settings"], ["DIAGNOSTICS", "diagnostics"]]:
				var button := _button(item[0], item[1])
				button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
				row.add_child(button)
			_text(box, "NATIVE GODOT PROTOTYPE  /  ORIGINAL PLACEHOLDER ART", 10, MUTED)
		Simulation.Phase.PAUSED:
			_text(box, "TRANSMISSION PAUSED", 29)
			_text(box, "The run clock and combat are stopped.", 15, MUTED)
			_add_button(box, "RESUME", "resume", true)
			_add_button(box, "SETTINGS", "settings")
			_add_button(box, "RESTART RUN", "start")
			_add_button(box, "RETURN TO TITLE", "menu")
		Simulation.Phase.UPGRADE:
			_text(box, "LEVEL %02d  /  CHOOSE ONE" % sim.level, 29)
			_text(box, "Combat is paused. This choice lasts for the current run.", 14, MUTED)
			for index in range(sim.offers.size()):
				var id: String = sim.offers[index]
				var data: Dictionary = Simulation.UPGRADES.get(id, {"name": "EMERGENCY SUPPLY", "detail": "Restore 25 health. Other upgrades are fully ranked.", "tag": "SUPPLY"})
				var button := Button.new()
				button.text = "%s  //  %s\n%s" % [data.tag, data.name, data.detail]
				button.custom_minimum_size = Vector2(548, 73)
				button.add_theme_font_size_override("font_size", 16)
				button.pressed.connect(func() -> void: upgrade_requested.emit(id))
				box.add_child(button)
				if index == 0:
					button.grab_focus.call_deferred()
		Simulation.Phase.RESULTS:
			_text(box, "RUN COMPLETE", 13, ACCENT)
			_text(box, sim.result, 32)
			_text(box, "%s SURVIVED     /     %d NEUTRALIZED     /     LEVEL %d" % [_time(sim.elapsed), sim.kills, sim.level], 15)
			_text(box, "Prototype run only. No permanent rewards or saved run.", 13, MUTED)
			_add_button(box, "DEPLOY AGAIN", "start", true)
			_add_button(box, "RETURN TO TITLE", "menu")

static func _time(seconds: float) -> String:
	var total := maxi(0, ceili(seconds))
	return "%02d:%02d" % [int(total / 60), total % 60]

func update_counters(frame_ms: float, step_ms: float, manual: bool) -> void:
	health_label.text = "%d / %d" % [ceili(sim.health), int(sim.max_health)]
	health_bar.max_value = sim.max_health
	health_bar.value = sim.health
	xp_bar.max_value = sim.xp_needed()
	xp_bar.value = sim.xp
	clock_label.text = _time(sim.time_limit - sim.elapsed)
	kills_label.text = "%d NEUTRALIZED" % sim.kills
	weapon_label.text = "RIFLE / %s" % ("MANUAL AIM" if manual else "AUTO TARGET")
	bottom_label.text = "LV %02d    XP %d/%d    DAMAGE %d    FIRE %.1f/s    F3 DIAGNOSTICS" % [sim.level, sim.xp, sim.xp_needed(), int(sim.rifle_damage()), 1.0 / sim.rifle_interval()]
	debug_label.visible = debug_visible
	if debug_visible:
		debug_label.text = "PROTOTYPE / NO BENCHMARK GUARANTEE\nGodot %s | %s\nSeed %d  |  %.1f FPS\nFrame %.2f ms  |  Simulation %.2f ms\nAliens %d  /  Bullets %d  /  XP objects %d\nShots %d  |  %.2f active seconds" % [Engine.get_version_info().string, OS.get_name(), sim.seed_value, Engine.get_frames_per_second(), frame_ms, step_ms, sim.enemies.size(), sim.bullets.size(), sim.pickups.size(), sim.shot_count, sim.elapsed]
	refresh()
