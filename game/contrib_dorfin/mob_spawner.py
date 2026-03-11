"""
DorfinMUD Mob Spawner & Respawn System
=======================================

Core infrastructure for spawning mobs, tracking them by dbref, and
respawning them when they die. Used by admin commands, batch scripts,
quest systems, and zone builders.

Spawn-Point Model
-----------------

A MobRespawnScript is attached to a mob's HOME ROOM. It tracks the
mob by dbref, not by room contents. This means:

  - Stationary mobs work (tracked mob is in the home room).
  - Wandering mobs work (tracked mob may be several rooms away).
  - Chasing mobs work (tracked mob may die far from home).

When the tracked mob is deleted (on death), the respawn script
detects it and spawns a fresh one at the home room.

Usage
-----

Simple spawn (no respawn):

    from contrib_dorfin.mob_spawner import spawn_mob
    goblin = spawn_mob(room, name="a goblin", hp=30, level=2,
                       damage_dice="1d6", xp_value=40)

Spawn with auto-respawn:

    from contrib_dorfin.mob_spawner import spawn_and_track
    goblin, script = spawn_and_track(room, name="a goblin", hp=30,
                                      level=2, damage_dice="1d6",
                                      xp_value=40, respawn_delay=60)

Just ensure a respawn script (mob already exists):

    from contrib_dorfin.mob_spawner import ensure_respawn_script
    script = ensure_respawn_script(room, mob_name="a goblin",
                                   mob_dbref=goblin.dbref)

Combat utility:

    from contrib_dorfin.mob_spawner import is_combat_active
    if not is_combat_active(room):
        # safe to spawn
"""

from evennia import create_object, DefaultScript
from evennia.utils.logger import log_info


# ---------------------------------------------------------------------------
# Combat state utilities
# ---------------------------------------------------------------------------

def cleanup_combat_zombies(room):
    """
    Find and delete any CombatHandler scripts on a room that are
    inactive (zombies). Clears stale in_combat flags on their
    combatants.

    Args:
        room: The room to clean.

    Returns:
        int: Number of zombie handlers removed.
    """
    handlers = room.scripts.get("CombatHandler")
    if not handlers:
        return 0

    removed = 0
    for h in list(handlers):
        if not h.is_active:
            for dbref in list(h.db.combatants or []):
                try:
                    from evennia import search_object
                    results = search_object(dbref)
                    if results:
                        results[0].db.in_combat = False
                        results[0].db.combat_target = None
                except Exception:
                    pass
            h.delete()
            removed += 1

    return removed


def is_combat_active(room):
    """
    Return True only if there is a genuinely active CombatHandler
    on this room. Cleans up zombies as a side effect.

    Args:
        room: The room to check.

    Returns:
        bool: True if active combat is in progress.
    """
    cleanup_combat_zombies(room)
    handlers = room.scripts.get("CombatHandler")
    if not handlers:
        return False
    return any(h.is_active for h in handlers)


# ---------------------------------------------------------------------------
# Mob spawning
# ---------------------------------------------------------------------------

DEFAULT_MOB_STATS = {
    "str": 10, "dex": 10, "agi": 10, "con": 10, "end": 10,
    "int": 6, "wis": 6, "per": 10, "cha": 4, "lck": 8,
}


def spawn_mob(room, name="a mob", stats=None, hp=20, level=1,
              xp_value=10, damage_dice="1d4", armor_bonus=0, desc=None,
              loot_table=None, wimpy=0, move_mode="stationary",
              move_interval=30, wander_chance=0.5, patrol_route=None,
              chase=False, chase_range=3):
    """
    Create a mob in a room.

    This is the low-level spawn function. For mobs that should respawn
    after death, use spawn_and_track() instead.

    Args:
        room: Room to spawn in.
        name (str): Mob name.
        stats (dict): The 10 base stats. Defaults to DEFAULT_MOB_STATS.
        hp (int): Hit points (current and max).
        level (int): Mob level.
        xp_value (int): XP awarded on kill.
        damage_dice (str): Natural attack dice (e.g. "1d6").
        armor_bonus (int): Flat defense bonus.
        desc (str): Description. Auto-generated if None.
        loot_table (list): List of loot dicts. Empty list if None.
        move_mode (str): "wander", "patrol", or "stationary".
        move_interval (int): Seconds between movement ticks.
        wander_chance (float): Chance to move each wander tick (0.0-1.0).
        patrol_route (list): List of room dbrefs for patrol path.
        chase (bool): Whether this mob chases fleeing players.
        chase_range (int): Max rooms to chase before returning home.

    Returns:
        AwtownMob: The created mob object.
    """
    from typeclasses.mobs import AwtownMob

    mob = create_object(AwtownMob, key=name, location=room)

    if desc:
        mob.db.desc = desc
    else:
        mob.db.desc = f"A {name}. It looks ready for a fight."

    mob.db.stats = stats or dict(DEFAULT_MOB_STATS)
    mob.db.hp = hp
    mob.db.hp_max = hp
    mob.db.level = level
    mob.db.xp_value = xp_value
    mob.db.damage_dice = damage_dice
    mob.db.armor_bonus = armor_bonus
    mob.db.loot_table = loot_table or []
    mob.db.wimpy = wimpy

    # Movement config
    mob.db.move_mode = move_mode
    mob.db.move_interval = move_interval
    mob.db.wander_chance = wander_chance
    mob.db.patrol_route = patrol_route or []
    mob.db.chase = chase
    mob.db.chase_range = chase_range
    mob.db.home_room = room.dbref

    # Attach movement script if needed
    if move_mode != "stationary" or chase:
        try:
            from contrib_dorfin.mob_movement import attach_movement_script
            attach_movement_script(
                mob, move_mode=move_mode, move_interval=move_interval,
                wander_chance=wander_chance, patrol_route=patrol_route,
                chase=chase, chase_range=chase_range, home_room=room.dbref,
            )
        except Exception as err:
            log_info(f"spawn_mob: failed to attach movement script: {err}")

    return mob


# ---------------------------------------------------------------------------
# Respawn script management
# ---------------------------------------------------------------------------

def ensure_respawn_script(room, mob_name="a mob", respawn_delay=30,
                          mob_dbref=None, **mob_kwargs):
    """
    Add a MobRespawnScript to a room if one isn't already running.
    Updates config if the script already exists.

    If an old-class script exists (from before the dbref-tracking
    refactor), it is deleted and replaced with a fresh one.

    Args:
        room: The home room (where the mob spawns).
        mob_name (str): Name of the mob to spawn.
        respawn_delay (int): Seconds between respawn checks.
        mob_dbref (str): Dbref of the currently living mob, if any.
        **mob_kwargs: All keyword args passed to spawn_mob on respawn.

    Returns:
        MobRespawnScript instance.
    """
    existing = room.scripts.get("MobRespawnScript")
    if existing:
        script = existing[0]
        # Check if this is the new class with is_mob_alive
        if hasattr(script, "is_mob_alive"):
            script.db.mob_name = mob_name
            script.db.mob_kwargs = mob_kwargs
            if mob_dbref:
                script.db.mob_dbref = mob_dbref
            return script
        else:
            # Old-class script — delete and recreate
            for s in existing:
                s.delete()

    from evennia import create_script
    script = create_script(
        MobRespawnScript,
        key="MobRespawnScript",
        obj=room,
        persistent=True,
        autostart=True,
    )
    script.db.mob_name = mob_name
    script.db.mob_kwargs = mob_kwargs
    script.db.mob_dbref = mob_dbref
    script.interval = respawn_delay
    return script


def spawn_and_track(room, respawn_script=None, respawn_delay=30, **mob_kwargs):
    """
    Spawn a mob and register its dbref with a respawn script.

    If no respawn_script is provided, one is created or found on
    the room. This is the recommended way to create mobs that should
    respawn after death.

    Args:
        room: Room to spawn in.
        respawn_script: Existing MobRespawnScript, or None.
        respawn_delay (int): Seconds between respawn checks.
        **mob_kwargs: Passed to spawn_mob().

    Returns:
        tuple: (mob, respawn_script)
    """
    mob_name = mob_kwargs.get("name", "a mob")
    mob = spawn_mob(room, **mob_kwargs)

    if not respawn_script:
        respawn_script = ensure_respawn_script(
            room, mob_name=mob_name, respawn_delay=respawn_delay,
            mob_dbref=mob.dbref, **mob_kwargs
        )
    else:
        respawn_script.db.mob_dbref = mob.dbref
        respawn_script.db.mob_kwargs = mob_kwargs

    return mob, respawn_script


# ---------------------------------------------------------------------------
# MobRespawnScript
# ---------------------------------------------------------------------------

class MobRespawnScript(DefaultScript):
    """
    Spawn-point respawn script. Tracks a mob by dbref.

    Attached to the mob's HOME ROOM. Works for stationary mobs,
    wandering mobs, and mobs that chase fleeing players — the mob
    may die anywhere in the world, but this script always checks
    whether its tracked dbref still exists in the database. When
    the mob is gone, it respawns a fresh one at the home room.

    db Attributes:
        mob_name   (str)  : Name of the mob to spawn.
        mob_dbref  (str)  : Dbref of the currently living mob, or None.
        mob_kwargs (dict) : Keyword args for spawn_mob() on respawn.
    """

    def at_script_creation(self):
        self.key = "MobRespawnScript"
        self.desc = "Tracks and respawns a mob at its home room."
        self.interval = 30
        self.persistent = True
        self.start_delay = False   # must be False — True resets on every reload
        self.db.mob_name = "a mob"
        self.db.mob_dbref = None
        self.db.mob_kwargs = {}
        self.db.tick_count = 0
        self.db.last_alive_tick = True
        self.db.death_noticed_at = None

    def at_init(self):
        """
        Called on every server reload. Fix start_delay on old scripts
        and force-restart the ticker to ensure at_repeat fires.
        """
        super().at_init()
        if self.start_delay:
            self.start_delay = False
        # Initialize fields that may not exist on old scripts
        if self.db.tick_count is None:
            self.db.tick_count = 0
        if self.db.last_alive_tick is None:
            self.db.last_alive_tick = True
        if self.db.death_noticed_at is None:
            self.db.death_noticed_at = None
        # Force restart the ticker — old scripts may have a dead timer
        # registration from a previous class version. This is safe:
        # restart() calls stop() then start(), re-registering the ticker
        # without calling at_script_creation() (so db attrs are preserved).
        if self.is_active:
            try:
                self.restart()
            except Exception:
                pass

    def at_repeat(self):
        room = self.obj
        if not room:
            self.stop()
            return

        self.db.tick_count = (self.db.tick_count or 0) + 1

        try:
            self._do_respawn_check(room)
        except Exception as err:
            # NEVER silently fail — log and try to spawn anyway
            log_info(
                f"MobRespawnScript ERROR in {room.name} (#{room.id}): {err}"
            )
            # Emergency spawn — skip all checks, just make a mob
            try:
                self._emergency_spawn(room)
            except Exception as err2:
                log_info(f"MobRespawnScript EMERGENCY SPAWN FAILED: {err2}")

    def _do_respawn_check(self, room):
        """Normal respawn logic, separated out for error handling."""
        # 1. Check if the tracked mob still exists ANYWHERE
        if self.is_mob_alive():
            self.db.last_alive_tick = True
            return

        # 2. Mob is gone. Record when we first noticed.
        if self.db.last_alive_tick:
            self.db.last_alive_tick = False
            self.db.death_noticed_at = self.db.tick_count or 0

        # 3. Clean zombie combat handlers on the home room.
        if is_combat_active(room):
            return

        # 4. Spawn a fresh mob — don't wait for corpses.
        #    Corpses are just loot containers; a new mob and an old
        #    corpse can coexist in the same room with no issues.
        self._spawn_fresh(room)

    def _spawn_fresh(self, room):
        """Spawn a fresh mob at the home room."""
        mob_name = self.db.mob_name or "a mob"
        mob_kwargs = dict(self.db.mob_kwargs or {})
        mob_kwargs["name"] = mob_name

        mob = spawn_mob(room, **mob_kwargs)
        self.db.mob_dbref = mob.dbref

        room.msg_contents(
            f"|yA new {mob_name} appears.|n"
        )
        log_info(
            f"MobRespawnScript: spawned {mob_name} ({mob.dbref}) "
            f"in {room.name} (#{room.id})"
        )

    def _emergency_spawn(self, room):
        """Last-resort spawn when normal checks error out."""
        mob_name = self.db.mob_name or "a mob"
        mob = spawn_mob(room, name=mob_name)
        self.db.mob_dbref = mob.dbref
        log_info(
            f"MobRespawnScript: EMERGENCY spawned {mob_name} ({mob.dbref}) "
            f"in {room.name} (#{room.id})"
        )

    def is_mob_alive(self):
        """
        Check if the tracked mob still exists and is alive.

        Returns True if the mob is alive somewhere in the world.
        Returns False if the mob is dead, deleted, or untracked.

        If no dbref is tracked yet, falls back to checking whether
        any mob exists in the home room (handles upgrade from old
        scripts or manual spawns).
        """
        tracked = self.db.mob_dbref
        if not tracked:
            # Fallback: scan home room for any mob, adopt it
            room = self.obj
            if room:
                for obj in room.contents:
                    if hasattr(obj, "db") and getattr(obj.db, "is_mob", False):
                        self.db.mob_dbref = obj.dbref
                        return True
            return False

        try:
            from evennia import search_object
            results = search_object(tracked)
            if not results:
                return False
            mob = results[0]
            if not mob.pk:
                return False
            if hasattr(mob, "is_alive"):
                return mob.is_alive()
            return True
        except Exception:
            return False
