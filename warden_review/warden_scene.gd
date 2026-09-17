extends SceneTree
var scene
var review
var ticks: int = 0
var frozen: float = 0.0
func _initialize() -> void:
	setup.call_deferred()
func setup() -> void:
	scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	scene.sound.muted = true
func require(ok: bool, label: String) -> void:
	if not ok:
		push_error(label)
		quit(1)
func _process(_dt: float) -> bool:
	ticks += 1
	if ticks == 5:
		scene._on_action("boss_test")
		scene.sim.spawning_enabled = false
		scene.sim.health = 10000.0
		scene.sim.boss.health = 10000.0
		scene.sim.boss.max_health = 10000.0
		scene.sim.boss.warning = 0.0
		scene.sim.boss.skill_cooldown = 999.0
	if ticks == 12:
		scene.sim._arm_attack(scene.sim.boss,"fan",Vector2.LEFT,0.4)
	if ticks == 20:
		require(scene.view.warden.clip == "acid_attack", "Acid warning art missing")
		scene._on_action("pause")
		frozen = scene.view.warden.age
	if ticks == 30:
		require(scene.view.warden.age == frozen, "Pause advanced boss pose")
		scene._on_action("resume")
	if ticks == 60:
		var boss = scene.sim.boss
		boss.recovery = 0.0
		scene.sim._arm_attack(boss,"charge",Vector2.DOWN,0.25)
	if ticks == 80:
		require(scene.view.warden.clip == "charge", "Active dash must display charge, not recovery")
	if ticks == 108:
		var boss = scene.sim.boss
		boss.action_timer = 0.0
		boss.recovery = 0.0
		scene.sim._arm_attack(boss,"pulse",Vector2.LEFT,0.3)
		boss.health = boss.max_health * 0.4
	if ticks == 115:
		require(scene.view.warden.phase_seen and scene.view.warden.clip == "pulse_attack", "Enrage pose hid a live warning")
	if ticks == 150:
		scene.sim.damage_enemy(scene.sim.boss,100000.0)
	if ticks == 155:
		require(scene.sim.result == "BROOD WARDEN ELIMINATED", "Boss death must settle victory immediately in simulation")
		require(scene.view.warden.dead and scene.hud.waiting_for_death, "Victory panel must wait for cosmetic fall")
		require(not scene.view.human.dead, "Boss fall killed the living human presentation")
		frozen = scene.sim.elapsed
	if ticks == 240:
		require(not scene.view.warden.waiting_for_death() and not scene.hud.waiting_for_death and scene.hud.overlay.visible, "Victory panel did not follow completed fall")
		require(scene.sim.elapsed == frozen and not scene.view.human.dead, "Result animation advanced gameplay or killed human")
	if ticks == 242:
		# Exercise deferred focus on controls abandoned by a rapid overlay rebuild.
		scene.hud.refresh(true)
		scene.hud.refresh(true)
	if ticks == 250:
		scene._on_action("warden_review")
		scene = null
	if ticks == 260:
		review = current_scene
		require(review.CLIPS.size() == 10, "All boss clips must be reviewable")
		review.play_clip("phase_transition")
	if ticks == 280:
		review._action("Pause")
		frozen = review.clock
	if ticks == 290:
		require(review.clock == frozen, "Viewer pause failed")
		review._action("0.5x")
		review._action("View")
		require(review.focus_direction == 0, "Native single view failed")
		review.play_clip("death")
		review._scrub(9)
		require(review.paused and is_equal_approx(review.clock,1.125), "Frame scrub failed")
	if ticks == 315: review._action("Return")
	if ticks == 325:
		scene = current_scene
		scene._on_action("boss_test")
		scene.sim.spawning_enabled = false
	if ticks == 330:
		scene.sim.health = 0.0
		scene.sim.damage_enemy(scene.sim.boss,100000.0)
	if ticks == 335:
		require(scene.sim.result == "CONTAINMENT LOST" and scene.view.human.dead and scene.view.warden.dead, "Simultaneous death must remain defeat")
	if ticks == 425:
		scene._on_action("start")
		require(not scene.view.warden.active and not scene.view.warden.dead and not scene.view.human.dead and not scene.hud.waiting_for_death, "Restart retained boss/player/results state")
		print("WARDEN_SCENE_PASS")
		quit(0)
	return false
