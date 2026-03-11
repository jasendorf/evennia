# DorfinMUD Mob System

Complete reference for the mob (monster/hostile NPC) system: typeclasses,
spawning, respawning, movement, combat integration, and admin commands.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      AwtownMob                              │
│                 typeclasses/mobs.py                          │
│  Typeclass with HP, stats, loot, damage, XP, death logic    │
└──────────┬──────────────────────────────────┬───────────────┘
           │                                  │
           ▼                                  ▼
┌─────────────────────┐          ┌──────────────────────────┐
│  MobRespawnScript    │          │  MobMovementScript       │
│  (on the ROOM)       │          │  (on the MOB)            │
│  mob_spawner.py      │          │  mob_movement.py         │
│                      │          │                          │
│  Tracks mob by dbref │          │  Wander / Patrol / Chase │
│  Respawns at home    │          │  Skips while in combat   │
│  room when mob dies  │          │  Survives server reload  │
└──────────────────────┘          └──────────────────────────┘
           │                                  │
           └──────────┬───────────────────────┘
                      ▼
           ┌─────────────────────┐
           │   CombatHandler     │
           │   (on the ROOM)     │
           │   combat_handler.py │
           │                     │
           │   Tick-based combat │
           │   Wimpy auto-flee   │
           │   Chase on flee     │
           └─────────────────────┘
```

Key principle: the **respawn script** lives on the room, the **movement
script** lives on the mob. They are independent. A wandering mob can die
three rooms away from home and the respawn script will detect its death
and spawn a fresh one at the home room with the same movement config.

## Files

| File | Purpose |
|------|---------|
| `typeclasses/mobs.py` | `AwtownMob` typeclass — HP, stats, loot, death |
| `contrib_dorfin/mob_spawner.py` | `spawn_mob()`, `spawn_and_track()`, `MobRespawnScript` |
| `contrib_dorfin/mob_movement.py` | `MobMovementScript`, `trigger_chase()`, `attach_movement_script()` |
| `contrib_dorfin/combat_handler.py` | `CombatHandler` — tick combat, wimpy, flee + chase hook |
| `contrib_dorfin/combat_rules.py` | `resolve_attack()`, `check_flee()`, `roll_initiative()` |
| `commands/command_combat.py` | Player commands: `kill`, `flee`, `consider`, `wimpy`, `rest`, `score`, `loot` |
| `commands/command_admin_combat.py` | Admin commands: `@spawnmob`, `@trainingroom`, `@testarena`, `@stopcombat`, `@combatdebug`, `@fixcombat` |

## Mob Attributes (db.*)

### Combat

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `is_mob` | bool | True | Identifies this as a killable mob |
| `hp` | int | 50 | Current hit points |
| `hp_max` | int | 50 | Maximum hit points |
| `level` | int | 1 | Mob level (affects XP, consider, rescue) |
| `stats` | dict | DEFAULT_MOB_STATS | The 10 base stats (str/dex/agi/con/end/int/wis/per/cha/lck) |
| `xp_value` | int | 25 | Total XP awarded on kill (split among attackers) |
| `damage_dice` | str | "1d4" | Natural attack dice (used when unarmed) |
| `damage_bonus` | int | 0 | Flat bonus added to damage rolls |
| `armor_bonus` | int | 0 | Flat defense bonus |
| `loot_table` | list | [] | List of loot dicts (see Loot Table below) |

### Behavior

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `aggro` | bool | False | Attack players on sight (future use) |
| `wimpy` | int | 0 | Auto-flee when HP drops to this value. 0 = fight to the death |

### Movement

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `move_mode` | str | "stationary" | Movement behavior: "stationary", "wander", or "patrol" |
| `move_interval` | int | 30 | Seconds between movement ticks |
| `wander_chance` | float | 0.5 | Probability of moving each wander tick (0.0–1.0) |
| `patrol_route` | list | [] | Ordered list of room dbrefs to patrol through |
| `chase` | bool | False | Follow fleeing players through exits |
| `chase_range` | int | 3 | Max rooms to chase before giving up and returning home |
| `home_room` | str | None | Dbref of spawn room (set automatically by `spawn_mob()`) |

## Spawning Mobs

### Simple spawn (no respawn)

```python
from contrib_dorfin.mob_spawner import spawn_mob

goblin = spawn_mob(room, name="a goblin", hp=30, level=2,
                   damage_dice="1d6", xp_value=40)
```

### Spawn with auto-respawn

```python
from contrib_dorfin.mob_spawner import spawn_and_track

goblin, script = spawn_and_track(room, name="a goblin", hp=30,
                                  level=2, damage_dice="1d6",
                                  xp_value=40, respawn_delay=60)
```

### Spawn with movement

```python
# Wandering mob
rat, script = spawn_and_track(room, name="a rat", hp=15,
                               move_mode="wander", move_interval=20,
                               wander_chance=0.6)

# Patrolling mob
guard, script = spawn_and_track(room, name="a guard", hp=40,
                                 move_mode="patrol", move_interval=15,
                                 patrol_route=[room1.dbref, room2.dbref,
                                               room3.dbref])

# Chase-enabled mob
wolf, script = spawn_and_track(room, name="a wolf", hp=30,
                                chase=True, chase_range=3)

# Cowardly mob (flees at low HP)
goblin, script = spawn_and_track(room, name="a cowardly goblin",
                                  hp=40, wimpy=15, move_mode="wander",
                                  chase=True)
```

### spawn_mob() parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `room` | Room | required | Room to spawn in |
| `name` | str | "a mob" | Mob display name |
| `stats` | dict | DEFAULT_MOB_STATS | Base stats dict |
| `hp` | int | 20 | Hit points (both current and max) |
| `level` | int | 1 | Mob level |
| `xp_value` | int | 10 | XP on kill |
| `damage_dice` | str | "1d4" | Natural attack dice |
| `armor_bonus` | int | 0 | Defense bonus |
| `desc` | str | auto | Description text |
| `loot_table` | list | [] | Loot drops |
| `wimpy` | int | 0 | Auto-flee threshold |
| `move_mode` | str | "stationary" | "stationary", "wander", or "patrol" |
| `move_interval` | int | 30 | Movement tick interval |
| `wander_chance` | float | 0.5 | Wander probability per tick |
| `patrol_route` | list | None | Room dbrefs for patrol |
| `chase` | bool | False | Chase fleeing players |
| `chase_range` | int | 3 | Max chase distance |

## Movement Behaviors

### Wander

The mob picks a random valid exit each tick and moves through it. "Valid"
means the exit is open and the destination is not a safe room.

- Controlled by `wander_chance` — each tick, a random roll determines
  whether the mob actually moves (e.g., 0.5 = 50% chance per tick).
- Mob will never enter a room with `db.is_safe = True`.
- Movement pauses while mob is in combat (`db.in_combat`).

### Patrol

The mob walks a fixed route of rooms in order, looping back to the start.
Each tick it advances one step.

- `patrol_route` is a list of room dbrefs: `["#123", "#124", "#125"]`
- If a room in the route no longer exists, it's skipped.
- If the mob is displaced (e.g., chased away), it teleports to the next
  patrol point on the next tick.

### Chase

When a player flees combat (via `flee` command or wimpy auto-flee), mobs
with `db.chase = True` follow through the same exit.

**Chase timeline:**

1. **t+0s** — Player flees. Mob announces: *"snarls and prepares to give chase!"*
2. **t+3s** — Mob moves through the same exit the player used.
   *"charges after its prey!"*
3. **t+5s** — If target is in the same room, mob re-engages combat.
   *"catches up and attacks!"*

**Chase limits:**
- `chase_range` controls how many rooms the mob will follow (default 3).
- Chase aborts if: target enters a safe room, mob dies, mob enters other
  combat, or target moves to a different room before the mob arrives.
- When chase ends (target lost or range exceeded), mob teleports home.

**What triggers chase:**
- `CmdFlee` in `command_combat.py`
- Wimpy auto-flee in `combat_handler.py` (player only — mob wimpy flee
  does not trigger chase on other mobs)

### Stationary

Default mode. Mob stays in its spawn room. No movement script is created.
Can still have `chase=True` to follow fleeing players.

## Wimpy (Auto-Flee)

Both players and mobs can have a `wimpy` threshold.

- **Players**: set via `wimpy <hp>` command.
- **Mobs**: set via `db.wimpy` attribute (0 = fight to the death).

When a combatant's HP drops to or below their wimpy value during a combat
tick, they automatically attempt to flee. The flee check uses the same
`check_flee()` roll as the manual `flee` command.

**Mob-specific behavior:**
- Mob flee messages are third-person room messages:
  *"a goblin whimpers and flees!"* (success) or
  *"a goblin tries to flee but can't escape!"* (failure)
- When a mob flees via wimpy, it does NOT trigger chase on other mobs.
- When a player flees via wimpy, chase IS triggered on mob opponents.

## Respawn System

`MobRespawnScript` lives on the mob's **home room** (not on the mob).
It tracks the mob by dbref, checking each tick whether the tracked mob
still exists in the database.

- When the mob dies (object deleted), the respawn script detects it on
  the next tick and calls `spawn_mob()` with the stored `mob_kwargs`.
- Since `mob_kwargs` includes movement config, the respawned mob gets
  a fresh `MobMovementScript` with the same settings.
- The respawn script does NOT care where the mob died — it always
  respawns at the home room.

## Loot Table

Each entry in `db.loot_table` is a dict:

```python
{
    "prototype": "rusty_dagger",   # Prototype key (tried first)
    "chance": 0.3,                 # Drop probability (0.0–1.0)
    "name": "a rusty dagger",      # Fallback name if prototype fails
    "desc": "A notched blade.",     # Fallback description
    "value": 5,                     # Fallback copper value
}
```

On death, each entry is rolled independently. Drops go into the corpse.

## Death Flow

1. `take_damage()` reduces HP to 0
2. Combat handler calls `at_defeat()`
3. Combat handler awards XP to player combatants (split evenly)
4. `at_defeat()` creates a Corpse object with rolled loot
5. Mob object is deleted
6. Respawn script detects deletion on next tick → spawns fresh mob

## Admin Commands

### @spawnmob

Spawn a mob with full parameter control:

```
@spawnmob a goblin hp=30 level=2 damage=1d6 xp=40
@spawnmob a wandering rat /wander hp=15 wander_chance=0.6
@spawnmob a fierce wolf /chase hp=30 chase_range=3
@spawnmob a cowardly goblin hp=40 wimpy=15 /wander /chase
@spawnmob a guard /patrol hp=50 level=3 armor=3 respawn=60
```

**Switches:** `/wander`, `/patrol`, `/chase`

**Key=value params:** `hp`, `level`, `xp`, `damage`, `armor`, `wimpy`,
`move_interval`, `wander_chance`, `chase_range`, `respawn`

### @testarena

Creates a 4-room test area with pre-configured mobs:

```
[Arena North] --- [Arena East]
      |                |
[Arena West]  --- [Arena South]
```

- **Arena North**: wandering rat (wanders every ~20s)
- **Arena East**: patrolling guard (patrols all 4 rooms every 15s)
- **Arena South**: fierce wolf (chases 3 rooms on flee)
- **Arena West**: empty observation room

Links to the Training Yard if it exists. Safe to run repeatedly.

### @trainingroom

Creates a single-room training area with a practice dummy.

### @stopcombat

Force-stop all combat in the current room.

### @combatdebug

Show detailed combat handler, respawn script, and mob state.

### @fixcombat

Global cleanup: destroy zombie CombatHandlers, clear stale combat flags.

## Script Lifecycle

### Server reload

Both `MobMovementScript` and `MobRespawnScript` are persistent and
survive `@reload`. They re-register their tickers on `at_init()`.

### Mob death

1. Mob is deleted by `at_defeat()`
2. `MobMovementScript` is deleted with the mob (it's attached to the mob)
3. `MobRespawnScript` (on the room) detects the mob is gone
4. Respawn script calls `spawn_mob()` → creates new mob + new movement script

### Chase during delayed callbacks

Chase uses `evennia.utils.delay()` for timing. If a server reload happens
during a chase delay, the non-persistent callbacks are lost and the mob
stays where it is. The movement script's `_handle_chase_return()` will
clean up on the next tick (return home or re-engage).

## Design Decisions

- **Movement script on mob, respawn script on room**: Keeps concerns
  separate. Movement dies with the mob; respawn outlives it.
- **Chase uses delays, not script ticks**: Chase needs sub-second timing
  (3s move, 2s engage) that doesn't align with the movement script's
  tick interval. Delays give precise control.
- **Dbrefs in delayed callbacks**: Chase callbacks store dbrefs (strings)
  instead of object references, then re-resolve them. This avoids stale
  object references if the mob or target is deleted during the delay.
- **Mobs don't chase mobs**: When a mob flees via wimpy, it does not
  trigger chase on other mobs. Only player flee triggers chase.
- **Safe room boundary**: Mobs never enter safe rooms, whether wandering,
  patrolling, or chasing. If a player flees into a safe room, the chase
  aborts and the mob returns home.
