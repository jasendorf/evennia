"""
Combat commands
===============

    kill/attack <target>     -- initiate combat against a mob
    flee                     -- attempt to escape combat
    consider/con <target>    -- gauge a mob's difficulty
    wimpy <hp>               -- set auto-flee threshold (0 to disable)
    score/stats              -- show character stats, HP, XP
    loot                     -- take items from a corpse

Rest and recovery commands are in command_rest.py (CmdRest) and
command_rent.py (CmdRentRoom). They are intentionally separate systems.

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

        # Trigger autoassist for party members
        _trigger_party_autoassist(caller, target, handler)


def _trigger_party_autoassist(attacker, target, handler):
    try:
        from contrib_dorfin.dorfin_party import trigger_party_autoassist
        trigger_party_autoassist(attacker, target, handler)
    except ImportError:
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

        from contrib_dorfin.combat_handler import CombatHandler
        handler = CombatHandler.get_handler(caller.location)

        if not handler or not handler.is_in_combat(caller):
            caller.msg("You're not in combat.")
            return

        from contrib_dorfin.combat_rules import check_flee
        opponents = handler.get_opponents(caller)
        result = check_flee(caller, opponents)

        if result["success"]:
            caller.msg("|gYou manage to disengage and flee!|n")
            caller.location.msg_contents(
                f"|y{caller.name} flees from combat!|n",
                exclude=[caller],
            )
            mob_opponents = [
                opp for opp in opponents
                if hasattr(opp, "db") and getattr(opp.db, "is_mob", False)
            ]
            handler.remove_combatant(caller)
            exit_used = handler._move_to_random_exit(caller)
            if exit_used:
                try:
                    from contrib_dorfin.mob_movement import trigger_chase
                    for mob in mob_opponents:
                        trigger_chase(mob, caller, exit_used)
                except ImportError:
                    pass
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
            caller.msg("Consider whom? Usage: consider <target>")
            return

        target = caller.search(args, location=caller.location, quiet=True)
        if not target:
            caller.msg(f"You don't see '{args}' here.")
            return
        if isinstance(target, list):
            mobs = [t for t in target if getattr(t.db, "is_mob", False)]
            target = mobs[0] if mobs else target[0]

        if not getattr(target.db, "is_mob", False):
            caller.msg("You can only consider mobs.")
            return

        from contrib_dorfin.combat_rules import consider_difficulty
        result = consider_difficulty(caller, target)
        target_name = target.get_display_name(caller)
        caller.msg(f"You size up {target_name}: |w{result}|n")


# ---------------------------------------------------------------------------
# wimpy
# ---------------------------------------------------------------------------

class CmdWimpy(Command):
    """
    Set your auto-flee HP threshold.

    Usage:
        wimpy <hp>
        wimpy 0

    When your HP drops to or below this value in combat, you will
    automatically attempt to flee. Set to 0 to disable.

    Example:
        wimpy 15    -- flee when HP reaches 15
        wimpy 0     -- never auto-flee
    """

    key = "wimpy"
    help_category = "Combat"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            current = caller.db.wimpy or 0
            if current:
                caller.msg(f"Wimpy is set to |w{current} HP|n.")
            else:
                caller.msg("Wimpy is disabled.")
            return

        try:
            value = int(args)
        except ValueError:
            caller.msg("Usage: wimpy <hp>")
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
# loot
# ---------------------------------------------------------------------------

class CmdLoot(Command):
    """
    Loot items from a corpse.

    Usage:
        loot                              -- loot everything from first corpse
        loot <corpse>                     -- loot everything from named corpse
        loot <item> from <corpse>         -- loot one item
        loot <N> <item> from <corpse>     -- loot N matching items
        loot all <item> from <corpse>     -- loot all matching items

    Without arguments, loots everything from the first corpse in the room.
    You can specify a particular corpse or a particular item.

    Examples:
        loot
        loot corpse
        loot dagger from corpse
        loot 2 coins from corpse
        loot all silk from corpse of goblin
    """

    key = "loot"
    aliases = []
    help_category = "Combat"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        from typeclasses.corpse import Corpse
        from commands.command_containers import _parse_quantity, _find_one, _find_n

        corpses = [
            obj for obj in caller.location.contents
            if isinstance(obj, Corpse)
        ]

        if not corpses:
            caller.msg("There are no corpses here to loot.")
            return

        item_text = None
        corpse_query = None

        if " from " in args.lower():
            parts = args.lower().split(" from ", 1)
            item_text = parts[0].strip()
            corpse_query = parts[1].strip()
        elif args:
            corpse_query = args.lower()

        if corpse_query:
            target_corpse = None
            for c in corpses:
                if corpse_query in c.key.lower():
                    target_corpse = c
                    break
            if not target_corpse:
                item_text = corpse_query
                corpse_query = None
                target_corpse = corpses[0]
        else:
            target_corpse = corpses[0]

        contents = [obj for obj in target_corpse.contents]

        if not contents:
            caller.msg(f"{target_corpse.key} is empty.")
            return

        if item_text:
            qty, item_query = _parse_quantity(item_text)

            if item_query is None:
                # "loot all from corpse" — take everything
                qty = "all"

            # Multiple items
            if qty != 1:
                if item_query:
                    matches = _find_n(caller, item_query, contents, qty)
                else:
                    matches = contents
                if not matches:
                    caller.msg(
                        f"You don't see '{item_query}' in {target_corpse.key}."
                    )
                    return
                taken = []
                for obj in list(matches):
                    obj.move_to(caller, quiet=True)
                    taken.append(obj.key)
                if taken:
                    caller.msg(
                        f"|gYou take {len(taken)}x from {target_corpse.key}: "
                        f"|w{', '.join(taken)}|n"
                    )
                    caller.location.msg_contents(
                        f"|w{caller.name}|n takes items from {target_corpse.key}.",
                        exclude=[caller],
                    )
                return

            # Single item
            match = _find_one(caller, item_query, contents)
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
            taken = []
            for obj in contents:
                obj.move_to(caller, quiet=True)
                taken.append(obj.key)
            if taken:
                item_list = ", ".join(taken)
                caller.msg(f"|gYou loot {target_corpse.key}: |w{item_list}|n")
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

    Shows your health, base stats, experience, level, class, race,
    weapon skills, combat stats, currency, and active buffs.

    See also: skills (detailed weapon skill view)
    """

    key = "score"
    aliases = ["stats", "sc"]
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        level = caller.db.level or 1

        # Header with class/race
        char_class = getattr(caller.db, "char_class", None) or ""
        race = getattr(caller.db, "race", None) or ""
        identity = " ".join(p for p in [race.replace("_", " ").title(), char_class.title()] if p)
        subtitle = f"Level {level} {identity}" if identity else f"Level {level}"

        lines = [
            f"|w{'=' * 50}|n",
            f"|w  {caller.name}|n   {subtitle}",
            f"|w{'=' * 50}|n",
        ]

        hp = caller.get_hp() if hasattr(caller, "get_hp") else 100
        hp_max = caller.get_hp_max() if hasattr(caller, "get_hp_max") else 100
        hp_bar = _render_bar(hp, hp_max)
        hp_color = "|g" if hp > hp_max * 0.5 else ("|y" if hp > hp_max * 0.25 else "|r")
        lines.append(f"  Health:  {hp_bar} {hp_color}{hp}/{hp_max}|n")

        xp = caller.db.xp or 0
        from contrib_dorfin.combat_config import CHARACTER_LEVEL_XP, MAX_CHARACTER_LEVEL
        if level >= MAX_CHARACTER_LEVEL:
            lines.append(f"  XP:      |w{xp}|n (|cMAX LEVEL|n)")
        else:
            xp_current_level = CHARACTER_LEVEL_XP[level]
            xp_next_level = CHARACTER_LEVEL_XP[level + 1]
            xp_into_level = xp - xp_current_level
            xp_needed = xp_next_level - xp_current_level
            xp_bar = _render_bar(xp_into_level, xp_needed)
            lines.append(
                f"  XP:      {xp_bar} |w{xp_into_level}/{xp_needed}|n to level {level + 1}"
            )

        unspent = caller.db.unspent_stat_points or 0
        if unspent > 0:
            lines.append(
                f"  |y  {unspent} unspent stat point{'s' if unspent != 1 else ''}"
                f" — use |wtrain <stat>|n"
            )

        lines.append(f"  Purse:   |y{caller.money_string()}|n")

        # --- Stats ---
        lines.append(f"\n|w  {'--- Stats ---':^46}|n")

        stat_names = {
            "str": "STR", "dex": "DEX", "agi": "AGI", "con": "CON",
            "end": "END", "int": "INT", "wis": "WIS", "per": "PER",
            "cha": "CHA", "lck": "LCK",
        }

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

        # --- Derived Combat Stats ---
        lines.append(f"\n|w  {'--- Combat ---':^46}|n")
        con = caller.get_stat("con") if hasattr(caller, "get_stat") else 10
        lck = caller.get_stat("lck") if hasattr(caller, "get_stat") else 10
        dr = max(0, (con - 10) // 2)
        base_crit = lck // 2
        lines.append(f"  Damage Reduction: |w{dr}|n    Crit Chance: |w{base_crit}%|n")

        # --- Weapon Skills (compact) ---
        weapon_skills = caller.db.weapon_skills or {}
        trained = {cat: data for cat, data in weapon_skills.items()
                   if data.get("level", 0) > 0 or data.get("xp", 0) > 0}
        if trained:
            from contrib_dorfin.combat_config import (
                WEAPON_SKILL_XP_THRESHOLDS, MAX_WEAPON_SKILL_LEVEL,
            )
            lines.append(f"\n|w  {'--- Weapon Skills ---':^46}|n")
            for cat in sorted(trained.keys()):
                data = trained[cat]
                sk_level = data.get("level", 0)
                sk_xp = data.get("xp", 0)
                if sk_level >= MAX_WEAPON_SKILL_LEVEL:
                    progress = "|cMAX|n"
                else:
                    xp_cur = WEAPON_SKILL_XP_THRESHOLDS[sk_level]
                    xp_nxt = WEAPON_SKILL_XP_THRESHOLDS[sk_level + 1]
                    xp_into = sk_xp - xp_cur
                    xp_need = xp_nxt - xp_cur
                    pct = int(100 * xp_into / xp_need) if xp_need > 0 else 0
                    progress = f"{pct}%"
                lines.append(f"  {cat:<12} Lv |w{sk_level:>2}|n  ({progress})")

        if hasattr(caller, "needs"):
            lines.append(f"\n|w  {'--- Needs ---':^46}|n")
            needs_display = caller.needs.display()
            if needs_display:
                lines.append(needs_display)

        wimpy = caller.db.wimpy or 0
        if wimpy > 0:
            lines.append(f"\n  Wimpy:   |y{wimpy} HP|n")

        if getattr(caller.db, "in_combat", False):
            lines.append(f"\n  |r** IN COMBAT **|n")

        lines.append(f"|w{'=' * 50}|n")
        caller.msg("\n".join(lines))


# ---------------------------------------------------------------------------
# train
# ---------------------------------------------------------------------------

TRAINABLE_STATS = {"str", "dex", "agi", "con", "end", "int", "wis", "per", "cha", "lck"}

STAT_FULL_NAMES = {
    "str": "Strength", "dex": "Dexterity", "agi": "Agility",
    "con": "Constitution", "end": "Endurance", "int": "Intelligence",
    "wis": "Wisdom", "per": "Perception", "cha": "Charisma", "lck": "Luck",
}


class CmdTrain(Command):
    """
    Spend stat points to permanently increase a base stat.

    Usage:
        train <stat>
        train str
        train con

    You earn stat points at every 5th character level (5, 10, 15, ..., 90).
    Each point permanently raises the chosen stat by 1.

    Valid stats: STR, DEX, AGI, CON, END, INT, WIS, PER, CHA, LCK
    """

    key = "train"
    aliases = ["spend"]
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip().lower()

        unspent = caller.db.unspent_stat_points or 0

        if not args:
            if unspent > 0:
                caller.msg(
                    f"|wYou have {unspent} unspent stat point"
                    f"{'s' if unspent != 1 else ''}.|n\n"
                    f"Usage: |wtrain <stat>|n  (e.g. |wtrain str|n)\n"
                    f"Stats: {', '.join(s.upper() for s in sorted(TRAINABLE_STATS))}"
                )
            else:
                caller.msg("You have no unspent stat points.")
            return

        if args not in TRAINABLE_STATS:
            caller.msg(
                f"'{args}' is not a valid stat. Choose from: "
                f"{', '.join(s.upper() for s in sorted(TRAINABLE_STATS))}"
            )
            return

        if unspent <= 0:
            caller.msg("You have no unspent stat points. Level up to earn more.")
            return

        # Apply the stat increase
        if not hasattr(caller, "traits") or not caller.traits:
            caller.msg("Trait system unavailable.")
            return

        trait = caller.traits.get(args)
        if not trait:
            caller.msg(f"Cannot find trait '{args}'.")
            return

        old_val = trait.base
        trait.base += 1
        new_val = trait.base
        caller.db.unspent_stat_points = unspent - 1
        remaining = caller.db.unspent_stat_points

        stat_name = STAT_FULL_NAMES.get(args, args.upper())
        caller.msg(
            f"|g{stat_name} increased from {old_val} to |w{new_val}|g!|n"
            f" ({remaining} stat point{'s' if remaining != 1 else ''} remaining)"
        )

        # If they raised CON, update HP max retroactively for current level
        # (future levels will use the new CON automatically)
        if args == "con":
            caller.msg("|xNote: Future level-ups will benefit from your higher CON.|n")


# ---------------------------------------------------------------------------
# skills — detailed weapon skill view
# ---------------------------------------------------------------------------

class CmdSkills(Command):
    """
    Show your weapon skills in detail with milestones.

    Usage:
        skills
        skills <category>

    Without arguments, lists all weapon categories you've trained.
    With a category name, shows XP progress, active perks, and
    upcoming milestones for that weapon type.

    Examples:
        skills
        skills sword
        skills bow
    """

    key = "skills"
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip().lower()

        from contrib_dorfin.combat_config import (
            WEAPON_CATEGORIES, WEAPON_SKILL_XP_THRESHOLDS,
            MAX_WEAPON_SKILL_LEVEL, WEAPON_MILESTONES,
        )

        weapon_skills = caller.db.weapon_skills or {}

        if args:
            # Detailed view for one category
            if args not in WEAPON_CATEGORIES:
                caller.msg(
                    f"'{args}' is not a weapon category. Valid: "
                    f"{', '.join(WEAPON_CATEGORIES)}"
                )
                return

            data = weapon_skills.get(args, {"xp": 0, "level": 0})
            sk_level = data.get("level", 0)
            sk_xp = data.get("xp", 0)

            lines = [f"|w=== {args.title()} Skill ===|n"]

            # Level + XP bar
            if sk_level >= MAX_WEAPON_SKILL_LEVEL:
                lines.append(f"  Level: |w{sk_level}|n / {MAX_WEAPON_SKILL_LEVEL} (|cMAX|n)")
                lines.append(f"  Total XP: |w{sk_xp}|n")
            else:
                xp_cur = WEAPON_SKILL_XP_THRESHOLDS[sk_level]
                xp_nxt = WEAPON_SKILL_XP_THRESHOLDS[sk_level + 1]
                xp_into = sk_xp - xp_cur
                xp_need = xp_nxt - xp_cur
                bar = _render_bar(xp_into, xp_need)
                lines.append(f"  Level: |w{sk_level}|n / {MAX_WEAPON_SKILL_LEVEL}")
                lines.append(f"  XP:    {bar} |w{xp_into}/{xp_need}|n to level {sk_level + 1}")

            # Per-level bonuses
            atk_bonus = sk_level
            dmg_bonus = sk_level // 2
            lines.append(f"  Bonuses: +{atk_bonus} attack, +{dmg_bonus} damage")

            # Milestones
            milestones = WEAPON_MILESTONES.get(args, [])
            if milestones:
                lines.append(f"\n|w  Milestones:|n")
                for lvl, effect_type, value, name in milestones:
                    if sk_level >= lvl:
                        lines.append(f"  |g  [{lvl:>2}] {name}|n — {_describe_effect(effect_type, value)}")
                    else:
                        lines.append(f"  |x  [{lvl:>2}] {name}|n — |x{_describe_effect(effect_type, value)}|n")

            # Proficiency
            char_class = getattr(caller.db, "char_class", None)
            if char_class:
                from contrib_dorfin.combat_config import CLASS_PROFICIENCIES, CLASS_OPPOSED
                cls = char_class.lower()
                opposed = CLASS_OPPOSED.get(cls, [])
                proficient = CLASS_PROFICIENCIES.get(cls, [])
                if args in opposed:
                    lines.append(f"\n  |rOpposed|n — {char_class}s suffer -25 attack, -5 damage")
                elif args in proficient:
                    lines.append(f"\n  |gProficient|n — no penalties")
                else:
                    lines.append(f"\n  |yUnfamiliar|n — {char_class}s suffer -15 attack, -3 damage")

            caller.msg("\n".join(lines))
            return

        # Summary view — all categories
        trained = {cat: data for cat, data in weapon_skills.items()
                   if data.get("level", 0) > 0 or data.get("xp", 0) > 0}

        if not trained:
            caller.msg(
                "You haven't trained any weapon skills yet.\n"
                "Fight with a weapon to gain skill XP. Use |wskills <category>|n "
                "to see details for any weapon type."
            )
            return

        lines = [f"|w{'=' * 40}|n", f"|w  Weapon Skills|n", f"|w{'=' * 40}|n"]

        for cat in sorted(trained.keys()):
            data = trained[cat]
            sk_level = data.get("level", 0)
            sk_xp = data.get("xp", 0)

            if sk_level >= MAX_WEAPON_SKILL_LEVEL:
                progress = "|cMAX|n"
            else:
                xp_cur = WEAPON_SKILL_XP_THRESHOLDS[sk_level]
                xp_nxt = WEAPON_SKILL_XP_THRESHOLDS[sk_level + 1]
                xp_into = sk_xp - xp_cur
                xp_need = xp_nxt - xp_cur
                pct = int(100 * xp_into / xp_need) if xp_need > 0 else 0
                bar = _render_bar(xp_into, xp_need, width=10)
                progress = f"{bar} {pct}%"

            # Count active milestones
            milestones = WEAPON_MILESTONES.get(cat, [])
            active = sum(1 for lvl, *_ in milestones if sk_level >= lvl)
            total = len(milestones)

            lines.append(
                f"  {cat:<12} Lv |w{sk_level:>2}|n  {progress}"
                f"  |x({active}/{total} perks)|n"
            )

        lines.append(f"|w{'=' * 40}|n")
        lines.append("Use |wskills <category>|n for details.")
        caller.msg("\n".join(lines))


def _describe_effect(effect_type, value):
    """Human-readable description of a milestone effect."""
    descriptions = {
        "passive_initiative": f"+{value} initiative",
        "passive_accuracy": f"+{value} accuracy",
        "passive_defense": f"+{value} defense",
        "passive_damage": f"+{value} damage",
        "passive_block": f"{value}% parry chance",
        "crit_chance_bonus": f"+{value}% crit chance",
        "crit_multiplier": f"x{value} crit damage",
        "armor_ignore_pct": f"ignore {value}% armor",
        "execute_threshold": f"+50% damage vs targets below {value}% HP",
        "stun_chance": f"{value}% stun chance",
        "bonus_attack_chance": f"{value}% bonus attack",
        "riposte_chance": f"{value}% counter on enemy miss",
        "backstab_multiplier": f"x{value} first attack damage",
        "damage_reduction_chance": f"{value}% chance to debuff target damage",
        "on_kill_cleave": f"on kill: {value}% damage to another enemy",
        "on_kill_attack_all": "on kill: attack all remaining enemies",
        "first_round_attack_all": "first round: attack all enemies",
        "first_attack_defense": f"+{value} defense until first hit taken",
        "unarmed_dice_upgrade": "unarmed dice upgrade (1d4 -> 1d6)",
    }
    if effect_type == "berserker":
        return f"+{value[0]} damage, -{value[1]} defense"
    if effect_type == "bleed":
        return f"{value[0]} damage/round for {value[1]} rounds"
    if effect_type == "armor_shatter":
        return f"reduce target armor by {value}"
    if effect_type == "defense_shatter":
        return f"{value[0]}% chance to reduce enemy defense by {value[1]}"
    return descriptions.get(effect_type, f"{effect_type}: {value}")


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _render_bar(current, maximum, width=20):
    """Simple ASCII health bar."""
    if maximum <= 0:
        return "[" + "-" * width + "]"
    filled = int(width * current / maximum)
    filled = max(0, min(width, filled))
    bar = "|g" + "#" * filled + "|x" + "-" * (width - filled) + "|n"
    return "[" + bar + "]"