"""
Equipment commands
==================

    wield <item>        -- equip a weapon or shield from inventory
    unwield [slot]      -- unequip weapon or offhand
    eq / equipment      -- show all equipment slots

These commands handle weapons only. Clothing (wear/remove) is handled
by ClothedCharacterCmdSet from evennia.contrib.game_systems.clothing.

Depends on:
    typeclasses.characters.AwtownCharacter  -- equip()/unequip()/get_equipped()
    typeclasses.items.AwtownWeapon          -- db.slot, db.damage_dice
"""

from evennia.commands.command import Command
from evennia.utils.utils import list_to_string


class CmdWield(Command):
    """
    Wield a weapon from your inventory.

    Usage:
        wield <weapon>
        wield <weapon> offhand
        wield all

    Equips the named weapon into your weapon slot (or offhand if specified).
    ``wield all`` auto-equips the first main-hand weapon and first
    offhand weapon/shield found in your inventory.

    You must be carrying the item.

    Examples:
        wield short sword
        wield dagger offhand
        wield all
    """

    key = "wield"
    aliases = ["hold"]
    help_category = "Equipment"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Wield what?")
            return

        from typeclasses.items import AwtownWeapon

        # "wield all" — auto-equip weapon + offhand
        if args.lower() == "all":
            self._wield_all(caller, AwtownWeapon)
            return

        # Parse optional "offhand" suffix
        slot = "weapon"
        if args.lower().endswith(" offhand"):
            slot = "offhand"
            args = args[:-8].strip()

        # Find item in inventory
        item = caller.search(args, location=caller, quiet=True)
        if not item:
            caller.msg(f"You aren't carrying '{args}'.")
            return
        if isinstance(item, list):
            if len(item) > 1:
                unique_keys = set(i.key for i in item)
                if len(unique_keys) > 1:
                    caller.msg(f"Which one? {list_to_string(list(unique_keys))}")
                    return
            item = item[0]

        # Must be a weapon
        if not isinstance(item, AwtownWeapon):
            caller.msg(f"{item.key} is not a weapon.")
            return

        # Read weapon properties
        item_wtype = getattr(item.db, "weapon_type", "melee") or "melee"
        item_hands = getattr(item.db, "hands", 1) or 1

        # --- Shield → force offhand ---
        if item_wtype == "shield":
            slot = "offhand"

        # --- Two-handed weapon → both slots ---
        if item_hands == 2:
            # Clear offhand if occupied
            current_off = caller.get_equipped("offhand")
            if current_off:
                caller.unequip("offhand")
                caller.msg(f"You lower {current_off.key}.")

            # Clear main hand if occupied
            current_main = caller.get_equipped("weapon")
            if current_main:
                caller.unequip("weapon")
                caller.msg(f"You lower {current_main.key}.")

            caller.equip("weapon", item)
            caller.equip("offhand", item)
            caller.msg(f"You grip |w{item.key}|n with both hands.")
            caller.location.msg_contents(
                f"|w{caller.name}|n wields {item.key} in both hands.",
                exclude=caller,
            )
            return

        # --- Block offhand equip when 2H is wielded ---
        if slot == "weapon":
            slot = item.db.slot or "weapon"
        if slot == "offhand":
            current_main = caller.get_equipped("weapon")
            if current_main:
                main_hands = getattr(current_main.db, "hands", 1) or 1
                if main_hands == 2:
                    caller.msg(
                        f"You must unwield {current_main.key} first "
                        f"(two-handed weapon)."
                    )
                    return

        # --- Standard 1H equip ---
        current = caller.get_equipped(slot)
        if current:
            caller.unequip(slot)
            caller.msg(f"You lower {current.key}.")

        caller.equip(slot, item)
        slot_label = "off hand" if slot == "offhand" else "main hand"
        caller.msg(f"You wield |w{item.key}|n in your {slot_label}.")
        caller.location.msg_contents(
            f"|w{caller.name}|n wields {item.key}.",
            exclude=caller
        )

    def _wield_all(self, caller, AwtownWeapon):
        """Auto-equip a main-hand weapon and an offhand weapon/shield."""
        weapons = [
            obj for obj in caller.contents
            if isinstance(obj, AwtownWeapon)
        ]

        if not weapons:
            caller.msg("You aren't carrying any weapons.")
            return

        wielded = []

        # Categorize weapons
        shields = [w for w in weapons if (getattr(w.db, "weapon_type", "melee") or "melee") == "shield"]
        two_handers = [w for w in weapons if (getattr(w.db, "hands", 1) or 1) == 2]
        one_handers = [w for w in weapons if w not in shields and w not in two_handers]

        # Prefer 1H main + shield/offhand over 2H
        main_candidates = [w for w in one_handers if (w.db.slot or "weapon") == "weapon"]
        if not main_candidates:
            main_candidates = one_handers

        if main_candidates:
            # Equip 1H main hand
            main_item = main_candidates[0]
            current = caller.get_equipped("weapon")
            if current and current != main_item:
                caller.unequip("weapon")
            # Clear offhand too if it was 2H
            current_off = caller.get_equipped("offhand")
            if current_off and current_off == current:
                caller.unequip("offhand")
            if not caller.get_equipped("weapon") or caller.get_equipped("weapon") != main_item:
                caller.equip("weapon", main_item)
                wielded.append(f"|w{main_item.key}|n (main hand)")

            # Equip offhand — prefer shields, then other 1H
            already_wielded = caller.get_equipped("weapon")
            off_choices = shields + [w for w in one_handers if w != already_wielded]
            off_choices = [w for w in off_choices if w != already_wielded]

            if off_choices:
                off_item = off_choices[0]
                current_off = caller.get_equipped("offhand")
                if current_off and current_off != off_item:
                    caller.unequip("offhand")
                if not caller.get_equipped("offhand") or caller.get_equipped("offhand") != off_item:
                    caller.equip("offhand", off_item)
                    off_label = "off hand"
                    wielded.append(f"|w{off_item.key}|n ({off_label})")

        elif two_handers:
            # No 1H available, use a 2H weapon
            main_item = two_handers[0]
            current = caller.get_equipped("weapon")
            current_off = caller.get_equipped("offhand")
            if current and current != main_item:
                caller.unequip("weapon")
            if current_off and current_off != main_item:
                caller.unequip("offhand")
            if not caller.get_equipped("weapon") or caller.get_equipped("weapon") != main_item:
                caller.equip("weapon", main_item)
                caller.equip("offhand", main_item)
                wielded.append(f"|w{main_item.key}|n (both hands)")

        elif shields:
            # Only shields, equip one in offhand
            off_item = shields[0]
            current_off = caller.get_equipped("offhand")
            if current_off and current_off != off_item:
                caller.unequip("offhand")
            if not caller.get_equipped("offhand") or caller.get_equipped("offhand") != off_item:
                caller.equip("offhand", off_item)
                wielded.append(f"|w{off_item.key}|n (off hand)")

        if wielded:
            caller.msg(f"|gYou wield: {', '.join(wielded)}|n")
            caller.location.msg_contents(
                f"|w{caller.name}|n readies weapons.",
                exclude=caller,
            )
        else:
            caller.msg("You're already wielding everything you can.")


class CmdUnwield(Command):
    """
    Stop wielding your weapon.

    Usage:
        unwield
        unwield offhand

    Without an argument, unequips your main hand weapon.
    """

    key = "unwield"
    aliases = ["holster", "sheathe"]
    help_category = "Equipment"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip().lower()

        slot = "weapon"
        if args in ("offhand", "off", "off-hand"):
            slot = "offhand"
        elif args and args not in ("weapon", "main", "mainhand", "main-hand"):
            caller.msg("Usage: unwield [weapon|offhand]")
            return

        current = caller.get_equipped(slot)
        if not current:
            label = "off hand" if slot == "offhand" else "main hand"
            caller.msg(f"You have nothing in your {label}.")
            return

        # 2H weapon: clear both slots
        item_hands = getattr(current.db, "hands", 1) or 1
        if item_hands == 2:
            caller.unequip("weapon")
            caller.unequip("offhand")
            caller.msg(f"You sheathe {current.key}.")
            caller.location.msg_contents(
                f"|w{caller.name}|n sheathes {current.key}.",
                exclude=caller
            )
            return

        caller.unequip(slot)
        caller.msg(f"You sheathe {current.key}.")
        caller.location.msg_contents(
            f"|w{caller.name}|n sheathes {current.key}.",
            exclude=caller
        )


class CmdEq(Command):
    """
    Show your currently equipped items and worn clothing.

    Usage:
        eq
        equipment
    """

    key = "eq"
    aliases = ["equipment", "worn"]
    help_category = "Equipment"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        lines = ["|wEquipment:|n"]

        slot_labels = {
            "weapon":  "Main Hand",
            "offhand": "Off Hand ",
            "head":    "Head     ",
            "chest":   "Chest    ",
            "legs":    "Legs     ",
            "feet":    "Feet     ",
            "hands":   "Hands    ",
        }

        main_weapon = caller.get_equipped("weapon")
        offhand_item = caller.get_equipped("offhand")
        is_two_handed = (
            main_weapon and offhand_item
            and main_weapon == offhand_item
        )

        for slot, label in slot_labels.items():
            item = caller.get_equipped(slot)
            if item:
                if slot == "weapon" and is_two_handed:
                    lines.append(f"  |c{label}|n : |w{item.key}|n (two-handed)")
                elif slot == "offhand" and is_two_handed:
                    continue  # suppress offhand line for 2H
                else:
                    lines.append(f"  |c{label}|n : |w{item.key}|n")
            else:
                lines.append(f"  |c{label}|n : |x-empty-|n")

        # Clothing from ClothedCharacter
        if hasattr(caller, "get_worn_clothes"):
            worn = caller.get_worn_clothes(exclude_covered=False)
            if worn:
                lines.append("\n|wClothing:|n")
                for item in worn:
                    style = item.db.worn or "worn"
                    lines.append(f"  |w{item.key}|n ({style})")

        caller.msg("\n".join(lines))
