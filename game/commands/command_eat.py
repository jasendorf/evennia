"""
Eat and drink commands
======================

    eat <item>      -- consume food from inventory, restoring hunger and/or HP
    eat <N> <item>  -- consume N of an item
    eat all <item>  -- consume all matching items
    drink <item>    -- consume a drink, restoring thirst and/or HP
    drink <N> <item> -- consume N single-use drinks

Both commands call the character's restore_hunger() / restore_thirst()
methods from DorfinNeedsMixin, then heal() from AwtownCharacter.
The consumed item is deleted after use.

Depends on:
    typeclasses.items.AwtownConsumable  -- db.nutrition, db.hydration, db.hp_restore
    typeclasses.characters.AwtownCharacter -- restore_hunger(), restore_thirst(), heal()
"""

from evennia.commands.command import Command
from commands.command_containers import _parse_quantity, _find_one, _find_n


class CmdEat(Command):
    """
    Eat food from your inventory.

    Usage:
        eat <food>
        eat <N> <food>
        eat all <food>

    Eating restores your hunger and may restore some health.
    You must be carrying the item.

    Examples:
        eat hunk of bread
        eat 3 bread
        eat all ration
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

        from typeclasses.items import AwtownConsumable

        qty, item_query = _parse_quantity(args)

        if item_query is None:
            caller.msg("Eat what?")
            return

        # Build list of edible items in inventory
        edible = [
            obj for obj in caller.contents
            if isinstance(obj, AwtownConsumable)
        ]

        # Multiple items
        if qty != 1:
            matches = _find_n(caller, item_query, edible, qty)
            if not matches:
                caller.msg(f"You aren't carrying any edible '{item_query}'.")
                return

            total_nutrition = 0
            total_hydration = 0
            total_hp = 0
            count = 0

            for item in list(matches):
                nutrition = item.db.nutrition or 0
                hydration = item.db.hydration or 0
                hp_restore = item.db.hp_restore or 0
                if nutrition <= 0 and hp_restore <= 0:
                    continue
                total_nutrition += nutrition
                total_hydration += hydration
                total_hp += hp_restore
                item.delete()
                count += 1

            if count == 0:
                caller.msg(f"None of those seem edible.")
                return

            if total_nutrition and hasattr(caller, "restore_hunger"):
                new_hunger = caller.restore_hunger(total_nutrition)
                if new_hunger is not None and new_hunger > 75:
                    caller.msg("|gYou feel satisfied.|n")

            if total_hydration and hasattr(caller, "restore_thirst"):
                caller.restore_thirst(total_hydration)

            if total_hp and hasattr(caller, "heal"):
                caller.heal(total_hp)
                caller.msg(f"|gYou recover {total_hp} health.|n")

            caller.msg(f"You eat {count}x {matches[0].key}.")
            caller.location.msg_contents(
                f"|w{caller.name}|n eats some food.",
                exclude=caller
            )
            return

        # Single item
        item = _find_one(caller, item_query, edible)
        if not item:
            # Try non-edible for a better error message
            any_match = _find_one(caller, item_query, list(caller.contents))
            if any_match:
                caller.msg(f"You can't eat {any_match.key}.")
            else:
                caller.msg(f"You aren't carrying '{item_query}'.")
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
        drink <N> <item>
        drink all <item>

    Drinking restores your thirst and may restore some health.
    You must be carrying the item.

    Multi-sip containers (like waterskins) are NOT destroyed after
    drinking — they track remaining sips. Single-use drinks (potions,
    etc.) are consumed and deleted.

    Quantity only applies to single-use drinks (potions, vials).
    For waterskins, use 'drink waterskin' to take one sip at a time.

    Examples:
        drink waterskin
        drink healing draught
        drink 2 potion
        drink all potion
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

        from typeclasses.items import AwtownDrinkable, AwtownConsumable

        qty, item_query = _parse_quantity(args)

        if item_query is None:
            caller.msg("Drink what?")
            return

        # Check for multi-sip drinkable first (waterskin, flask)
        # Quantity doesn't apply to these — always one sip
        drinkables = [
            obj for obj in caller.contents
            if isinstance(obj, AwtownDrinkable)
        ]
        drinkable = _find_one(caller, item_query, drinkables) if drinkables else None

        if drinkable:
            if qty != 1:
                caller.msg(f"You can only take one sip at a time from {drinkable.key}.")
            success, msg = drinkable.drink_sip(caller)
            if success:
                caller.msg(f"You take a drink from {drinkable.key}. {msg}")
                caller.location.msg_contents(
                    f"|w{caller.name}|n takes a drink from {drinkable.key}.",
                    exclude=caller,
                )
            else:
                caller.msg(msg)
            return

        # Single-use consumable drinks
        consumables = [
            obj for obj in caller.contents
            if isinstance(obj, AwtownConsumable)
        ]

        # Multiple single-use drinks
        if qty != 1:
            matches = _find_n(caller, item_query, consumables, qty)
            if not matches:
                caller.msg(f"You aren't carrying any '{item_query}'.")
                return

            total_nutrition = 0
            total_hydration = 0
            total_hp = 0
            count = 0

            for item in list(matches):
                hydration = item.db.hydration or 0
                hp_restore = item.db.hp_restore or 0
                if hydration <= 0 and hp_restore <= 0:
                    continue
                total_nutrition += (item.db.nutrition or 0)
                total_hydration += hydration
                total_hp += hp_restore
                item.delete()
                count += 1

            if count == 0:
                caller.msg(f"None of those seem drinkable.")
                return

            if total_hydration and hasattr(caller, "restore_thirst"):
                new_thirst = caller.restore_thirst(total_hydration)
                if new_thirst is not None and new_thirst > 75:
                    caller.msg("|gYou feel refreshed.|n")

            if total_nutrition and hasattr(caller, "restore_hunger"):
                caller.restore_hunger(total_nutrition)

            if total_hp and hasattr(caller, "heal"):
                caller.heal(total_hp)
                caller.msg(f"|gYou recover {total_hp} health.|n")

            caller.msg(f"You drink {count}x {matches[0].key}.")
            caller.location.msg_contents(
                f"|w{caller.name}|n drinks some beverages.",
                exclude=caller
            )
            return

        # Single consumable drink
        item = _find_one(caller, item_query, consumables)
        if not item:
            caller.msg(f"You can't drink that.")
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
            exclude=caller,
        )

        item.delete()
