"""
Clothing contrib overrides
==========================

Extends the clothing contrib's ``wear`` and ``inventory`` commands.

- ``wear all`` wears all unworn clothing from inventory.
- ``inventory`` shows wielded weapons, worn clothing, and carried items
  as separate sections.

Depends on:
    evennia.contrib.game_systems.clothing  -- CmdWear, CmdInventory, ContribClothing
    typeclasses.characters.AwtownCharacter -- get_equipped()
"""

from evennia.contrib.game_systems.clothing.clothing import (
    CmdWear as ContribCmdWear,
    CmdInventory as ContribCmdInventory,
    get_worn_clothes,
    order_clothes_list,
)


class CmdWearAll(ContribCmdWear):
    """
    Wear clothing from your inventory.

    Usage:
        wear <item>                   -- wear a single item
        wear <item> <style>           -- wear with a style description
        wear all                      -- wear all unworn clothing

    Examples:
        wear red shirt
        wear scarf wrapped loosely about the shoulders
        wear all
    """

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if args.lower() != "all":
            # Delegate to standard contrib wear
            super().func()
            return

        # Wear all unworn clothing in inventory
        from evennia.contrib.game_systems.clothing.clothing import ContribClothing

        unworn = [
            obj for obj in caller.contents
            if isinstance(obj, ContribClothing)
            and not obj.db.worn
        ]

        if not unworn:
            caller.msg("You don't have any unworn clothing to put on.")
            return

        worn_items = []
        skipped = []

        for item in unworn:
            try:
                item.wear(caller, True)
                worn_items.append(item.key)
            except Exception:
                skipped.append(item.key)

        if worn_items:
            caller.msg(f"|gYou put on: {', '.join(worn_items)}|n")
            caller.location.msg_contents(
                f"|w{caller.name}|n puts on some clothing.",
                exclude=caller,
            )

        if skipped:
            caller.msg(f"Couldn't wear: {', '.join(skipped)}")

        if not worn_items and not skipped:
            caller.msg("You couldn't wear anything.")


class CmdInventory(ContribCmdInventory):
    """
    View your inventory.

    Usage:
        inventory
        inv
        i

    Shows what you are wielding, wearing, and carrying.
    """

    def func(self):
        caller = self.caller

        if not caller.contents:
            caller.msg("You are not carrying or wearing anything.")
            return

        lines = []

        # --- Wielded weapons ---
        wielded = []
        if hasattr(caller, "get_equipped"):
            slot_labels = {"weapon": "Main Hand", "offhand": "Off Hand"}
            for slot, label in slot_labels.items():
                item = caller.get_equipped(slot)
                if item:
                    wielded.append((label, item))

        if wielded:
            lines.append("|wWielded:|n")
            for label, item in wielded:
                lines.append(f"  |c{label:<10}|n : |w{item.key}|n")
            lines.append("")

        # --- Worn clothing ---
        worn = get_worn_clothes(caller, exclude_covered=False)
        if worn:
            lines.append("|wWorn:|n")
            for garment in worn:
                style = garment.db.worn
                if garment.db.covered_by:
                    lines.append(f"  |x{garment.key} (covered by {garment.db.covered_by.key})|n")
                elif type(style) is str:
                    lines.append(f"  |w{garment.key}|n ({style})")
                else:
                    lines.append(f"  |w{garment.key}|n")
            lines.append("")

        # --- Carried items (not worn, not wielded) ---
        wielded_items = set(item for _, item in wielded)
        carried = [
            obj for obj in caller.contents
            if not obj.db.worn
            and obj not in wielded_items
        ]

        lines.append("|wCarrying:|n")
        if carried:
            # Group identical items
            from collections import Counter
            counts = Counter(obj.key for obj in carried)
            for name, count in sorted(counts.items()):
                if count > 1:
                    lines.append(f"  {name} (x{count})")
                else:
                    lines.append(f"  {name}")
        else:
            lines.append("  Nothing.")

        caller.msg("\n".join(lines))
