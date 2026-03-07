"""
Combat commands
===============

    kill/attack <target>     -- initiate combat against a mob
    flee                     -- attempt to escape combat
    consider/con <target>    -- gauge a mob's difficulty
    wimpy <hp>               -- set auto-flee threshold (0 to disable)
    rest                     -- recover HP outside of combat
    score/stats              -- show character stats, HP, XP

Depends on:
    contrib_dorfin.combat_handler.CombatHandler
    contrib_dorfin.combat_rules
    typeclasses.mobs.AwtownMob
"""

from evennia.commands.command import Command


# ---------------------------------------------------------------------------
# kill / attack
# ---------------------------------------------------------------------------

class CmdKill(Command):
    """
    Attack a target, initiating combat.

    Usage:
        kill <target>
        attack <target>
        k <target>

    Starts combat with the named mob or creature. If combat is already
    underway in this room, you join the existing fight. If you are
    already in combat, this switches your target.

    You cannot attack NPCs that are not mobs (shopkeepers, trainers, etc.).
    PvP is not enabled in this phase.

    Examples:
        kill goblin
        attack troll
        k rat
    """

    key = "kill"
    aliases = ["attack", "k"]
    help_category = "Combat"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Kill what? Usage: kill <target>")
            return

        # Find target in the room
        target = caller.search(args, location=caller.location, quiet=True)
        if not target:
            caller.msg(f"You don't see '{args}' here.")
            return
        if isinstance(target, list):
            # Prefer mobs over other objects
            mobs = [t for t in target if getattr(t.db, "is_mob", False)]
            target = mobs[0] if mobs else target[0]

        # Can't attack yourself
        if target == caller:
            caller.msg("You can't attack yourself.")
            return

        # Must be a mob
        if not getattr(target.db, "is_mob", False):
            # Check if it's an NPC
            if getattr(target.db, "is_npc", False):
                caller.msg(
                    f"You can't attack {target.get_display_name(caller)}. "
                    f"They're not hostile."
                )
            else:
                caller.msg(f"You can't attack that.")
            return

        # Check if mob is alive
        if hasattr(target, "is_alive") and not target.is_alive():
            caller.msg(f"{target.get_display_name(caller)} is already dead.")
            return

        # Check safe room
        if getattr(caller.location.db, "is_safe", False):
            caller.msg(
                "|yThis is a safe area. Combat is not permitted here.|n"
            )
            return

        # Get or create combat handler
        from contrib_dorfin.combat_handler import CombatHandler
        handler = CombatHandler.get_or_create(caller.location)

        already_fighting = handler.is_in_combat(caller)

        # Add attacker to combat
        handler.add_combatant(caller, target)

        # Add mob to combat (targeting attacker, unless it has an aggro lock)
        if not handler.is_in_combat(target):
            handler.add_combatant(target, caller)

        # Messages
        target_name = target.get_display_name(caller)
        if already_fighting:
            caller.msg(f"|rYou switch your attack to {target_name}!|n")
            caller.location.msg_contents(
                f"|w{caller.name}|n turns to attack {target_name}!",
                exclude=[caller],
            )
        else:
            caller.msg(f"|rYou attack {target_name}!|n")
            caller.location.msg_contents(
                f"|w{caller.name}|n attacks {target_name}!",
                exclude=[caller],
            )

        # Trigger autoassist for party members (hook for Chunk 6)
        _trigger_party_autoassist(caller, target, handler)


def _trigger_party_autoassist(attacker, target, handler):
    """
    Hook for the party system. Checks if the attacker is in a party
    and has party members in the room with autoassist enabled.

    Does nothing until the party system is wired in (Chunk 6).
    """
    # Phase 5: no-op. Phase 6 will replace this with real party logic.
    pass


# ---------------------------------------------------------------------------
# flee
# ---------------------------------------------------------------------------

class CmdFlee(Command):
    """
    Attempt to flee from combat.

    Usage:
        flee

    Makes a check based on your Agility and Luck against your opponents'
    Perception. On success, you escape through a random exit. On failure,
    you lose your attack this round but remain in combat.

    You cannot flee if you are not in combat.
    """

    key = "flee"
    aliases = ["retreat", "run"]
    help_category = "Combat"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller

        # Must be in combat
        from contrib_dorfin.combat_handler import CombatHandler
        handler = CombatHandler.get_handler(caller.location)

        if not handler or not handler.is_in_combat(caller):
            caller.msg("You're not in combat.")
            return

        # Roll flee check
        from contrib_dorfin.combat_rules import check_flee
        opponents = handler.get_opponents(caller)
        result = check_flee(caller, opponents)

        if result["success"]:
            caller.msg("|gYou manage to disengage and flee!|n")
            caller.location.msg_contents(
                f"|y{caller.name} flees from combat!|n",
                exclude=[caller],
            )
            handler.remove_combatant(caller)
            handler._move_to_random_exit(caller)
        else:
            caller.msg(
                f"|rYou try to flee but can't break free! "
                f"(Flee chance: {result['flee_chance']}%)|n"
            )
            caller.location.msg_contents(
                f"|w{caller.name}|n tries to flee but fails!",
                exclude=[caller],
            )


# ---------------------------------------------------------------------------
# consider
# ---------------------------------------------------------------------------

class CmdConsider(Command):
    """
    Gauge a target's strength relative to yours.

    Usage:
        consider <target>
        con <target>

    Gives a qualitative assessment of how difficult a fight with the
    target would be. This can be used in or out of combat.

    Examples:
        consider goblin
        con troll
    """

    key = "consider"
    aliases = ["con"]
    help_category = "Combat"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Consider what? Usage: consider <target>")
            return

        target = caller.search(args, location=caller.location, quiet=True)
        if not target:
            caller.msg(f"You don't see '{args}' here.")
            return
        if isinstance(target, list):
            mobs = [t for t in target if getattr(t.db, "is_mob", False)]
            target = mobs[0] if mobs else target[0]

        from contrib_dorfin.combat_rules import get_consider_message
        message = get_consider_message(caller, target)
        caller.msg(f"|c{message}|n")


# ---------------------------------------------------------------------------
# wimpy
# ---------------------------------------------------------------------------

class CmdWimpy(Command):
    """
    Set your auto-flee HP threshold.

    Usage:
        wimpy <hp>
        wimpy 0
        wimpy

    When your HP drops to or below your wimpy threshold during combat,
    you will automatically attempt to flee. Set to 0 to disable.

    Without arguments, shows your current wimpy setting.

    Examples:
        wimpy 30       -- auto-flee when HP drops to 30
        wimpy 0        -- disable auto-flee
        wimpy          -- check current setting
    """

    key = "wimpy"
    help_category = "Combat"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            current = caller.db.wimpy or 0
            if current > 0:
                caller.msg(f"|wWimpy:|n {current} HP (auto-flee when HP drops to {current})")
            else:
                caller.msg("|wWimpy:|n disabled")
            return

        try:
            value = int(args)
        except ValueError:
            caller.msg("Wimpy must be a number. Usage: wimpy <hp>")
            return

        if value < 0:
            value = 0

        hp_max = caller.get_hp_max() if hasattr(caller, "get_hp_max") else 100
        if value >= hp_max:
            caller.msg(
                f"That's higher than your max HP ({hp_max}). "
                f"Set wimpy to a lower value."
            )
            return

        caller.db.wimpy = value

        if value > 0:
            caller.msg(f"|gWimpy set to {value} HP.|n You will auto-flee at {value} HP.")
        else:
            caller.msg("|yWimpy disabled.|n You will not auto-flee.")


# ---------------------------------------------------------------------------
# rest
# ---------------------------------------------------------------------------

class CmdRest(Command):
    """
    Rest to recover health.

    Usage:
        rest

    Resting restores your HP to full over a short time. You cannot
    rest while in combat. Resting is interrupted if you enter combat
    or move to another room.
    """

    key = "rest"
    aliases = ["recover"]
    help_category = "Combat"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller

        # Can't rest in combat
        if getattr(caller.db, "in_combat", False):
            caller.msg("You can't rest while in combat!")
            return

        from contrib_dorfin.combat_handler import CombatHandler
        handler = CombatHandler.get_handler(caller.location)
        if handler and handler.is_in_combat(caller):
            caller.msg("You can't rest while in combat!")
            return

        # Check if already at full HP
        current_hp = caller.get_hp() if hasattr(caller, "get_hp") else 100
        max_hp = caller.get_hp_max() if hasattr(caller, "get_hp_max") else 100

        if current_hp >= max_hp:
            caller.msg("You are already at full health.")
            return

        # Heal to full
        amount = max_hp - current_hp
        if hasattr(caller, "heal"):
            caller.heal(amount)

        caller.msg(
            f"|gYou sit down and rest for a moment...\n"
            f"You feel refreshed. Health restored to {max_hp}/{max_hp}.|n"
        )
        caller.location.msg_contents(
            f"|w{caller.name}|n sits down to rest.",
            exclude=[caller],
        )


# ---------------------------------------------------------------------------
# loot
# ---------------------------------------------------------------------------

class CmdLoot(Command):
    """
    Loot items from a corpse.

    Usage:
        loot
        loot <corpse>
        loot <item> from <corpse>
        get <item> from <corpse>

    Without arguments, loots everything from the first corpse in the room.
    You can specify a particular corpse or a particular item.

    Examples:
        loot
        loot corpse
        loot dagger from corpse
        loot spider silk from corpse of goblin
    """

    key = "loot"
    aliases = []
    help_category = "Combat"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        # Find all corpses in the room
        from typeclasses.corpse import Corpse
        corpses = [
            obj for obj in caller.location.contents
            if isinstance(obj, Corpse)
        ]

        if not corpses:
            caller.msg("There are no corpses here to loot.")
            return

        # Parse "item from corpse" syntax
        item_query = None
        corpse_query = None

        if " from " in args.lower():
            parts = args.lower().split(" from ", 1)
            item_query = parts[0].strip()
            corpse_query = parts[1].strip()
        elif args:
            # Could be a corpse name or an item name — try corpse first
            corpse_query = args.lower()

        # Find the target corpse
        if corpse_query:
            target_corpse = None
            for c in corpses:
                if corpse_query in c.key.lower():
                    target_corpse = c
                    break
            if not target_corpse:
                # Maybe args is an item name, not a corpse name.
                # Try to find the item in any corpse.
                item_query = corpse_query
                corpse_query = None
                target_corpse = corpses[0]
        else:
            target_corpse = corpses[0]

        # Get contents of the target corpse
        contents = [obj for obj in target_corpse.contents]

        if not contents:
            caller.msg(f"{target_corpse.key} is empty.")
            return

        if item_query:
            # Loot a specific item
            match = None
            for obj in contents:
                if item_query in obj.key.lower():
                    match = obj
                    break
            if not match:
                caller.msg(
                    f"You don't see '{item_query}' in {target_corpse.key}."
                )
                return
            match.move_to(caller, quiet=True)
            caller.msg(f"|gYou take |w{match.key}|g from {target_corpse.key}.|n")
            caller.location.msg_contents(
                f"|w{caller.name}|n takes {match.key} from {target_corpse.key}.",
                exclude=[caller],
            )
        else:
            # Loot everything
            taken = []
            for obj in contents:
                obj.move_to(caller, quiet=True)
                taken.append(obj.key)
            if taken:
                item_list = ", ".join(taken)
                caller.msg(
                    f"|gYou loot {target_corpse.key}: |w{item_list}|n"
                )
                caller.location.msg_contents(
                    f"|w{caller.name}|n loots {target_corpse.key}.",
                    exclude=[caller],
                )
            else:
                caller.msg(f"{target_corpse.key} is empty.")


# ---------------------------------------------------------------------------
# score / stats
# ---------------------------------------------------------------------------

class CmdScore(Command):
    """
    Display your character information.

    Usage:
        score
        stats
        sc

    Shows your health, base stats, experience, level, currency,
    hunger/thirst, and active buffs.
    """

    key = "score"
    aliases = ["stats", "sc"]
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller

        # Header
        lines = [
            f"|w{'=' * 50}|n",
            f"|w  {caller.name}|n   Level {caller.db.level or 1}",
            f"|w{'=' * 50}|n",
        ]

        # HP
        hp = caller.get_hp() if hasattr(caller, "get_hp") else 100
        hp_max = caller.get_hp_max() if hasattr(caller, "get_hp_max") else 100
        hp_bar = _render_bar(hp, hp_max)
        hp_color = "|g" if hp > hp_max * 0.5 else ("|y" if hp > hp_max * 0.25 else "|r")
        lines.append(f"  Health:  {hp_bar} {hp_color}{hp}/{hp_max}|n")

        # XP
        xp = caller.db.xp or 0
        lines.append(f"  XP:      |w{xp}|n")

        # Currency
        copper = caller.db.copper or 0
        lines.append(f"  Copper:  |y{copper}|n")

        # Stats
        lines.append(f"\n|w  {'--- Stats ---':^46}|n")

        stat_names = {
            "str": "STR", "dex": "DEX", "agi": "AGI", "con": "CON",
            "end": "END", "int": "INT", "wis": "WIS", "per": "PER",
            "cha": "CHA", "lck": "LCK",
        }

        # Display in two columns
        stat_keys = list(stat_names.keys())
        for i in range(0, len(stat_keys), 2):
            left_key = stat_keys[i]
            left_val = caller.get_stat(left_key) if hasattr(caller, "get_stat") else 10
            left_str = f"  {stat_names[left_key]}: {left_val:>3}"

            if i + 1 < len(stat_keys):
                right_key = stat_keys[i + 1]
                right_val = caller.get_stat(right_key) if hasattr(caller, "get_stat") else 10
                right_str = f"    {stat_names[right_key]}: {right_val:>3}"
            else:
                right_str = ""

            lines.append(f"{left_str:<25}{right_str}")

        # Needs (hunger/thirst)
        if hasattr(caller, "needs"):
            lines.append(f"\n|w  {'--- Needs ---':^46}|n")
            needs_display = caller.needs.display()
            if needs_display:
                lines.append(needs_display)

        # Wimpy
        wimpy = caller.db.wimpy or 0
        if wimpy > 0:
            lines.append(f"\n  Wimpy:   |y{wimpy} HP|n")

        # Combat status
        if getattr(caller.db, "in_combat", False):
            lines.append(f"\n  |r** IN COMBAT **|n")

        lines.append(f"|w{'=' * 50}|n")
        caller.msg("\n".join(lines))


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _render_bar(current, maximum, width=20):
    """Simple ASCII health bar."""
    if maximum <= 0:
        ratio = 0
    else:
        ratio = max(0.0, min(1.0, current / maximum))
    filled = int(ratio * width)
    return "[" + "|" * filled + "-" * (width - filled) + "]"
