extends Control
## Actual new sprites, not a gameplay or artwork-approval screen.
const DIRECTIONS: Array[String] = ["e","se","s","sw","w","nw","n","ne"]
const EXPECTED := {"ready":4, "walk":8, "fire":4}
const PIVOT := Vector2(64,110)
const CELL := Vector2(128,128)
var atlas: Texture2D
var sequences: Dictionary = {}
var clips: Dictionary = {}
var clip: String = "ready"
var direction: String = "e"
var clock: float = 0.0
var paused: bool = false
var half_speed: bool = false
var markers: bool = false
var bright: bool = false
var loaded: bool = false
var frame_count: int = 0
var status: Label
var slider: HSlider

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_build_ui()
	loaded = _load_art()
	if loaded:
		play_clip("ready")
	queue_redraw()

func _load_art() -> bool:
	atlas = load("res://runtime/atlas.png") as Texture2D
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://runtime/index.json"))
	if atlas == null or not parsed is Dictionary:
		return false
	var data: Dictionary = parsed
	if data.get("asset_id") != "player_rework_v2" or data.get("status") != "review":
		return false
	clips = data.get("clips", {})
	for name: String in EXPECTED:
		if not clips.has(name) or int(clips[name].frames) != int(EXPECTED[name]):
			return false
		for d: String in DIRECTIONS:
			var items: Array = []
			items.resize(int(EXPECTED[name]))
			sequences[name+"_"+d] = items
	for item: Dictionary in data.get("frames", []):
		var key: String = String(item.clip) + "_" + String(item.direction)
		var index: int = int(item.frame)
		if not sequences.has(key) or index < 0 or index >= sequences[key].size() or sequences[key][index] != null:
			return false
		var r: Array = item.region
		if r.size() != 4:
			return false
		var rect := Rect2(float(r[0]),float(r[1]),float(r[2]),float(r[3]))
		if rect.size != CELL or not Rect2(Vector2.ZERO,atlas.get_size()).encloses(rect):
			return false
		sequences[key][index] = item
		frame_count += 1
	for items: Array in sequences.values():
		if items.has(null):
			return false
	return frame_count == 128

func _build_ui() -> void:
	_label("PLAYER REWORK v2",Vector2(24,18),30)
	_label("SHOULDER-MOUNTED RIFLE  /  EIGHT MODELED BODY VIEWS  /  FIRST MOTION DRAFT",Vector2(25,62),15)
	_label("Native-size sprites",Vector2(24,106),14)
	_label("Selected view - 3x",Vector2(914,106),14)
	for i in range(8):
		var button := Button.new()
		button.text = DIRECTIONS[i].to_upper()
		button.position = Vector2(32 + (i%4)*214,156+(i/4)*228)
		button.size = Vector2(50,25)
		button.pressed.connect(_select.bind(DIRECTIONS[i]))
		add_child(button)
	var bar := HBoxContainer.new()
	bar.position = Vector2(24,604)
	bar.add_theme_constant_override("separation",8)
	add_child(bar)
	for value: String in ["Ready","Walk","Fire","Pause","Half speed","Sockets","Background","Replay"]:
		var button := Button.new()
		button.text = value
		button.custom_minimum_size = Vector2(112,38)
		button.pressed.connect(_action.bind(value))
		bar.add_child(button)
	slider = HSlider.new()
	slider.position = Vector2(1010,602)
	slider.size = Vector2(235,40)
	slider.step = 1.0
	slider.value_changed.connect(_scrub)
	add_child(slider)
	status = _label("",Vector2(24,660),15)
	_label("Review only. Hit, death, strafing and gameplay integration are not included. Original game stays unchanged.",Vector2(24,692),13)

func _label(text: String, point: Vector2, size: int) -> Label:
	var label := Label.new()
	label.text = text
	label.position = point
	label.add_theme_font_size_override("font_size",size)
	label.add_theme_color_override("font_color",Color("d8ddd1"))
	add_child(label)
	return label

func _select(value: String) -> void:
	direction = value
	queue_redraw()

func play_clip(value: String) -> void:
	if not loaded or not clips.has(value):
		return
	clip = value
	clock = 0.0
	paused = false
	slider.max_value = float(int(EXPECTED[clip])-1)
	_refresh()

func frame_index() -> int:
	if not loaded:
		return 0
	var index := floori(clock * float(clips[clip].fps) + 0.00001)
	return posmod(index,int(EXPECTED[clip])) if bool(clips[clip].loop) else mini(index,int(EXPECTED[clip])-1)

func advance(dt: float) -> void:
	if not loaded or paused or dt <= 0.0:
		return
	var duration: float = float(EXPECTED[clip])/float(clips[clip].fps)
	clock += dt*(0.5 if half_speed else 1.0)
	clock = fmod(clock,duration) if bool(clips[clip].loop) else minf(clock,duration)
	_refresh()

func _process(dt: float) -> void:
	advance(dt)

func _refresh() -> void:
	slider.set_value_no_signal(frame_index())
	status.text = "%s  /  FRAME %d OF %d  /  %s  /  %s    |    SOCKETS: muzzle red, stock/shoulder amber, hands teal" % [clip.to_upper(),frame_index()+1,int(EXPECTED[clip]),"PAUSED" if paused else "PLAYING","0.5x" if half_speed else "1x"]
	queue_redraw()

func _scrub(value: float) -> void:
	if not loaded:
		return
	paused = true
	clock = value/float(clips[clip].fps)
	_refresh()

func _action(value: String) -> void:
	if not loaded:
		return
	match value:
		"Ready","Walk","Fire": play_clip(value.to_lower())
		"Pause": paused = not paused
		"Half speed": half_speed = not half_speed
		"Sockets": markers = not markers
		"Background": bright = not bright
		"Replay": play_clip(clip)
	_refresh()

func _draw_actor(d: String, ground: Vector2, scale_value: float) -> void:
	var item: Dictionary = sequences[clip+"_"+d][frame_index()]
	var r: Array = item.region
	var rect := Rect2(float(r[0]),float(r[1]),float(r[2]),float(r[3]))
	draw_line(ground-Vector2(24,0)*scale_value,ground+Vector2(24,0)*scale_value,Color("526054"),1.0)
	draw_texture_rect_region(atlas,Rect2(ground-PIVOT*scale_value,CELL*scale_value),rect)
	if markers:
		for name: String in ["muzzle","stock","trigger_grip","support_grip"]:
			var p: Array = item.sockets[name]
			var color := Color("ea8c67") if name=="muzzle" else (Color("d2ac70") if name=="stock" else Color("78b8ad"))
			draw_circle(ground+(Vector2(float(p[0]),float(p[1]))-PIVOT)*scale_value,2.0,color)

func _draw() -> void:
	draw_rect(Rect2(0,0,1280,720),Color("172124"))
	if not loaded:
		return
	for i in range(8):
		var panel := Rect2(20+(i%4)*214,143+(i/4)*228,205,212)
		draw_rect(panel,Color("b8baa8") if bright else Color("242e30"))
		_draw_actor(DIRECTIONS[i],panel.position+Vector2(107,173),1.0)
	draw_rect(Rect2(893,143,363,440),Color("b8baa8") if bright else Color("242e30"))
	_draw_actor(direction,Vector2(1070,522),3.0)
