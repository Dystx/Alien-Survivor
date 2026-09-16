extends RefCounted
## Shared trimmed-atlas cache. Candidate art is labelled, never auto-approved.
const ROOT := "res://assets/motion_review/"
const DIRECTIONS: Array[String] = ["e", "s", "w", "n"]
var families: Dictionary = {}
var missing: Array[String] = []

func _init() -> void:
	var index: Variant = JSON.parse_string(FileAccess.get_file_as_string(ROOT + "index.json"))
	if not index is Dictionary or not index.has("families"):
		push_error("Missing motion review index")
		missing.append(ROOT + "index.json")
		return
	for kind: String in index.families:
		var path: String = ROOT + kind + "/animations.json"
		var meta: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
		var pages: Array[Texture2D] = []
		for p: Dictionary in meta.pages:
			var tex := load(ROOT + kind + "/" + String(p.file)) as Texture2D
			if tex == null:
				missing.append(String(p.file))
			pages.append(tex)
		for clip: String in meta.clips:
			for direction: String in meta.clips[clip].directions:
				for f: Dictionary in meta.clips[clip].directions[direction]:
					var texture := AtlasTexture.new()
					texture.atlas = pages[int(f.page)]
					texture.region = Rect2(float(f.rect[0]), float(f.rect[1]), float(f.rect[2]), float(f.rect[3]))
					texture.filter_clip = true
					f["texture"] = texture
		families[kind] = meta

static func direction_key(direction: Vector2) -> String:
	return DIRECTIONS[posmod(roundi(direction.angle() / (PI * 0.5)), 4)]

func canonical(kind: String) -> String:
	return "brood_warden" if kind == "boss" else kind

func has_clip(kind: String, clip: String) -> bool:
	kind = canonical(kind)
	return families.has(kind) and families[kind].clips.has(clip)

func duration(kind: String, clip: String) -> float:
	var c: Dictionary = families[canonical(kind)].clips[clip]
	return float(c.directions.e.size()) / float(c.fps)

func sample(kind: String, clip: String, direction: Vector2, seconds: float, progress: float = -1.0) -> Dictionary:
	kind = canonical(kind)
	if not has_clip(kind, clip):
		push_error("Missing motion clip %s/%s" % [kind, clip])
		return {}
	var c: Dictionary = families[kind].clips[clip]
	var key := direction_key(direction)
	var seq: Array = c.directions[key]
	var frame: int
	if progress >= 0.0:
		frame = clampi(int(clampf(progress, 0.0, 1.0) * float(seq.size())), 0, seq.size() - 1)
	elif bool(c.loop):
		frame = posmod(floori(maxf(seconds, 0.0) * float(c.fps)), seq.size())
	else:
		frame = clampi(floori(maxf(seconds, 0.0) * float(c.fps)), 0, seq.size() - 1)
	return seq[frame]
