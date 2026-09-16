extends RefCounted
## Versioned local preferences only. No account or run-save promise.
const DEFAULTS: Dictionary = {"muted": false, "gore": true, "shake": false, "touch": false, "touch_radius": 62.0}
var values: Dictionary = DEFAULTS.duplicate()
var path: String
var recovered_backup: bool = false

func _init(file_path: String = "user://settings_v1.cfg") -> void:
	path = file_path
	load_settings()

func _validated(raw: Dictionary) -> Dictionary:
	var clean := DEFAULTS.duplicate()
	for key: String in DEFAULTS:
		if not raw.has(key):
			continue
		if key == "touch_radius":
			if typeof(raw[key]) in [TYPE_INT, TYPE_FLOAT]:
				var number := float(raw[key])
				if is_finite(number):
					clean[key] = clampf(number, 40.0, 100.0)
		elif typeof(raw[key]) == TYPE_BOOL:
			clean[key] = raw[key]
	return clean

func load_settings() -> void:
	values = DEFAULTS.duplicate()
	recovered_backup = false
	for candidate in [path, path + ".bak"]:
		var config := ConfigFile.new()
		if config.load(candidate) != OK:
			continue
		if config.get_value("meta", "version", 0) != 1:
			continue
		var raw: Dictionary = {}
		for key: String in DEFAULTS:
			raw[key] = config.get_value("settings", key, DEFAULTS[key])
		values = _validated(raw)
		recovered_backup = candidate != path
		return

func set_value(key: String, value: Variant) -> Error:
	if not DEFAULTS.has(key):
		return ERR_INVALID_PARAMETER
	var updated := values.duplicate()
	updated[key] = value
	values = _validated(updated)
	return save()

func save() -> Error:
	var config := ConfigFile.new()
	config.set_value("meta", "version", 1)
	for key: String in values:
		config.set_value("settings", key, values[key])
	var temporary := path + ".tmp"
	var error := config.save(temporary)
	if error != OK:
		return error
	var verify := ConfigFile.new()
	if verify.load(temporary) != OK:
		return ERR_FILE_CORRUPT
	# Never overwrite a known good backup with the corrupt file we recovered from.
	if FileAccess.file_exists(path) and not recovered_backup:
		error = DirAccess.copy_absolute(path, path + ".bak")
		if error != OK:
			return error
	error = DirAccess.rename_absolute(temporary, path)
	if error == OK:
		recovered_backup = false
	return error
