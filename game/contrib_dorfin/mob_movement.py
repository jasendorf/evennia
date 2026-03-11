"""
DorfinMUD Mob Movement System
==============================

Three movement behaviors for mobs, configurable via db attributes:

Wander — mob randomly moves to an adjacent room on a timer.
         Respects safe rooms (won't enter). Configurable chance per tick.

Patrol — mob walks a fixed route of rooms (list of dbrefs), loops back.
         Moves one step per tick along the route.

Chase  — when a player flees combat, the mob follows through the same exit.
         Configurable chase range; mob returns home when range exceeded or
         target is lost.

The MobMovementScript is attached to the mob (not the room). It is
separate from MobRespawnScript (which is on the home room). When a mob
dies and respawns, spawn_mob() re-attaches a fresh movement script.

Usage
-----

    mob.db.move_mode = "wander"       # or "patrol" or "stationary"
    mob.db.move_interval = 30         # seconds between moves
    mob.db.wander_chance = 0.5        # 50% chance to move each tick
    mob.db.patrol_route = ["#123", "#124", "#125"]
    mob.db.chase = True               # follow fleeing players
    mob.db.chase_range = 3            # max rooms to chase
    mob.db.home_room = "#123"         # where to return after chase

Integration
-----------

Chase is triggered by calling trigger_chase(mob, target, exit_used) from
the flee command or combat handler when a player escapes combat.
"""

from random import random, choice

from evennia import DefaultScript
from evennia.utils.logger import log_info, log_err


class MobMovementScript(DefaultScript):
    """
    Persistent script on a mob that handles wander/patrol movement.

    db Attributes:
        move_mode      (str)  : "wander", "patrol", or "stationary"
        move_interval  (int)  : seconds between movement ticks
        wander_chance  (float): probability of moving each tick (0.0-1.0)
        patrol_route   (list) : list of room dbrefs for patrol path
        patrol_index   (int)  : current position in patrol route
        chase          (bool) : whether this mob chases fleeing players
        chase_range    (int)  : max rooms to chase before returning home
        chase_target   (str)  : dbref of player being chased
        chase_count    (int)  : rooms chased so far
        home_room      (str)  : dbref of home room (return after chase)
    """

    def at_script_creation(self):
        self.key = "MobMovementScript"
        self.desc = "Controls mob wander/patrol/chase movement."
        self.interval = 30
        self.persistent = True
        self.start_delay = True

        self.db.move_mode = "stationary"
        self.db.move_interval = 30
        self.db.wander_chance = 0.5
        self.db.patrol_route = []
        self.db.patrol_index = 0
        self.db.chase = False
        self.db.chase_range = 3
        self.db.chase_target = None
        self.db.chase_count = 0
        self.db.home_room = None

    def at_init(self):
        """Called on server reload. Ensure interval matches config."""
        super().at_init()
        interval = self.db.move_interval or 30
        if self.interval != interval:
            self.interval = interval
            if self.is_active:
                try:
                    self.restart()
                except Exception:
                    pass

    def at_repeat(self):
        """Called each tick. Dispatch based on move_mode."""
        mob = self.obj
        if not mob or not mob.pk:
            self.stop()
            return

        # Don't move while in combat
        if getattr(mob.db, "in_combat", False):
            return

        # If we're chasing, handle chase return logic
        if self.db.chase_target:
            self._handle_chase_return(mob)
            return

        mode = self.db.move_mode or "stationary"
        if mode == "wander":
            self._do_wander(mob)
        elif mode == "patrol":
            self._do_patrol(mob)
        # "stationary" does nothing

    def _do_wander(self, mob):
        """Move to a random adjacent room, respecting safe rooms and chance."""
        chance = self.db.wander_chance
        if chance is None:
            chance = 0.5
        if random() > chance:
            return

        room = mob.location
        if not room:
            return

        exits = self._get_valid_exits(room)
        if not exits:
            return

        exit_obj = choice(exits)
        mob.move_to(exit_obj.destination, quiet=False)

    def _do_patrol(self, mob):
        """Move to the next room in the patrol route."""
        route = self.db.patrol_route or []
        if not route:
            return

        index = self.db.patrol_index or 0
        if index >= len(route):
            index = 0

        target_ref = route[index]
        target_room = self._resolve(target_ref)
        if not target_room:
            # Skip invalid room, advance index
            self.db.patrol_index = (index + 1) % len(route)
            return

        # Only move if we're not already there
        if mob.location != target_room:
            # Find exit leading to target room
            exit_obj = self._find_exit_to(mob.location, target_room)
            if exit_obj:
                mob.move_to(target_room, quiet=False)
            else:
                # No direct exit — teleport silently (patrol route may skip rooms)
                mob.move_to(target_room, quiet=False)

        self.db.patrol_index = (index + 1) % len(route)

    def _handle_chase_return(self, mob):
        """
        Called each tick while a chase target is set.
        If the target is in the same room, re-engage combat.
        If the target is gone or chase_count exceeded, return home.
        """
        target = self._resolve(self.db.chase_target)

        # Target found in same room — re-engage
        if target and target.location == mob.location:
            self._engage_target(mob, target)
            self._clear_chase()
            return

        # Chase expired or target gone — return home
        chase_count = self.db.chase_count or 0
        chase_range = self.db.chase_range or 3

        if not target or chase_count >= chase_range:
            self._return_home(mob)
            self._clear_chase()
            return

        # Target is somewhere else but within chase range — keep waiting
        # (The actual chase step happens in trigger_chase, not here)
        # If target moved further away, give up
        self._return_home(mob)
        self._clear_chase()

    def _engage_target(self, mob, target):
        """Start combat with target in the current room."""
        room = mob.location
        if not room:
            return

        # Don't fight in safe rooms
        if getattr(room.db, "is_safe", False):
            return

        try:
            from contrib_dorfin.combat_handler import CombatHandler
            handler = CombatHandler.get_or_create(room)
            handler.add_combatant(mob, target)
            if not handler.is_in_combat(target):
                handler.add_combatant(target, mob)

            room.msg_contents(
                f"|r{mob.key} snarls and attacks {target.key}!|n"
            )
        except Exception as err:
            log_err(f"MobMovementScript._engage_target: {err}")

    def _return_home(self, mob):
        """Return mob to its home room."""
        home_ref = self.db.home_room
        if not home_ref:
            return

        home = self._resolve(home_ref)
        if not home or mob.location == home:
            return

        mob.move_to(home, quiet=True)
        if home:
            home.msg_contents(f"|y{mob.key} returns to its territory.|n")

    def _clear_chase(self):
        """Reset chase state."""
        self.db.chase_target = None
        self.db.chase_count = 0

    def _get_valid_exits(self, room):
        """
        Get exits from a room that the mob can use.
        Excludes exits to safe rooms and closed exits.
        """
        if not room:
            return []

        valid = []
        for ex in room.exits:
            # Skip closed exits
            if getattr(ex.db, "is_open", True) is False:
                continue
            dest = ex.destination
            if not dest:
                continue
            # Don't enter safe rooms
            if getattr(dest.db, "is_safe", False):
                continue
            valid.append(ex)
        return valid

    def _find_exit_to(self, from_room, to_room):
        """Find an exit from from_room that leads to to_room."""
        if not from_room:
            return None
        for ex in from_room.exits:
            if ex.destination == to_room:
                return ex
        return None

    def _resolve(self, dbref):
        """Resolve a dbref string to a live object."""
        if not dbref:
            return None
        try:
            from evennia import search_object
            results = search_object(dbref)
            return results[0] if results else None
        except Exception:
            return None


CHASE_MOVE_DELAY = 3    # seconds before mob follows through the exit
CHASE_ENGAGE_DELAY = 2  # seconds after arriving before re-engaging combat


def trigger_chase(mob, target, exit_used):
    """
    Called when a player flees combat. If the mob has chase enabled,
    it follows through the same exit after a short delay.

    The mob announces it's about to give chase, then follows after
    CHASE_MOVE_DELAY seconds. After arriving, it waits another
    CHASE_ENGAGE_DELAY seconds before re-engaging combat.

    Args:
        mob: The AwtownMob that might chase.
        target: The player who fled.
        exit_used: The exit object the player fled through, or None.
    """
    if not mob or not target:
        return

    # Check if mob has chase enabled
    if not getattr(mob.db, "chase", False):
        return

    # Don't chase if mob is dead
    if hasattr(mob, "is_alive") and not mob.is_alive():
        return

    # Get the movement script
    scripts = mob.scripts.get("MobMovementScript")
    if not scripts:
        return
    script = scripts[0]

    chase_range = script.db.chase_range or 3
    chase_count = (script.db.chase_count or 0) + 1

    if chase_count > chase_range:
        return

    # Determine destination
    if exit_used and exit_used.destination:
        destination = exit_used.destination
    else:
        return

    # Don't chase into safe rooms
    if getattr(destination.db, "is_safe", False):
        return

    # Set chase state
    script.db.chase_target = target.dbref
    script.db.chase_count = chase_count

    # Set home room if not already set
    if not script.db.home_room:
        script.db.home_room = mob.location.dbref if mob.location else None

    # Announce the chase is starting (mob hasn't moved yet)
    room = mob.location
    if room:
        room.msg_contents(
            f"|r{mob.key} snarls and prepares to give chase!|n"
        )

    # Store dbrefs for the delayed callbacks (objects may move/die)
    mob_dbref = mob.dbref
    target_dbref = target.dbref
    dest_dbref = destination.dbref

    # After a delay, the mob follows
    from evennia.utils import delay
    delay(CHASE_MOVE_DELAY, _chase_move, mob_dbref, target_dbref,
          dest_dbref, persistent=False)


def _chase_move(mob_dbref, target_dbref, dest_dbref):
    """
    Delayed callback: move the mob through to the destination room.
    Called CHASE_MOVE_DELAY seconds after the player fled.
    """
    from evennia import search_object

    mob_results = search_object(mob_dbref)
    if not mob_results:
        return
    mob = mob_results[0]

    # Mob may have died or entered combat in the meantime
    if hasattr(mob, "is_alive") and not mob.is_alive():
        return
    if getattr(mob.db, "in_combat", False):
        return

    dest_results = search_object(dest_dbref)
    if not dest_results:
        return
    destination = dest_results[0]

    # Don't chase into safe rooms (re-check in case it changed)
    if getattr(destination.db, "is_safe", False):
        _abort_chase(mob)
        return

    # Move the mob
    old_room = mob.location
    mob.move_to(destination, quiet=False)

    if old_room:
        old_room.msg_contents(
            f"|r{mob.key} charges after its prey!|n"
        )

    # After another delay, re-engage combat
    from evennia.utils import delay
    delay(CHASE_ENGAGE_DELAY, _chase_engage, mob_dbref, target_dbref,
          dest_dbref, persistent=False)


def _chase_engage(mob_dbref, target_dbref, dest_dbref):
    """
    Delayed callback: re-engage combat with the target if both are
    in the same room. Called CHASE_ENGAGE_DELAY seconds after the
    mob arrived.
    """
    from evennia import search_object

    mob_results = search_object(mob_dbref)
    if not mob_results:
        return
    mob = mob_results[0]

    if hasattr(mob, "is_alive") and not mob.is_alive():
        return
    if getattr(mob.db, "in_combat", False):
        return

    target_results = search_object(target_dbref)
    if not target_results:
        _abort_chase(mob)
        return
    target = target_results[0]

    # Target must still be in the same room
    if target.location != mob.location:
        _abort_chase(mob)
        return

    # Don't fight in safe rooms
    if getattr(mob.location.db, "is_safe", False):
        _abort_chase(mob)
        return

    try:
        from contrib_dorfin.combat_handler import CombatHandler
        handler = CombatHandler.get_or_create(mob.location)
        handler.add_combatant(mob, target)
        handler.add_combatant(target, mob)
        mob.location.msg_contents(
            f"|r{mob.key} catches up and attacks {target.key}!|n"
        )
    except Exception as err:
        log_err(f"_chase_engage: combat re-engage failed: {err}")


def _abort_chase(mob):
    """Clear chase state and return mob home if possible."""
    scripts = mob.scripts.get("MobMovementScript")
    if scripts:
        script = scripts[0]
        script._return_home(mob)
        script._clear_chase()


def attach_movement_script(mob, move_mode="stationary", move_interval=30,
                            wander_chance=0.5, patrol_route=None,
                            chase=False, chase_range=3, home_room=None):
    """
    Attach a MobMovementScript to a mob with the given config.

    If a movement script already exists on the mob, update its config
    instead of creating a duplicate.

    Args:
        mob: The mob object.
        move_mode (str): "wander", "patrol", or "stationary".
        move_interval (int): Seconds between movement ticks.
        wander_chance (float): Chance to move each wander tick.
        patrol_route (list): List of room dbrefs for patrol.
        chase (bool): Whether to chase fleeing players.
        chase_range (int): Max rooms to chase.
        home_room (str): Dbref of home room.

    Returns:
        MobMovementScript instance, or None if stationary with no chase.
    """
    # Don't create a script if there's nothing to do
    if move_mode == "stationary" and not chase:
        return None

    existing = mob.scripts.get("MobMovementScript")
    if existing:
        script = existing[0]
    else:
        from evennia import create_script
        script = create_script(
            MobMovementScript,
            key="MobMovementScript",
            obj=mob,
            persistent=True,
            autostart=True,
        )

    script.db.move_mode = move_mode
    script.db.move_interval = move_interval
    script.db.wander_chance = wander_chance
    script.db.patrol_route = patrol_route or []
    script.db.patrol_index = 0
    script.db.chase = chase
    script.db.chase_range = chase_range
    script.db.home_room = home_room or (mob.location.dbref if mob.location else None)

    # Update interval
    if script.interval != move_interval:
        script.interval = move_interval
        if script.is_active:
            try:
                script.restart()
            except Exception:
                pass

    return script
