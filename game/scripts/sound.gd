extends Node
## Small original synthesized effects; no audio library is bundled.

var voices: Array[AudioStreamPlayer] = []
var sounds: Dictionary = {}
var clock: float = 0.0
var last_pickup: float = -1.0
var muted: bool = false
var audio_output_available: bool = true

func _ready() -> void:
	# Dummy/headless playback cannot validate sound and may leave unmixed voices at exit.
	# Still build the PCM resources below to validate their construction.
	audio_output_available = DisplayServer.get_name() != "headless"
	if not audio_output_available:
		print("AUDIO_OUTPUT_NOT_TESTED: headless run; synthesis resources only")
	for index in range(6):
		var voice := AudioStreamPlayer.new()
		voice.volume_db = -16.0
		add_child(voice)
		voices.append(voice)
	sounds.shot = _make_sound(0.07, 130.0, 0.8, 11)
	sounds.hit = _make_sound(0.045, 240.0, 0.65, 22)
	sounds.death = _make_sound(0.16, 60.0, 0.65, 33)
	sounds.pickup = _make_sound(0.08, 780.0, 0.02, 44)
	sounds.level = _make_sound(0.28, 520.0, 0.01, 55)
	sounds.hurt = _make_sound(0.18, 90.0, 0.45, 66)

func _make_sound(duration: float, frequency: float, noise: float, seed_value: int) -> AudioStreamWAV:
	var rate: int = 22050
	var count := int(duration * rate)
	var data := PackedByteArray()
	data.resize(count * 2)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	for index in range(count):
		var t := float(index) / rate
		var envelope := pow(1.0 - float(index) / count, 2.0)
		var tone := sin(TAU * frequency * t * (1.0 - t * 0.6))
		var sample := (tone * (1.0 - noise) + rng.randf_range(-1.0, 1.0) * noise) * envelope
		data.encode_s16(index * 2, int(clampf(sample, -1.0, 1.0) * 22000))
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = rate
	stream.stereo = false
	stream.data = data
	return stream

func consume(dt: float, events: Array[Dictionary]) -> void:
	clock += dt
	if muted or not audio_output_available:
		return
	for event in events:
		var id: String = event.type
		if not sounds.has(id):
			continue
		if id == "pickup":
			if clock - last_pickup < 0.075:
				continue
			last_pickup = clock
		for voice in voices:
			if not voice.playing:
				voice.stream = sounds[id]
				voice.play()
				break

func stop_all() -> void:
	for voice in voices:
		voice.stop()
		voice.stream = null

func _exit_tree() -> void:
	stop_all()
	sounds.clear()
