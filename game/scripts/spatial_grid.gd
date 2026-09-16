extends RefCounted
## Rebuilt from live enemies; values are indices valid until the next rebuild.

const CELL: float = 64.0
var buckets: Dictionary = {}

func rebuild(enemies: Array) -> void:
	buckets.clear()
	for index in range(enemies.size()):
		var enemy = enemies[index]
		if enemy.health <= 0.0 or enemy.warning > 0.0:
			continue
		var cell := Vector2i(floori(enemy.position.x / CELL), floori(enemy.position.y / CELL))
		if not buckets.has(cell):
			buckets[cell] = []
		buckets[cell].append(index)

func query(point: Vector2, radius: float) -> Array[int]:
	var found: Array[int] = []
	var low := Vector2i(floori((point.x - radius) / CELL), floori((point.y - radius) / CELL))
	var high := Vector2i(floori((point.x + radius) / CELL), floori((point.y + radius) / CELL))
	for y in range(low.y, high.y + 1):
		for x in range(low.x, high.x + 1):
			var key := Vector2i(x, y)
			if buckets.has(key):
				for index: int in buckets[key]:
					found.append(index)
	return found
