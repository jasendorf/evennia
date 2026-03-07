"""
Admin combat commands
=====================

    @trainingroom       -- create a training room and teleport there
    @spawnmob <name>    -- spawn a test mob in current room
    @stopcombat         -- force-stop combat in current room, clear all state
    @combatdebug        -- show combat handler state for current room

These are builder/admin commands for testing Phase 5 combat.
"""

from evennia.commands.command import Command
from evennia import create_object


class CmdTrainingRoom(Command):
    """
    Create a training room with a practice dummy mob and teleport there.

    Usage:
        @trainingroom

    Creates a room called "The Training Yard" that is NOT safe,
    spawns a training dummy mob, and teleports you there. The room
    persists — use it any time for combat testing.

    The training dummy respawns 30 seconds after being killed.
    """

    key = "@trainingroom"
    locks = "cmd:perm(Admin) or perm(Builder)"
    help_category = "Admin"

    def func(self):
        caller = self.caller

        # Check if room already exists
        import evennia
        existing = evennia.search_tag("training_yard", category="awtown_dbkey")
        if existing:
            room = existing[0]
            caller.msg(f"|gTraining room already exists: {room.name} (#{room.id})|n")
        else:
            # Create the room
            from typeclasses.rooms import AwtownRoom
            room = create_object(AwtownRoom, key="The Training Yard")
            room.db.desc = (
                "A walled yard of packed dirt behind the Warden's Barracks. "
                "Straw dummies and weapon racks line the walls. Scuff marks and "
                "dried bloodstains suggest this place sees heavy use. A sign reads: "
                "'|wHit things here. Not in town.|n'"
            )
            room.db.is_safe = False
            room.db.no_pvp = True
            room.db.is_outdoor = True
            room.db.room_type = "training"
            room.tags.add("training_yard", category="awtown_dbkey")
            caller.msg(f"|gCreated: {room.name} (#{room.id})|n")

            # Create a two-way exit from the Warden's Barracks if it exists
            barracks = evennia.search_tag("warden_barracks", category="awtown_dbkey")
            if barracks:
                from evennia.objects.objects import DefaultExit
                # Barracks -> Training Yard
                if not any(ex.key == "yard" for ex in barracks[0].exits):
                    create_object(
                        DefaultExit,
                        key="yard",
                        location=barracks[0],
                        destination=room,
                        aliases=["training", "training yard"],
                    )
                # Training Yard -> Barracks
                if not any(ex.key == "barracks" for ex in room.exits):
                    create_object(
                        DefaultExit,
                        key="barracks",
                        location=room,
                        destination=barracks[0],
                        aliases=["back", "out"],
                    )
                caller.msg("|gLinked to Warden's Barracks.|n")

        # Teleport
        caller.move_to(room, quiet=True)
        caller.msg(caller.at_look(room))

        # Spawn a dummy if none exists
        has_mob = any(
            getattr(obj.db, "is_mob", False)
            for obj in room.contents
            if hasattr(obj, "db")
        )
        if not has_mob:
            _spawn_training_dummy(room)
            caller.msg("|gSpawned a training dummy.|n")
        else:
            caller.msg("|yA training mob is already here.|n")


class CmdSpawnMob(Command):
    """
    Spawn a test mob in your current room.

    Usage:
        @spawnmob
        @spawnmob <name>

    Spawns a level 1 training mob. The room must not be safe.
    Default name is "a training dummy" if none given.
    """

    key = "@spawnmob"
    locks = "cmd:perm(Admin) or perm(Builder)"
    help_category = "Admin"

    def func(self):
        caller = self.caller
        room = caller.location

        if getattr(room.db, "is_safe", True):
            caller.msg(
                "|rThis room is safe — mobs can't be fought here.|n\n"
                "Set it unsafe first: |w@py self.location.db.is_safe = False|n\n"
                "Or use |w@trainingroom|n for a ready-made combat room."
            )
            return

        name = self.args.strip() or "a training dummy"
        mob = _spawn_training_dummy(room, name=name)
        caller.msg(f"|gSpawned: {mob.key} (#{mob.id}) in {room.name}|n")


class CmdStopCombat(Command):
    """
    Force-stop all combat in the current room and clean up state.

    Usage:
        @stopcombat

    Stops the CombatHandler script, clears in_combat flags on all
    characters in the room, and removes stale combat state.
    Use when combat gets stuck.
    """

    key = "@stopcombat"
    locks = "cmd:perm(Admin) or perm(Builder)"
    help_category = "Admin"

    def func(self):
        caller = self.caller
        room = caller.location

        # Kill ALL CombatHandler scripts on this room
        handlers = room.scripts.get("CombatHandler")
        count = len(handlers) if handlers else 0
        if handlers:
            for h in handlers:
                # Clean up combatants first
                for dbref in list(h.db.combatants or []):
                    try:
                        from evennia import search_object
                        results = search_object(dbref)
                        if results:
                            obj = results[0]
                            obj.db.in_combat = False
                            obj.db.combat_target = None
                    except Exception:
                        pass
                h.stop()
            caller.msg(f"|gStopped {count} CombatHandler(s).|n")
        else:
            caller.msg("|yNo CombatHandler found on this room.|n")

        # Also clear in_combat on everyone in the room just in case
        for obj in room.contents:
            if hasattr(obj, "db"):
                if getattr(obj.db, "in_combat", False):
                    obj.db.in_combat = False
                    obj.db.combat_target = None
                    caller.msg(f"  Cleared combat state on {obj.name}")

        caller.msg("|gCombat state cleaned up.|n")


class CmdCombatDebug(Command):
    """
    Show the combat handler state for the current room.

    Usage:
        @combatdebug

    Shows all CombatHandler scripts, their combatants, targets,
    tick counts, and whether characters think they're in combat.
    """

    key = "@combatdebug"
    aliases = ["@cdebug"]
    locks = "cmd:perm(Admin) or perm(Builder)"
    help_category = "Admin"

    def func(self):
        caller = self.caller
        room = caller.location
        lines = [f"|w=== Combat Debug: {room.name} (#{room.id}) ===|n"]

        # Room flags
        lines.append(f"  is_safe: {getattr(room.db, 'is_safe', 'NOT SET')}")
        lines.append(f"  no_pvp: {getattr(room.db, 'no_pvp', 'NOT SET')}")

        # All scripts on the room
        all_scripts = room.scripts.all()
        lines.append(f"\n  Scripts on room: {len(all_scripts)}")
        for s in all_scripts:
            lines.append(
                f"    {s.key} (#{s.id}) interval={s.interval} "
                f"is_active={s.is_active} repeats={s.repeats}"
            )

        # CombatHandler details
        handlers = room.scripts.get("CombatHandler")
        if handlers:
            for i, h in enumerate(handlers):
                lines.append(f"\n|w  --- CombatHandler #{i+1} (#{h.id}) ---|n")
                lines.append(f"    tick_count: {h.db.tick_count}")
                lines.append(f"    is_active: {h.is_active}")
                lines.append(f"    interval: {h.interval}")
                lines.append(f"    start_delay: {h.start_delay}")

                combatants = h.db.combatants or []
                lines.append(f"    combatants ({len(combatants)}):")
                for dbref in combatants:
                    try:
                        from evennia import search_object
                        results = search_object(dbref)
                        if results:
                            obj = results[0]
                            target_ref = (h.db.targets or {}).get(dbref, "none")
                            hp_str = ""
                            if hasattr(obj, "get_hp"):
                                hp_str = f" HP:{obj.get_hp()}/{obj.get_hp_max()}"
                            lines.append(
                                f"      {obj.name} ({dbref}){hp_str} -> {target_ref}"
                            )
                        else:
                            lines.append(f"      MISSING ({dbref})")
                    except Exception as e:
                        lines.append(f"      ERROR ({dbref}): {e}")

                aggro = h.db.aggro_locks or {}
                if aggro:
                    lines.append(f"    aggro_locks: {aggro}")
        else:
            lines.append("\n  |yNo CombatHandler on this room.|n")

        # Character combat state
        lines.append(f"\n|w  --- Character State ---|n")
        for obj in room.contents:
            if hasattr(obj, "db") and hasattr(obj.db, "in_combat"):
                in_combat = getattr(obj.db, "in_combat", False)
                is_mob = getattr(obj.db, "is_mob", False)
                tag = "MOB" if is_mob else "PC"
                hp_str = ""
                if hasattr(obj, "get_hp"):
                    hp_str = f" HP:{obj.get_hp()}/{obj.get_hp_max()}"
                lines.append(
                    f"    [{tag}] {obj.name} ({obj.dbref}){hp_str}"
                    f" in_combat={in_combat}"
                )

        caller.msg("\n".join(lines))


# ---------------------------------------------------------------------------
# Mob spawning helper
# ---------------------------------------------------------------------------

def _spawn_training_dummy(room, name="a training dummy"):
    """Spawn a basic training mob with a respawn script."""
    from typeclasses.mobs import AwtownMob

    mob = create_object(AwtownMob, key=name, location=room)
    mob.db.desc = (
        "A straw-stuffed practice dummy propped up on a wooden frame. "
        "Someone has drawn an angry face on it in charcoal."
        if "dummy" in name
        else f"A {name} ready for a fight."
    )
    mob.db.stats = {
        "str": 6, "dex": 10, "agi": 10, "con": 6, "end": 8,
        "int": 2, "wis": 3, "per": 8, "cha": 1, "lck": 5,
    }
    mob.db.hp = 20
    mob.db.hp_max = 20
    mob.db.level = 1
    mob.db.xp_value = 10
    mob.db.damage_dice = "1d4"
    mob.db.armor_bonus = 0
    mob.db.loot_table = [
        {"name": "straw stuffing", "desc": "A handful of straw from the dummy.", "value": 1, "chance": 0.5},
    ]

    # Add respawn script to the ROOM (not the mob — mob gets deleted on death)
    _ensure_respawn_script(room, name)

    return mob


def _ensure_respawn_script(room, mob_name):
    """Add a MobRespawnScript to a room if one isn't already running."""
    existing = room.scripts.get("MobRespawnScript")
    if existing:
        return existing[0]

    from evennia import create_script
    script = create_script(
        MobRespawnScript,
        key="MobRespawnScript",
        obj=room,
        persistent=True,
        autostart=True,
    )
    script.db.mob_name = mob_name
    return script


from evennia import DefaultScript


class MobRespawnScript(DefaultScript):
    """
    Checks every 30 seconds if the room's mob is dead/gone and respawns it.

    Attached to the room, not the mob (since the mob gets deleted on death).
    """

    def at_script_creation(self):
        self.key = "MobRespawnScript"
        self.desc = "Respawns a training mob when it dies."
        self.interval = 30
        self.persistent = True
        self.start_delay = True
        self.db.mob_name = "a training dummy"

    def at_repeat(self):
        room = self.obj
        if not room:
            self.stop()
            return

        # Check if a mob exists in the room
        has_mob = any(
            getattr(obj.db, "is_mob", False)
            for obj in room.contents
            if hasattr(obj, "db")
        )

        # Also make sure there's no active combat
        handlers = room.scripts.get("CombatHandler")
        in_combat = bool(handlers)

        if not has_mob and not in_combat:
            mob_name = self.db.mob_name or "a training dummy"
            from typeclasses.mobs import AwtownMob

            mob = create_object(AwtownMob, key=mob_name, location=room)
            mob.db.desc = (
                "A straw-stuffed practice dummy propped up on a wooden frame. "
                "Someone has drawn an angry face on it in charcoal."
                if "dummy" in mob_name
                else f"A {mob_name} ready for a fight."
            )
            mob.db.stats = {
                "str": 6, "dex": 10, "agi": 10, "con": 6, "end": 8,
                "int": 2, "wis": 3, "per": 8, "cha": 1, "lck": 5,
            }
            mob.db.hp = 20
            mob.db.hp_max = 20
            mob.db.level = 1
            mob.db.xp_value = 10
            mob.db.damage_dice = "1d4"
            mob.db.armor_bonus = 0
            mob.db.loot_table = [
                {"name": "straw stuffing", "desc": "A handful of straw.", "value": 1, "chance": 0.5},
            ]

            room.msg_contents(
                f"|yA new {mob_name} appears, ready for a beating.|n"
            )
