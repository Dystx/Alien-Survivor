extends Resource
## Read-only design values. Per-run upgrades never mutate this Resource.

@export var weapon_id: String = "rifle"
@export var enemy_id: String = "runner"
@export var duration: float = 300.0
@export var player_health: float = 100.0
@export var player_speed: float = 158.0
@export var player_radius: float = 13.0
@export var rifle_damage: float = 25.0
@export var rifle_interval: float = 0.18
@export var rifle_range: float = 450.0
@export var bullet_speed: float = 920.0
@export var enemy_health: float = 35.0
@export var enemy_speed: float = 58.0
@export var enemy_radius: float = 13.0
@export var contact_damage: float = 10.0
@export var hurt_interval: float = 0.65
@export var enemy_limit: int = 150
@export var pickup_limit: int = 300
@export var bullet_limit: int = 96
@export var spawn_warning: float = 0.75
