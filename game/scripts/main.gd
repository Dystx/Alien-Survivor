extends Node2D
## Composition root: fixed-step simulation plus replaceable input/view/UI/audio.

const Simulation = preload("res://scripts/simulation.gd")
const View = preload("res://scripts/arena_view.gd")
const Controls = preload("res://scripts/input_router.gd")
const HUD = preload("res://scripts/hud.gd")
const Settings = preload("res://scripts/settings.gd")
const Sound = preload("res://scripts/sound.gd")
var sim := Simulation.new()
var controls := Controls.new()
var settings := Settings.new()
var view: View
var hud: HUD
var sound: Sound
var step_ms: float = 0.0
var frame_ms: float = 16.67
var ui_clock: float = 0.0
var last_manual: bool = false
var smoke_mode: bool = false
var smoke_ticks: int = 0

func _ready() -> void:
	view = View.new()
	view.sim = sim
	add_child(view)
	sound = Sound.new()
	add_child(sound)
	hud = HUD.new()
	hud.sim = sim
	hud.settings = settings
	hud.controls = controls
	add_child(hud)
	hud.action_requested.connect(_on_action)
	hud.upgrade_requested.connect(_on_upgrade)
	hud.setting_requested.connect(_on_setting)
	_apply_settings()
	_show_title()
	if OS.get_cmdline_user_args().has("--smoke"):
		smoke_mode = true
		_start_run()
		sim.time_limit = 3.0
		sim.spawning_enabled = false
		sim.add_enemy(sim.player + Vector2(180, 0))

func _show_title() -> void:
	sim.reset(1709)
	sim.phase = Simulation.Phase.MENU
	controls.set_enabled(false)
	view.reset()
	hud.screen_override = ""
	hud.refresh(true)

func _start_run(count: int = -1) -> void:
	if count >= 0:
		sim.seed_benchmark(count)
		hud.debug_visible = true
	else:
		sim.reset(1709)
	view.reset()
	sound.stop_all()
	controls.clear()
	controls.set_enabled(true)
	hud.screen_override = ""
	hud.refresh(true)

func _physics_process(dt: float) -> void:
	var playable := sim.phase == Simulation.Phase.RUNNING and hud.screen_override.is_empty()
	controls.set_enabled(playable)
	var intent := controls.sample(view.screen_to_world(get_viewport().get_mouse_position()), sim.player)
	last_manual = intent.aim != Vector2.ZERO
	var start := Time.get_ticks_usec()
	sim.step(dt, intent.move, intent.aim)
	step_ms = float(Time.get_ticks_usec() - start) / 1000.0
	if playable:
		view.advance(dt, intent.move != Vector2.ZERO, sim.events)
		sound.consume(dt, sim.events)
	else:
		sound.stop_all()
	if sim.phase != Simulation.Phase.RUNNING:
		controls.set_enabled(false)
	if smoke_mode:
		smoke_ticks += 1
		if sim.phase == Simulation.Phase.UPGRADE:
			sim.choose_upgrade(sim.offers[0])
		if smoke_ticks > 240:
			var passed := sim.phase == Simulation.Phase.RESULTS and sim.kills == 1
			print("SCENE_SMOKE_%s kills=%d shots=%d" % ["PASS" if passed else "FAIL", sim.kills, sim.shot_count])
			get_tree().quit(0 if passed else 1)

func _process(dt: float) -> void:
	frame_ms = lerpf(frame_ms, dt * 1000.0, 0.1)
	ui_clock += dt
	if ui_clock >= 0.1:
		ui_clock = 0.0
		hud.update_counters(frame_ms, step_ms, last_manual)

func _input(event: InputEvent) -> void:
	controls.release_event(event)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause_run"):
		if not hud.screen_override.is_empty():
			_on_action("back")
		elif sim.phase == Simulation.Phase.PAUSED:
			_on_action("resume")
		elif sim.phase == Simulation.Phase.RUNNING or sim.phase == Simulation.Phase.UPGRADE:
			_on_action("pause")
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("debug_hud"):
		hud.debug_visible = not hud.debug_visible
	elif event.is_action_pressed("touch_preview"):
		_on_setting("touch", not bool(settings.values.touch))
	elif controls.handle_event(event):
		get_viewport().set_input_as_handled()

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_APPLICATION_PAUSED:
		if sim != null:
			sim.pause()
		if controls != null:
			controls.clear()
			controls.set_enabled(false)
		if sound != null:
			sound.stop_all()
		if hud != null and is_instance_valid(hud):
			hud.refresh(true)

func _on_action(action: String) -> void:
	if action.begins_with("benchmark_"):
		_start_run(int(action.trim_prefix("benchmark_")))
		return
	match action:
		"start":
			_start_run()
		"menu":
			_show_title()
		"pause":
			sim.pause()
			controls.set_enabled(false)
		"resume":
			sim.resume()
			controls.set_enabled(sim.phase == Simulation.Phase.RUNNING)
		"settings":
			sim.pause()
			controls.set_enabled(false)
			hud.screen_override = "settings"
		"diagnostics":
			hud.screen_override = "diagnostics"
		"back":
			hud.screen_override = ""
	hud.refresh(true)

func _on_upgrade(id: String) -> void:
	if sim.choose_upgrade(id):
		controls.clear()
		controls.set_enabled(sim.phase == Simulation.Phase.RUNNING)
		hud.refresh(true)

func _on_setting(key: String, value: Variant) -> void:
	var error := settings.set_value(key, value)
	if error != OK:
		push_warning("Could not save preference: %s" % error_string(error))
	_apply_settings()
	# Rebuilding a slider while dragging steals its input; update on the next menu opening.
	if key != "touch_radius":
		hud.refresh(true)

func _apply_settings() -> void:
	view.gore = bool(settings.values.gore)
	view.shake_enabled = bool(settings.values.shake)
	if not view.gore:
		view.corpses.clear()
	sound.muted = bool(settings.values.muted)
	if sound.muted:
		sound.stop_all()
	controls.touch_visible = bool(settings.values.touch) or OS.has_feature("mobile")
	controls.touch_radius = float(settings.values.touch_radius)
