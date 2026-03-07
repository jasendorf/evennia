"""
Admin combat commands
=====================

    @trainingroom       -- create/go to training room, ensure mob + respawn
    @spawnmob <name>    -- spawn a test mob in current room
    @stopcombat         -- force-stop combat in current room, clear all state
    @combatdebug        -- show combat handler state for current room
    @fixcombat          -- global cleanup: nuke ALL zombie combat handlers

These are builder/admin commands for testing Phase 5 combat.
"""

from evennia.commands.command import Command
from evennia import create_object, DefaultScript
from evennia.utils.logger import log_info


# ---------------------------------------------------------------------------
# Zombie cleanup utility — used by respawn, @stopcombat, @fixcombat
# ---------------------------------------------------------------------------

def cleanup_combat_zombies(room):
    """
    Find and delete any CombatHandler scripts on a room that are
    inactive (zombies). Returns the count of zombies removed.
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
    """
    cleanup_combat_zombies(room)
    handlers = room.scripts.get("CombatHandler")
    if not handlers:
        return False
    return any(h.is_active for h in handlers)


# ---------------------------------------------------------------------------
# Mob spawning helpers
# ---------------------------------------------------------------------------

DEFAULT_DUMMY_STATS = {
    "str": 6, "dex": 10, "agi": 10, "con": 6, "end": 8,
    "int": 2, "wis": 3, "per": 8, "cha": 1, "lck": 5,
}


def spawn_mob(room, name="a training dummy", stats=None, hp=20, level=1,
              xp_value=10, damage_dice="1d4", armor_bonus=0, desc=None,
              loot_table=None):
    """
    Spawn a mob in a room. Reusable by commands, scripts, and batch code.
    """
    from typeclasses.mobs import AwtownMob

    mob = create_object(AwtownMob, key=name, location=room)

    if desc:
        mob.db.desc = desc
    elif "dummy" in name:
        mob.db.desc = (
            "A straw-stuffed practice dummy propped up on a wooden frame. "
            "Someone has drawn an angry face on it in charcoal."
        )
    else:
        mob.db.desc = f"A {name}. It looks ready for a fight."

    mob.db.stats = stats or dict(DEFAULT_DUMMY_STATS)
    mob.db.hp = hp
    mob.db.hp_max = hp
    mob.db.level = level
    mob.db.xp_value = xp_value
    mob.db.damage_dice = damage_dice
    mob.db.armor_bonus = armor_bonus
    mob.db.loot_table = loot_table or [
        {"name": "straw stuffing", "desc": "A handful of straw.",
         "value": 1, "chance": 0.5},
    ]

    return mob


def ensure_respawn_script(room, mob_name="a training dummy", **mob_kwargs):
    """
    Add a MobRespawnScript to a room if one isn't already running.
    Updates the mob config if the script already exists.
    """
    existing = room.scripts.get("MobRespawnScript")
    if existing:
        script = existing[0]
        script.db.mob_name = mob_name
        script.db.mob_kwargs = mob_kwargs
        return script

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
    return script


# ---------------------------------------------------------------------------
# MobRespawnScript
# ---------------------------------------------------------------------------

class MobRespawnScript(DefaultScript):
    """
    Checks every 30 seconds if the room's mob is dead/gone and respawns it.

    Attached to the room, not the mob (since the mob gets deleted on death).
    Automatically cleans up zombie CombatHandlers before checking.
    """

    def at_script_creation(self):
        self.key = "MobRespawnScript"
        self.desc = "Respawns a training mob when it dies."
        self.interval = 30
        self.persistent = True
        self.start_delay = True
        self.db.mob_name = "a training dummy"
        self.db.mob_kwargs = {}

    def at_repeat(self):
        room = self.obj
        if not room:
            self.stop()
            return

        # Check if a mob already exists
        has_mob = any(
            getattr(obj.db, "is_mob", False)
            for obj in room.contents
            if hasattr(obj, "db")
        )

        if has_mob:
            return

        # Clean zombies and check for REAL active combat
        if is_combat_active(room):
            return

        # Spawn mob
        mob_name = self.db.mob_name or "a training dummy"
        mob_kwargs = self.db.mob_kwargs or {}
        spawn_mob(room, name=mob_name, **mob_kwargs)

        room.msg_contents(
            f"|yA new {mob_name} appears, ready for a beating.|n"
        )


# ---------------------------------------------------------------------------
# @trainingroom
# ---------------------------------------------------------------------------

class CmdTrainingRoom(Command):
    """
    Create a training room with a practice dummy mob and teleport there.

    Usage:
        @trainingroom

    Creates "The Training Yard" linked to the Warden's Barracks.
    Ensures a respawn script is active and a dummy is present.
    Safe to run repeatedly — it fixes any broken state.
    """

    key = "@trainingroom"
    locks = "cmd:perm(Admin) or perm(Builder)"
    help_category = "Admin"

    def func(self):
        caller = self.caller

        import evennia
        existing = evennia.search_tag("training_yard", category="awtown_dbkey")
        if existing:
            room = existing[0]
            caller.msg(f"|gTraining room exists: {room.name} (#{room.id})|n")
        else:
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

            barracks = evennia.search_tag("warden_barracks", category="awtown_dbkey")
            if barracks:
                from evennia.objects.objects import DefaultExit
                if not any(ex.key == "yard" for ex in barracks[0].exits):
                    create_object(
                        DefaultExit, key="yard",
                        location=barracks[0], destination=room,
                        aliases=["training", "training yard"],
                    )
                if not any(ex.key == "barracks" for ex in room.exits):
                    create_object(
                        DefaultExit, key="barracks",
                        location=room, destination=barracks[0],
                        aliases=["back", "out"],
                    )
                caller.msg("|gLinked to Warden's Barracks.|n")

        # Teleport
        caller.move_to(room, quiet=True)
        caller.msg(caller.at_look(room))

        # Clean up zombies
        zombies = cleanup_combat_zombies(room)
        if zombies:
            caller.msg(f"|yCleaned up {zombies} stale combat handler(s).|n")

        # Ensure respawn script
        ensure_respawn_script(room, "a training dummy")

        # Spawn a dummy right now if needed
        has_mob = any(
            getattr(obj.db, "is_mob", False)
            for obj in room.contents
            if hasattr(obj, "db")
        )
        if not has_mob and not is_combat_active(room):
            spawn_mob(room, "a training dummy")
            caller.msg("|gSpawned a training dummy.|n")
        elif has_mob:
            caller.msg("|yA training mob is already here.|n")


# ---------------------------------------------------------------------------
# @spawnmob
# ---------------------------------------------------------------------------

class CmdSpawnMob(Command):
    """
    Spawn a test mob in your current room.

    Usage:
        @spawnmob
        @spawnmob <name>

    The room must not be safe. Default is "a training dummy".
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
                "Use |w@trainingroom|n for a ready-made combat room."
            )
            return

        name = self.args.strip() or "a training dummy"
        mob = spawn_mob(room, name=name)
        caller.msg(f"|gSpawned: {mob.key} (#{mob.id}) in {room.name}|n")


# ---------------------------------------------------------------------------
# @stopcombat
# ---------------------------------------------------------------------------

class CmdStopCombat(Command):
    """
    Force-stop all combat in the current room and clean up state.

    Usage:
        @stopcombat

    Deletes all CombatHandler scripts (active and zombie), clears
    in_combat flags on all characters in the room.
    """

    key = "@stopcombat"
    locks = "cmd:perm(Admin) or perm(Builder)"
    help_category = "Admin"

    def func(self):
        caller = self.caller
        room = caller.location

        handlers = room.scripts.get("CombatHandler")
        count = len(handlers) if handlers else 0
        if handlers:
            for h in list(handlers):
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
            caller.msg(f"|gDeleted {count} CombatHandler(s).|n")
        else:
            caller.msg("|yNo CombatHandler found on this room.|n")

        for obj in room.contents:
            if hasattr(obj, "db"):
                if getattr(obj.db, "in_combat", False):
                    obj.db.in_combat = False
                    obj.db.combat_target = None
                    caller.msg(f"  Cleared combat state on {obj.name}")

        caller.msg("|gCombat state cleaned up.|n")


# ---------------------------------------------------------------------------
# @fixcombat — global cleanup
# ---------------------------------------------------------------------------

class CmdFixCombat(Command):
    """
    Global cleanup: find and destroy ALL zombie CombatHandlers
    across every room in the game. Also clears stale in_combat
    flags on all characters.

    Usage:
        @fixcombat

    Run this after server restarts or when combat gets stuck.
    Safe to run any time — it only removes inactive handlers and
    stale flags.
    """

    key = "@fixcombat"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"

    def func(self):
        caller = self.caller

        from evennia.scripts.models import ScriptDB

        # Find ALL CombatHandler scripts in the game
        all_handlers = ScriptDB.objects.filter(db_key="CombatHandler")
        total = all_handlers.count()
        zombies = 0
        active = 0

        for h in list(all_handlers):
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
                room_name = h.obj.name if h.obj else "unknown"
                h.delete()
                zombies += 1
                caller.msg(f"  |xDeleted zombie handler in {room_name}|n")
            else:
                active += 1

        # Clear stale in_combat on ALL player characters
        stale_chars = 0
        try:
            from typeclasses.characters import AwtownCharacter
            for char in AwtownCharacter.objects.all():
                if getattr(char.db, "in_combat", False):
                    if char.location:
                        real_handlers = char.location.scripts.get("CombatHandler")
                        in_real_fight = any(
                            h.is_active and char.dbref in (h.db.combatants or [])
                            for h in (real_handlers or [])
                        )
                        if not in_real_fight:
                            char.db.in_combat = False
                            char.db.combat_target = None
                            stale_chars += 1
                            caller.msg(f"  Cleared stale combat on {char.name}")
                    else:
                        char.db.in_combat = False
                        char.db.combat_target = None
                        stale_chars += 1
        except Exception as err:
            caller.msg(f"  |rError scanning characters: {err}|n")

        caller.msg(
            f"\n|w=== @fixcombat Results ===|n\n"
            f"  Total CombatHandlers found: {total}\n"
            f"  Zombies deleted: {zombies}\n"
            f"  Active (left alone): {active}\n"
            f"  Characters with stale combat state: {stale_chars}\n"
            f"|gDone.|n"
        )


# ---------------------------------------------------------------------------
# @combatdebug
# ---------------------------------------------------------------------------

class CmdCombatDebug(Command):
    """
    Show the combat handler state for the current room.

    Usage:
        @combatdebug
    """

    key = "@combatdebug"
    aliases = ["@cdebug"]
    locks = "cmd:perm(Admin) or perm(Builder)"
    help_category = "Admin"

    def func(self):
        caller = self.caller
        room = caller.location
        lines = [f"|w=== Combat Debug: {room.name} (#{room.id}) ===|n"]

        lines.append(f"  is_safe: {getattr(room.db, 'is_safe', 'NOT SET')}")
        lines.append(f"  no_pvp: {getattr(room.db, 'no_pvp', 'NOT SET')}")

        all_scripts = room.scripts.all()
        lines.append(f"\n  Scripts on room: {len(all_scripts)}")
        for s in all_scripts:
            status = "|gACTIVE|n" if s.is_active else "|rINACTIVE/ZOMBIE|n"
            lines.append(
                f"    {s.key} (#{s.id}) {status} interval={s.interval}"
            )

        handlers = room.scripts.get("CombatHandler")
        if handlers:
            for i, h in enumerate(handlers):
                lines.append(f"\n|w  --- CombatHandler #{i+1} (#{h.id}) ---|n")
                lines.append(f"    tick_count: {h.db.tick_count}")
                lines.append(f"    is_active: {h.is_active}")

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
        else:
            lines.append("\n  |yNo CombatHandler on this room.|n")

        lines.append(f"\n|w  --- Characters ---|n")
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
