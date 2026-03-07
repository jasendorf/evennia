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

    Equips the named weapon into your weapon slot (or offhand if specified).
    You must be carrying the item.

    Examples:
        wield short sword
        wield dagger offhand
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
                caller.msg(f"Which one? {list_to_string([i.key for i in item])}")
                return
            item = item[0]

        # Must be a weapon
        from typeclasses.items import AwtownWeapon
        if not isinstance(item, AwtownWeapon):
            caller.msg(f"{item.key} is not a weapon.")
            return

        # Use item's preferred slot unless player specified offhand
        if slot == "weapon":
            slot = item.db.slot or "weapon"

        # Unequip anything already there
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

        for slot, label in slot_labels.items():
            item = caller.get_equipped(slot)
            if item:
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
