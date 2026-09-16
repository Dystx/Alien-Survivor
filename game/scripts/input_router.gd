extends RefCounted
## Produces intent only. Touch, keyboard and controller share the same simulation.

var enabled: bool = false
var require_neutral: bool = false
var touch_visible: bool = false
var touch_radius: float = 62.0
var move_id: int = -1
var aim_id: int = -1
var move_origin := Vector2.ZERO
var aim_origin := Vector2.ZERO
var move_touch := Vector2.ZERO
var aim_touch := Vector2.ZERO

func _init() -> void:
	_key("move_left", KEY_A)
	_key("move_right", KEY_D)
	_key("move_up", KEY_W)
	_key("move_down", KEY_S)
	_axis("move_left", JOY_AXIS_LEFT_X, -1.0)
	_axis("move_right", JOY_AXIS_LEFT_X, 1.0)
	_axis("move_up", JOY_AXIS_LEFT_Y, -1.0)
	_axis("move_down", JOY_AXIS_LEFT_Y, 1.0)
	_axis("aim_left", JOY_AXIS_RIGHT_X, -1.0)
	_axis("aim_right", JOY_AXIS_RIGHT_X, 1.0)
	_axis("aim_up", JOY_AXIS_RIGHT_Y, -1.0)
	_axis("aim_down", JOY_AXIS_RIGHT_Y, 1.0)
	_key("pause_run", KEY_ESCAPE)
	_key("debug_hud", KEY_F3)
	_key("touch_preview", KEY_F4)
	var pause_button := InputEventJoypadButton.new()
	pause_button.button_index = JOY_BUTTON_START
	InputMap.action_add_event("pause_run", pause_button)

func _action(id: String) -> void:
	if not InputMap.has_action(id):
		InputMap.add_action(id, 0.22)

func _key(id: String, code: Key) -> void:
	_action(id)
	var event := InputEventKey.new()
	event.physical_keycode = code
	InputMap.action_add_event(id, event)

func _axis(id: String, axis: JoyAxis, direction: float) -> void:
	_action(id)
	var event := InputEventJoypadMotion.new()
	event.axis = axis
	event.axis_value = direction
	InputMap.action_add_event(id, event)

func set_enabled(value: bool) -> void:
	if enabled == value:
		return
	enabled = value
	clear()
	require_neutral = value

func clear() -> void:
	move_id = -1
	aim_id = -1
	move_touch = Vector2.ZERO
	aim_touch = Vector2.ZERO

func release_event(event: InputEvent) -> void:
	# Called before GUI handling, so releasing over a button cannot stick a joystick.
	if event is InputEventScreenTouch and (not event.pressed or event.canceled):
		if event.index == move_id:
			move_id = -1
			move_touch = Vector2.ZERO
		if event.index == aim_id:
			aim_id = -1
			aim_touch = Vector2.ZERO

func handle_event(event: InputEvent) -> bool:
	if not enabled:
		return false
	if event is InputEventScreenTouch and event.pressed and not event.canceled:
		touch_visible = true
		if event.position.y < 95:
			return false
		if event.position.x < 480 and move_id == -1:
			move_id = event.index
			move_origin = event.position
			move_touch = Vector2.ZERO
			return true
		if event.position.x >= 480 and aim_id == -1:
			aim_id = event.index
			aim_origin = event.position
			aim_touch = Vector2.ZERO
			return true
	if event is InputEventScreenDrag:
		if event.index == move_id:
			move_touch = ((event.position - move_origin) / touch_radius).limit_length()
			return true
		if event.index == aim_id:
			aim_touch = ((event.position - aim_origin) / touch_radius).limit_length()
			return true
	return false

func sample(mouse_world: Vector2, player: Vector2) -> Dictionary:
	var move := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	var aim := Input.get_vector("aim_left", "aim_right", "aim_up", "aim_down")
	var mouse_down := Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
	if require_neutral:
		if move.length_squared() < 0.01 and aim.length_squared() < 0.01 and not mouse_down:
			require_neutral = false
		else:
			return {"move": Vector2.ZERO, "aim": Vector2.ZERO}
	if not enabled:
		return {"move": Vector2.ZERO, "aim": Vector2.ZERO}
	if move_id >= 0:
		move = move_touch
	if aim_id >= 0:
		aim = aim_touch if aim_touch.length() > 0.2 else Vector2.ZERO
	elif mouse_down:
		aim = player.direction_to(mouse_world)
	return {"move": move.limit_length(), "aim": aim.normalized() if aim.length_squared() > 0.04 else Vector2.ZERO}
