"""
Fill command
============

    fill <container>    -- refill a drinkable container at a water source

Works at any room tagged with "water_source" (category "awtown_room"),
or any room containing an object tagged with "water_source"
(category "awtown_object") — fountains, wells, troughs, etc.

Depends on:
    typeclasses.items.AwtownDrinkable -- db.sips, db.sips_max, refill()
"""

from evennia.commands.command import Command


def _has_water_source(location):
    """
    Check if a room has a water source.

    Returns (has_source: bool, source_name: str).

    A room counts as a water source if:
      1. The room itself is tagged "water_source" (category "awtown_room")
      2. Any object in the room is tagged "water_source" (category "awtown_object")
    """
    if not location:
        return False, ""

    # Check room tag
    if location.tags.get("water_source", category="awtown_room"):
        return True, "the water here"

    # Check objects in the room
    for obj in location.contents:
        if hasattr(obj, "tags") and obj.tags.get("water_source", category="awtown_object"):
            name = obj.get_display_name(None) if hasattr(obj, "get_display_name") else obj.key
            return True, name

    return False, ""


class CmdFill(Command):
    """
    Refill a drinkable container at a water source.

    Usage:
        fill <container>
        fill waterskin
        refill <container>

    You must be near a water source — a fountain, well, stream, or
    similar. Refills the container to its maximum capacity.

    Examples:
        fill waterskin
        refill flask
    """

    key = "fill"
    aliases = ["refill"]
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Fill what? Usage: |wfill <container>|n")
            return

        # Find the item in inventory
        item = caller.search(args, location=caller, quiet=True)
        if not item:
            caller.msg(f"You aren't carrying '{args}'.")
            return
        if isinstance(item, list):
            if len(item) > 1:
                unique_keys = set(i.key for i in item)
                if len(unique_keys) > 1:
                    caller.msg(f"Which one? {', '.join(unique_keys)}")
                    return
            item = item[0]

        # Must be a drinkable
        from typeclasses.items import AwtownDrinkable
        if not isinstance(item, AwtownDrinkable):
            caller.msg(f"You can't fill {item.key}.")
            return

        # Already full?
        if (item.db.sips or 0) >= (item.db.sips_max or 5):
            caller.msg(f"{item.key} is already full.")
            return

        # Check for water source
        has_water, source_name = _has_water_source(caller.location)
        if not has_water:
            caller.msg(
                "There's no water source here. Find a fountain, well, "
                "or stream to refill your container."
            )
            return

        # Refill
        old_sips = item.db.sips or 0
        new_sips = item.refill()

        caller.msg(
            f"|gYou fill {item.key} from {source_name}. "
            f"({new_sips}/{item.db.sips_max} sips)|n"
        )
        caller.location.msg_contents(
            f"|w{caller.name}|n fills {item.key} from {source_name}.",
            exclude=caller,
        )
