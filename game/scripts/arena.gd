extends RefCounted
## Ground-plane collision and one shared coarse navigation field.

const SIZE := Vector2(1792, 1152)
const CELL: float = 64.0
const COLS: int = 28
const ROWS: int = 18
const INFINITY_COST: int = 99999
const STEPS := [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]

var bounds := Rect2(Vector2(40, 40), SIZE - Vector2(80, 80))
var blockers: Array[Rect2] = [
	Rect2(384, 256, 176, 96), Rect2(1184, 256, 160, 96),
	Rect2(384, 800, 176, 96), Rect2(1184, 800, 160, 96),
	Rect2(816, 208, 160, 64), Rect2(816, 912, 160, 64)
]
var costs := PackedInt32Array()
var blocked := PackedByteArray()
var goal_cell := Vector2i(-1, -1)

func _init() -> void:
	costs.resize(COLS * ROWS)
	blocked.resize(COLS * ROWS)
	for y in range(ROWS):
		for x in range(COLS):
			blocked[y * COLS + x] = 0 if is_clear(cell_center(Vector2i(x, y)), 22.0) else 1

func cell_of(point: Vector2) -> Vector2i:
	return Vector2i(clampi(int(point.x / CELL), 0, COLS - 1), clampi(int(point.y / CELL), 0, ROWS - 1))

func cell_center(cell: Vector2i) -> Vector2:
	return (Vector2(cell) + Vector2(0.5, 0.5)) * CELL

func valid_cell(cell: Vector2i) -> bool:
	return cell.x >= 0 and cell.x < COLS and cell.y >= 0 and cell.y < ROWS

func is_clear(point: Vector2, radius: float) -> bool:
	if not bounds.grow(-radius).has_point(point):
		return false
	for rect in blockers:
		if rect.grow(radius).has_point(point):
			return false
	return true

func move_body(origin: Vector2, delta: Vector2, radius: float) -> Vector2:
	# Axis-separated motion slides along solids. Fixed, short steps prevent tunneling.
	var p := origin
	var inner := bounds.grow(-radius)
	p.x = clampf(p.x + delta.x, inner.position.x, inner.end.x - 0.01)
	for rect in blockers:
		var box := rect.grow(radius)
		if box.has_point(p):
			p.x = box.position.x - 0.01 if delta.x > 0.0 else box.end.x + 0.01
	p.y = clampf(p.y + delta.y, inner.position.y, inner.end.y - 0.01)
	for rect in blockers:
		var box := rect.grow(radius)
		if box.has_point(p):
			p.y = box.position.y - 0.01 if delta.y > 0.0 else box.end.y + 0.01
	return p.clamp(inner.position + Vector2(0.01, 0.01), inner.end - Vector2(0.01, 0.01))

static func box_hit_t(a: Vector2, b: Vector2, rect: Rect2) -> float:
	# Slab intersection, returning first segment fraction or >1 for no collision.
	var direction := b - a
	var near_t: float = 0.0
	var far_t: float = 1.0
	for axis in range(2):
		if absf(direction[axis]) < 0.00001:
			if a[axis] < rect.position[axis] or a[axis] > rect.end[axis]:
				return 2.0
		else:
			var t1: float = (rect.position[axis] - a[axis]) / direction[axis]
			var t2: float = (rect.end[axis] - a[axis]) / direction[axis]
			near_t = maxf(near_t, minf(t1, t2))
			far_t = minf(far_t, maxf(t1, t2))
			if near_t > far_t:
				return 2.0
	return near_t

func wall_hit_t(a: Vector2, b: Vector2, radius: float = 0.0) -> float:
	var result: float = 2.0
	for rect in blockers:
		result = minf(result, box_hit_t(a, b, rect.grow(radius)))
	return result

func update_field(player: Vector2) -> void:
	var goal := cell_of(player)
	if goal == goal_cell:
		return
	goal_cell = goal
	costs.fill(INFINITY_COST)
	var queue: Array[Vector2i] = [goal]
	costs[goal.y * COLS + goal.x] = 0
	var head: int = 0
	while head < queue.size():
		var current: Vector2i = queue[head]
		head += 1
		for offset: Vector2i in STEPS:
			var next: Vector2i = current + offset
			if not valid_cell(next):
				continue
			var index: int = next.y * COLS + next.x
			if blocked[index] != 0 or costs[index] != INFINITY_COST:
				continue
			costs[index] = costs[current.y * COLS + current.x] + 1
			queue.append(next)

func direction_to(point: Vector2, target: Vector2, radius: float) -> Vector2:
	if wall_hit_t(point, target, radius + 1.0) > 1.0:
		return point.direction_to(target)
	var cell := cell_of(point)
	var best := cell
	var best_cost: int = costs[cell.y * COLS + cell.x]
	for offset: Vector2i in STEPS:
		var next: Vector2i = cell + offset
		if valid_cell(next):
			var cost: int = costs[next.y * COLS + next.x]
			if cost < best_cost:
				best = next
				best_cost = cost
	if best == cell and best_cost == INFINITY_COST:
		return Vector2.ZERO
	return point.direction_to(cell_center(best))
