extends SceneTree
const Sim = preload("res://scripts/simulation.gd")
const Firing = preload("res://scripts/firing_presentation.gd")
const Human = preload("res://scripts/human_animation.gd")
const Iso = preload("res://scripts/projection.gd")
var passed: int = 0
var failed: int = 0
func check(ok: bool, label: String) -> void:
	if ok:
		passed += 1
		print("PASS ", label)
	else:
		failed += 1
		print("FAIL ", label)
func _initialize() -> void:
	var h := Human.new()
	var f := Firing.new()
	# Regression: the old launch offset changed slope abruptly at 110 world units.
	# Also check legacy/test shots without mount data: they must stay straight.
	for angle in [0.0, 0.37, 1.57, 2.3, 3.14159, 4.71]:
		h.direction = Human.direction_for(Vector2.from_angle(angle))
		var sim := Sim.new()
		sim.reset()
		sim.spawning_enabled = false
		var geometry := Firing.launch_geometry(h, 1.0/60.0, 0.96)
		var direction := Iso.unproject(Vector2.from_angle(angle)).normalized()
		sim.grid.rebuild(sim.enemies)
		sim._fire(direction, geometry)
		check(sim.bullets.size() == 1, "mounted shot exists angle %.2f" % angle)
		if sim.bullets.is_empty(): continue
		var bullet = sim.bullets[0]
		var origin: Vector2 = bullet.origin
		var v: Vector2 = bullet.velocity
		f.reset()
		f.advance(1.0/60.0,h,true,sim.bullets,sim.balance.rifle_range,0.96,sim.events)
		var muzzle := Iso.project(sim.player) + Firing.muzzle_offset(h,0.96)
		check((Iso.project(origin)+Firing.TRACER_HEIGHT).distance_to(muzzle)<0.001,"physical and drawn origin equal the visible muzzle")
		var axis := Iso.project(v).normalized()
		var all_straight := true
		for travelled in [0.0,3.0,60.0,109.9,110.1,160.0,300.0]:
			bullet.position=origin+v.normalized()*travelled
			bullet.remaining=bullet.path_length-travelled
			var points := f.trace_points(bullet)
			for p in points:
				all_straight=all_straight and absf((p-muzzle).cross(axis))<0.002
			all_straight=all_straight and points[1].distance_to(Iso.project(bullet.position)+Firing.TRACER_HEIGHT)<0.002
		check(all_straight,"whole ray and tail stay collinear through old blend boundary")
		h.direction="w" if h.direction!="w" else "s"
		h.clip="hit"
		var previous := f.trace_points(bullet)
		f.advance(0.016,h,false,sim.bullets,sim.balance.rifle_range,0.96)
		check(f.trace_points(bullet)==previous and bullet.velocity==v,"turning/hit pose cannot pull or re-aim an existing bullet")
		h.reset()
	var sim := Sim.new()
	sim.reset()
	sim.spawning_enabled=false
	sim.finale_enabled=false
	var geometry := Firing.launch_geometry(h,0.016,0.96)
	var point := sim.player+Vector2(180,30)
	sim._fire(sim.player.direction_to(point),geometry,point)
	var bullet=sim.bullets[0]
	check(bullet.velocity.normalized().distance_to(bullet.origin.direction_to(point))<0.0001,"mouse or automatic target is resolved once at launch")
	var velocity: Vector2=bullet.velocity
	var initial: Vector2=bullet.position
	var enemy=sim.add_enemy(point)
	sim.grid.rebuild(sim.enemies)
	enemy.position=sim.player+Vector2(-180,0)
	for i in range(4):
		sim.player += Vector2(-3,3)
		sim.facing=Vector2.from_angle(float(i))
		sim.grid.rebuild(sim.enemies)
		sim._update_bullets(0.016)
	check(bullet.velocity==velocity and absf((bullet.position-initial).cross(velocity.normalized()))<0.002,"moving target and shooter cannot steer in-flight physics")
	check(enemy.health==sim.balance.enemy_health,"target that leaves the line is not magnetically hit")
	var first_id:int=bullet.get_instance_id()
	sim.grid.rebuild(sim.enemies)
	sim.cooldown=0.0
	sim.step(0.016,Vector2.ZERO,Vector2.ZERO,geometry)
	check(bullet.get_instance_id()==first_id and bullet.velocity==velocity,"next automatic shot does not retarget the previous shot")
	# Manual directional aim must remain arbitrary, not snapped to four sprite views.
	sim.reset()
	sim.grid.rebuild(sim.enemies)
	var angle_dir:=Vector2(0.8,0.37).normalized()
	sim._fire(angle_dir,geometry)
	check(sim.bullets[0].velocity.normalized().distance_to(angle_dir)<0.0001,"analog/free directional aim is not quantized")
	# Cover between the body and the calibrated muzzle must prevent teleporting shots.
	sim.reset()
	var offset:Vector2=geometry.offsets[0]
	var barrier:Rect2=Rect2(sim.player+offset*0.5-Vector2(4,4),Vector2(8,8))
	sim.arena.blockers.append(barrier)
	sim.grid.rebuild(sim.enemies)
	sim._fire(Iso.unproject(Vector2.RIGHT).normalized(),geometry)
	check(sim.bullets.is_empty(),"barrel cannot spawn a projectile beyond a wall")
	var contact=false
	for e in sim.events:
		contact=contact or (e.type=="rifle_impact" and bool(e.wall))
	check(contact and sim.shot_count==1,"blocked shot keeps its shot count and exact wall feedback")
	# Fresh arena per test because reset preserves its static collision map.
	sim=Sim.new();sim.reset()
	enemy=sim.add_enemy(sim.player+Vector2(-20,-20))
	enemy.health=sim.rifle_damage()
	sim.grid.rebuild(sim.enemies)
	sim._fire(Iso.unproject(Vector2.RIGHT).normalized(),geometry)
	check(sim.bullets.is_empty() and sim.kills==1,"point-blank enemy inside muzzle segment cannot be skipped")
	check(sim.pickups.size()==1,"point-blank hit produces only one reward")
	# Long-flight collision agrees with the drawn line at the actual edge contact.
	sim=Sim.new();sim.reset()
	point=sim.player+Vector2(160,30)
	enemy=sim.add_enemy(point);enemy.health=1000.0
	sim.grid.rebuild(sim.enemies)
	sim._fire(sim.player.direction_to(point),geometry,point)
	bullet=sim.bullets[0]
	initial=bullet.origin;velocity=bullet.velocity
	for i in range(40):
		if sim.bullets.is_empty():break
		sim._update_bullets(1.0/120.0)
	var exact=false
	for event in sim.events:
		if event.type=="rifle_impact" and not bool(event.wall):
			var hit:Vector2=event.position
			exact=absf((hit-initial).cross(velocity.normalized()))<0.002 and absf(hit.distance_to(point)-(enemy.radius+2.0))<0.01
	check(exact,"impact is on the frozen ray at collision edge, not pulled toward centre")
	check(is_equal_approx(enemy.health,1000.0-sim.rifle_damage()),"damage value unchanged")
	# Zero-time and finite-input guards.
	sim=Sim.new();sim.reset();sim.grid.rebuild(sim.enemies)
	sim._fire(Vector2.ZERO,geometry)
	sim._fire(Vector2.INF,geometry)
	check(sim.bullets.is_empty() and sim.shot_count==0,"invalid shot vectors rejected")
	sim.step(0.0,Vector2.ZERO,Vector2.RIGHT,geometry)
	check(sim.bullets.is_empty(),"pause creates no shot")
	# Socket prediction preserves source animation state and selects actual hit cells.
	h.clip="hit";h.time=0.09;h.hit_remaining=0.07
	var time_before:=h.time
	geometry=Firing.launch_geometry(h,0.016,0.96)
	check(h.time==time_before and h.hit_remaining==0.07,"mount calculation never advances or changes human")
	var expected_h:=Human.new();expected_h.clip="hit";expected_h.time=0.106;expected_h.direction="e"
	check((Iso.project(geometry.offsets[0])+Firing.TRACER_HEIGHT).distance_to(Firing.muzzle_offset(expected_h,0.96))<0.001,"existing hit frame uses its matching muzzle")
	sim=Sim.new();sim.reset();sim.grid.rebuild(sim.enemies)
	sim.events.append({"type":"hurt","position":sim.player})
	sim._fire(Iso.unproject(Vector2.RIGHT).normalized(),geometry)
	expected_h.time=0.0
	check((Iso.project(sim.bullets[0].origin-sim.player)+Firing.TRACER_HEIGHT).distance_to(Firing.muzzle_offset(expected_h,0.96))<0.001,"same-tick contact hit selects first hit pose socket")
	# Show that the old renderer really failed straightness; this is not a vacuous test.
	var offset_old:=Vector2(26.88,-49.92)
	var sample_old:=Iso.project(Vector2(160,0))+offset_old.lerp(Firing.TRACER_HEIGHT,1.0)
	var middle_old:=Iso.project(Vector2(60,0))+offset_old.lerp(Firing.TRACER_HEIGHT,60.0/110.0)
	check(absf((middle_old-offset_old).cross((sample_old-offset_old).normalized()))>1.0,"negative control detects the old visual bend")
	print("STRAIGHT_SHOT_TESTS: %d passed, %d failed" % [passed,failed])
	quit(0 if failed==0 else 1)
