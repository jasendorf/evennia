"""
Group combat commands
=====================

    assist <player>     -- join combat targeting the same mob as <player>
    rescue <player>     -- attempt to pull aggro off <player> onto yourself

These commands work with or without a party. Anyone can assist or
rescue anyone in the same room.

Depends on:
    contrib_dorfin.combat_handler.CombatHandler
    contrib_dorfin.combat_rules.check_rescue, RESCUE_COOLDOWN
"""

from evennia.commands.command import Command


class CmdAssist(Command):
    """
    Join combat targeting the same enemy as another player.

    Usage:
        assist <player>

    Joins the fight attacking whatever <player> is currently fighting.
    If you're already in combat, switches your target to match theirs.
    You don't need to be in a party to assist someone.

    Examples:
        assist Gandalf
        assist Legolas
    """

    key = "assist"
    aliases = ["aid"]
    help_category = "Combat"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Assist whom? Usage: |wassist <player>|n")
            return

        # Find the player in the room
        target_player = caller.search(args, location=caller.location, quiet=True)
        if not target_player:
            caller.msg(f"You don't see '{args}' here.")
            return
        if isinstance(target_player, list):
            # Prefer non-mob characters
            players = [t for t in target_player if not getattr(t.db, "is_mob", False)]
            target_player = players[0] if players else target_player[0]

        if target_player == caller:
            caller.msg("You can't assist yourself.")
            return

        # Target player must be in combat
        from contrib_dorfin.combat_handler import CombatHandler
        handler = CombatHandler.get_handler(caller.location)

        if not handler or not handler.is_in_combat(target_player):
            caller.msg(f"{target_player.name} is not in combat.")
            return

        # Find what they're attacking
        their_target = handler.get_target(target_player)
        if not their_target:
            caller.msg(f"{target_player.name} doesn't have a target.")
            return

        # Check safe room
        if getattr(caller.location.db, "is_safe", False):
            caller.msg("|yThis is a safe area. Combat is not permitted here.|n")
            return

        # Join or switch target
        already_fighting = handler.is_in_combat(caller)
        handler.add_combatant(caller, their_target)

        # Make sure the mob also targets the new combatant if it has no target
        if not handler.is_in_combat(their_target):
            handler.add_combatant(their_target, caller)

        target_name = their_target.get_display_name(caller) if hasattr(their_target, "get_display_name") else their_target.key

        if already_fighting:
            caller.msg(
                f"|gYou switch to assist |w{target_player.name}|g, "
                f"attacking {target_name}!|n"
            )
        else:
            caller.msg(
                f"|gYou leap to assist |w{target_player.name}|g, "
                f"attacking {target_name}!|n"
            )

        caller.location.msg_contents(
            f"|w{caller.name}|n assists |w{target_player.name}|n, "
            f"attacking {target_name}!",
            exclude=[caller],
        )


class CmdRescue(Command):
    """
    Attempt to draw a mob's aggro away from another player.

    Usage:
        rescue <player>

    Attempts to force the mob attacking <player> to switch its target
    to you instead. Success is based on your Strength and Charisma
    versus the mob's Wisdom and level.

    On success: the mob targets you for 2 combat rounds (aggro lock).
    On failure: you still join the fight targeting the mob (free assist).

    Rescue has a 15-second cooldown between attempts. You don't need
    to be in a party to rescue someone.

    Examples:
        rescue Frodo
        rescue Samwise
    """

    key = "rescue"
    aliases = ["taunt"]
    help_category = "Combat"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Rescue whom? Usage: |wrescue <player>|n")
            return

        # Check cooldown
        if hasattr(caller, "cooldowns") and caller.cooldowns:
            if not caller.cooldowns.ready("rescue"):
                remaining = caller.cooldowns.time_left("rescue", use_int=True)
                caller.msg(
                    f"|yYou can't rescue again yet. "
                    f"({remaining}s remaining)|n"
                )
                return

        # Find the player in the room
        target_player = caller.search(args, location=caller.location, quiet=True)
        if not target_player:
            caller.msg(f"You don't see '{args}' here.")
            return
        if isinstance(target_player, list):
            players = [t for t in target_player if not getattr(t.db, "is_mob", False)]
            target_player = players[0] if players else target_player[0]

        if target_player == caller:
            caller.msg("You can't rescue yourself.")
            return

        # Target player must be in combat
        from contrib_dorfin.combat_handler import CombatHandler
        handler = CombatHandler.get_handler(caller.location)

        if not handler or not handler.is_in_combat(target_player):
            caller.msg(f"{target_player.name} is not in combat.")
            return

        # Find mobs that are attacking the target player
        attackers = handler.get_opponents(target_player)
        mobs = [
            a for a in attackers
            if hasattr(a, "db") and getattr(a.db, "is_mob", False)
        ]

        if not mobs:
            caller.msg(
                f"No mobs are currently attacking {target_player.name}."
            )
            return

        # Pick the first mob to rescue from
        mob = mobs[0]
        mob_name = mob.get_display_name(caller) if hasattr(mob, "get_display_name") else mob.key

        # Check safe room
        if getattr(caller.location.db, "is_safe", False):
            caller.msg("|yThis is a safe area. Combat is not permitted here.|n")
            return

        # Set cooldown
        from contrib_dorfin.combat_rules import check_rescue, RESCUE_COOLDOWN
        if hasattr(caller, "cooldowns") and caller.cooldowns:
            caller.cooldowns.add("rescue", RESCUE_COOLDOWN)

        # Roll the rescue
        result = check_rescue(caller, mob)

        # Make sure caller is in the fight regardless of outcome
        if not handler.is_in_combat(caller):
            handler.add_combatant(caller, mob)

        if result["success"]:
            # Aggro lock: mob targets caller for 2 ticks
            handler.set_aggro_lock(mob, caller)
            handler.set_target(caller, mob)

            caller.msg(
                f"|g*** You rescue |w{target_player.name}|g! ***|n\n"
                f"|g{mob_name} turns its attention to you!|n"
            )
            target_player.msg(
                f"|g{caller.name} rescues you from {mob_name}!|n"
            )
            caller.location.msg_contents(
                f"|w{caller.name}|n rescues |w{target_player.name}|n "
                f"from {mob_name}!",
                exclude=[caller, target_player],
            )
        else:
            # Failed rescue — still assists
            handler.set_target(caller, mob)

            caller.msg(
                f"|yYou try to rescue |w{target_player.name}|y "
                f"but {mob_name} ignores your taunt!|n\n"
                f"|yYou attack {mob_name} instead.|n"
            )
            target_player.msg(
                f"|y{caller.name} tries to rescue you but fails.|n"
            )
            caller.location.msg_contents(
                f"|w{caller.name}|n tries to rescue |w{target_player.name}|n "
                f"but fails! They attack {mob_name} instead.",
                exclude=[caller, target_player],
            )
