"""
Eat and drink commands
======================

    eat <item>      -- consume food from inventory, restoring hunger and/or HP
    drink <item>    -- consume a drink, restoring thirst and/or HP

Both commands call the character's restore_hunger() / restore_thirst()
methods from DorfinNeedsMixin, then heal() from AwtownCharacter.
The consumed item is deleted after use.

Depends on:
    typeclasses.items.AwtownConsumable  -- db.nutrition, db.hydration, db.hp_restore
    typeclasses.characters.AwtownCharacter -- restore_hunger(), restore_thirst(), heal()
"""

from evennia.commands.command import Command


class CmdEat(Command):
    """
    Eat food from your inventory.

    Usage:
        eat <food>

    Eating restores your hunger and may restore some health.
    You must be carrying the item.

    Examples:
        eat hunk of bread
        eat ration
    """

    key = "eat"
    aliases = ["consume"]
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Eat what?")
            return

        item = caller.search(args, location=caller, quiet=True)
        if not item:
            caller.msg(f"You aren't carrying '{args}'.")
            return
        if isinstance(item, list):
            if len(item) > 1:
                matches = ", ".join(i.key for i in item)
                caller.msg(f"Which one? {matches}")
                return
            item = item[0]

        from typeclasses.items import AwtownConsumable
        if not isinstance(item, AwtownConsumable):
            caller.msg(f"You can't eat {item.key}.")
            return

        nutrition = item.db.nutrition or 0
        hydration = item.db.hydration or 0
        hp_restore = item.db.hp_restore or 0

        if nutrition <= 0 and hp_restore <= 0:
            caller.msg(f"{item.key} doesn't seem edible.")
            return

        # Apply effects
        if nutrition and hasattr(caller, "restore_hunger"):
            new_hunger = caller.restore_hunger(nutrition)
            if new_hunger is not None and new_hunger > 75:
                caller.msg("|gYou feel satisfied.|n")

        if hydration and hasattr(caller, "restore_thirst"):
            caller.restore_thirst(hydration)

        if hp_restore and hasattr(caller, "heal"):
            caller.heal(hp_restore)
            caller.msg(f"|gYou recover {hp_restore} health.|n")

        # Describe eating
        desc = item.db.desc or ""
        caller.msg(f"You eat {item.key}.{' ' + desc if desc else ''}")
        caller.location.msg_contents(
            f"|w{caller.name}|n eats {item.key}.",
            exclude=caller
        )

        item.delete()


class CmdDrink(Command):
    """
    Drink something from your inventory.

    Usage:
        drink <item>

    Drinking restores your thirst and may restore some health.
    You must be carrying the item.

    Examples:
        drink waterskin
        drink healing draught
    """

    key = "drink"
    aliases = ["quaff", "sip"]
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Drink what?")
            return

        item = caller.search(args, location=caller, quiet=True)
        if not item:
            caller.msg(f"You aren't carrying '{args}'.")
            return
        if isinstance(item, list):
            if len(item) > 1:
                matches = ", ".join(i.key for i in item)
                caller.msg(f"Which one? {matches}")
                return
            item = item[0]

        from typeclasses.items import AwtownConsumable
        if not isinstance(item, AwtownConsumable):
            caller.msg(f"You can't drink {item.key}.")
            return

        nutrition = item.db.nutrition or 0
        hydration = item.db.hydration or 0
        hp_restore = item.db.hp_restore or 0

        if hydration <= 0 and hp_restore <= 0:
            caller.msg(f"{item.key} doesn't seem drinkable.")
            return

        # Apply effects
        if hydration and hasattr(caller, "restore_thirst"):
            new_thirst = caller.restore_thirst(hydration)
            if new_thirst is not None and new_thirst > 75:
                caller.msg("|gYou feel refreshed.|n")

        if nutrition and hasattr(caller, "restore_hunger"):
            caller.restore_hunger(nutrition)

        if hp_restore and hasattr(caller, "heal"):
            caller.heal(hp_restore)
            caller.msg(f"|gYou recover {hp_restore} health.|n")

        caller.msg(f"You drink {item.key}.")
        caller.location.msg_contents(
            f"|w{caller.name}|n drinks {item.key}.",
            exclude=caller
        )

        item.delete()
