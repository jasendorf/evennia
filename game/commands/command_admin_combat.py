"""
Admin combat commands
=====================

    @trainingroom       -- create/go to training room, ensure mob + respawn
    @testarena          -- create multi-room test area for movement behaviors
    @spawnmob <name>    -- spawn a test mob in current room with respawn
    @stopcombat         -- force-stop combat in current room, clear all state
    @combatdebug        -- show combat handler state for current room
    @fixcombat          -- global cleanup: nuke ALL zombie combat handlers

These are builder/admin commands. All infrastructure (spawning, respawn
scripts, zombie cleanup) lives in contrib_dorfin.mob_spawner.
"""

from evennia.commands.command import Command
from evennia import create_object

from contrib_dorfin.mob_spawner import (
    spawn_mob,
    spawn_and_track,
    ensure_respawn_script,
    cleanup_combat_zombies,
    is_combat_active,
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
        respawn = ensure_respawn_script(room, "a training dummy")

        # Spawn a dummy right now if needed
        if not respawn.is_mob_alive() and not is_combat_active(room):
            mob, _ = spawn_and_track(
                room, respawn_script=respawn, name="a training dummy",
                desc=(
                    "A straw-stuffed practice dummy propped up on a wooden "
                    "frame. Someone has drawn an angry face on it in charcoal."
                ),
                hp=20, level=1, xp_value=10, damage_dice="1d4",
                loot_table=[
                    {"name": "straw stuffing",
                     "desc": "A handful of straw from the dummy.",
                     "value": 1, "chance": 0.5},
                ],
            )
            caller.msg(f"|gSpawned a training dummy (tracking {mob.dbref}).|n")
        else:
            caller.msg("|yA training mob is already alive.|n")


# ---------------------------------------------------------------------------
# @testarena
# ---------------------------------------------------------------------------

class CmdTestArena(Command):
    """
    Create a multi-room test arena for mob movement behaviors.

    Usage:
        @testarena

    Creates four connected rooms in a loop:

        [Arena North] --- [Arena East]
              |                |
        [Arena West]  --- [Arena South]

    Each room is non-safe. Spawns test mobs:
      - Arena North: a wandering rat (wander mode)
      - Arena East:  a patrolling guard (patrol mode, loops all 4 rooms)
      - Arena South: a fierce wolf (chase mode, follows you 3 rooms)
      - Arena West:  empty (for observing arrivals)

    Safe to run repeatedly — finds existing rooms by tag.
    """

    key = "@testarena"
    locks = "cmd:perm(Admin) or perm(Builder)"
    help_category = "Admin"

    def func(self):
        caller = self.caller

        import evennia
        from typeclasses.rooms import AwtownRoom
        from evennia.objects.objects import DefaultExit

        # Room definitions: (tag, name, description)
        room_defs = [
            ("test_arena_north", "Arena North",
             "A sandy clearing ringed by wooden fences. Scuff marks cover the "
             "ground. A weathered sign reads: '|wWander Zone|n'. Exits lead "
             "east and west."),
            ("test_arena_east", "Arena East",
             "A cobblestone yard with torch sconces bolted to iron posts. "
             "A sign reads: '|wPatrol Route|n'. Exits lead north and south."),
            ("test_arena_south", "Arena South",
             "A muddy pit surrounded by sharpened stakes. A sign reads: "
             "'|wChase Zone — watch your back|n'. Exits lead east and west."),
            ("test_arena_west", "Arena West",
             "An empty stretch of hard-packed dirt. Good for observing mob "
             "arrivals. A sign reads: '|wObservation Point|n'. Exits lead "
             "north and south."),
        ]

        # Create or find rooms
        rooms = {}
        for tag, name, desc in room_defs:
            existing = evennia.search_tag(tag, category="awtown_dbkey")
            if existing:
                room = existing[0]
                caller.msg(f"|yFound existing: {room.name} (#{room.id})|n")
            else:
                room = create_object(AwtownRoom, key=name)
                room.db.desc = desc
                room.db.is_safe = False
                room.db.is_outdoor = True
                room.db.room_type = "arena"
                room.tags.add(tag, category="awtown_dbkey")
                caller.msg(f"|gCreated: {room.name} (#{room.id})|n")
            rooms[tag] = room

        north = rooms["test_arena_north"]
        east = rooms["test_arena_east"]
        south = rooms["test_arena_south"]
        west = rooms["test_arena_west"]

        # Connect rooms in a loop: N-E-S-W-N
        exit_map = [
            (north, "east", east, "west"),
            (east, "south", south, "north"),
            (south, "west", west, "east"),
            (west, "north", north, "south"),
        ]

        for from_room, exit_name, to_room, return_name in exit_map:
            if not any(ex.key == exit_name for ex in from_room.exits):
                create_object(DefaultExit, key=exit_name,
                              location=from_room, destination=to_room)
            if not any(ex.key == return_name for ex in to_room.exits):
                create_object(DefaultExit, key=return_name,
                              location=to_room, destination=from_room)

        # Link to training yard if it exists
        training = evennia.search_tag("training_yard", category="awtown_dbkey")
        if training:
            ty = training[0]
            if not any(ex.key == "arena" for ex in ty.exits):
                create_object(DefaultExit, key="arena",
                              location=ty, destination=north,
                              aliases=["test arena"])
            if not any(ex.key == "training" for ex in north.exits):
                create_object(DefaultExit, key="training",
                              location=north, destination=ty,
                              aliases=["yard", "back"])
            caller.msg("|gLinked to Training Yard.|n")

        caller.msg("")

        # Build patrol route (all 4 rooms in loop order)
        patrol_route = [north.dbref, east.dbref, south.dbref, west.dbref]

        # Spawn mobs if not already present
        mob_defs = [
            (north, {
                "name": "a wandering rat", "hp": 15, "level": 1,
                "xp_value": 15, "damage_dice": "1d4",
                "desc": "A mangy brown rat. It skitters nervously, looking "
                        "for an exit.",
                "move_mode": "wander", "move_interval": 20,
                "wander_chance": 0.6,
            }),
            (east, {
                "name": "a patrolling guard", "hp": 40, "level": 3,
                "xp_value": 60, "damage_dice": "1d8", "armor_bonus": 3,
                "desc": "A stern guard in dented plate armor. He marches a "
                        "steady circuit around the arena.",
                "move_mode": "patrol", "move_interval": 15,
                "patrol_route": patrol_route,
            }),
            (south, {
                "name": "a fierce wolf", "hp": 30, "level": 2,
                "xp_value": 40, "damage_dice": "1d6",
                "desc": "A lean grey wolf with hungry yellow eyes. It looks "
                        "like it would chase anything that runs.",
                "chase": True, "chase_range": 3,
            }),
        ]

        for room, kwargs in mob_defs:
            # Check if a respawn script already has a living mob
            respawns = room.scripts.get("MobRespawnScript")
            if respawns and respawns[0].is_mob_alive():
                caller.msg(
                    f"|y  {kwargs['name']} already alive in {room.name}.|n"
                )
                continue

            cleanup_combat_zombies(room)
            if is_combat_active(room):
                caller.msg(
                    f"|r  Combat active in {room.name}, skipping spawn.|n"
                )
                continue

            mob, script = spawn_and_track(room, **kwargs)
            caller.msg(
                f"|g  Spawned {mob.key} (#{mob.id}) in {room.name}|n"
            )

        # Teleport to arena north
        caller.move_to(north, quiet=True)
        caller.msg("")
        caller.msg(caller.at_look(north))
        caller.msg(
            "\n|w=== Test Arena Ready ===|n\n"
            "  |yArena North|n: wandering rat (wanders every ~20s)\n"
            "  |yArena East|n:  patrolling guard (patrols all 4 rooms)\n"
            "  |yArena South|n: fierce wolf (chases 3 rooms on flee)\n"
            "  |yArena West|n:  empty (watch for arrivals)\n"
            "\n"
            "  Try: |wkill rat|n then |wflee|n to test chase.\n"
            "  Use |w@combatdebug|n to inspect state."
        )


# ---------------------------------------------------------------------------
# @spawnmob
# ---------------------------------------------------------------------------

class CmdSpawnMob(Command):
    """
    Spawn a test mob in your current room with auto-respawn.

    Usage:
        @spawnmob [name] [/wander] [/patrol] [/chase]

    Switches:
        /wander  - mob wanders to adjacent rooms randomly
        /patrol  - mob patrols (requires patrol route, placeholder for now)
        /chase   - mob chases fleeing players (up to 3 rooms)

    The room must not be safe. Default is "a training dummy".
    A respawn script is attached so the mob returns after death.

    Examples:
        @spawnmob a wandering rat /wander
        @spawnmob a guard /patrol
        @spawnmob a fierce wolf /chase
        @spawnmob a rabid dog /wander /chase
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

        # Parse switches from args
        args = self.args.strip()
        do_wander = False
        do_patrol = False
        do_chase = False

        parts = args.split()
        name_parts = []
        for part in parts:
            if part.lower() == "/wander":
                do_wander = True
            elif part.lower() == "/patrol":
                do_patrol = True
            elif part.lower() == "/chase":
                do_chase = True
            else:
                name_parts.append(part)

        name = " ".join(name_parts) if name_parts else "a training dummy"

        # Determine move mode
        if do_patrol:
            move_mode = "patrol"
        elif do_wander:
            move_mode = "wander"
        else:
            move_mode = "stationary"

        mob, script = spawn_and_track(
            room, name=name, move_mode=move_mode, chase=do_chase,
        )
        caller.msg(f"|gSpawned: {mob.key} (#{mob.id}) in {room.name}|n")
        caller.msg(f"|gRespawn script tracking {mob.dbref}.|n")

        mode_info = []
        if move_mode != "stationary":
            mode_info.append(f"mode={move_mode}")
        if do_chase:
            mode_info.append("chase=on")
        if mode_info:
            caller.msg(f"|gMovement: {', '.join(mode_info)}|n")


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
    Safe to run any time.
    """

    key = "@fixcombat"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"

    def func(self):
        caller = self.caller

        from evennia.scripts.models import ScriptDB

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
    Show the combat handler and mob spawner state for the current room.

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

        # Respawn script details
        respawns = room.scripts.get("MobRespawnScript")
        if respawns:
            for rs in respawns:
                lines.append(f"\n|w  --- MobRespawnScript (#{rs.id}) ---|n")
                lines.append(f"    mob_name: {rs.db.mob_name}")
                lines.append(f"    mob_dbref: {rs.db.mob_dbref}")
                lines.append(f"    is_mob_alive: {rs.is_mob_alive()}")
                lines.append(f"    tick_count: {rs.db.tick_count or 0}")
                lines.append(f"    interval: {rs.interval}s")
                lines.append(f"    is_active: {rs.is_active}")
                lines.append(f"    start_delay: {rs.start_delay}")
                lines.append(f"    last_alive_tick: {getattr(rs.db, 'last_alive_tick', '?')}")
                lines.append(f"    death_noticed_at: {getattr(rs.db, 'death_noticed_at', '?')}")
        else:
            lines.append("\n  |yNo MobRespawnScript on this room.|n")

        # Combat handler details
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
