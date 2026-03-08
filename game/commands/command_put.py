"""
Custom put command
==================

    put <item> in <container>

Overrides the containers contrib's CmdPut to handle the case where
a player has multiple items with the same name (e.g. three torches).
Instead of asking "which one?", it just puts the first one.

Also handles 'put all in <container>' for convenience.
"""

from evennia.commands.command import Command


class CmdPut(Command):
    """
    Put an item into a container.

    Usage:
        put <item> in <container>
        put all in <container>

    Places an item from your inventory into a container you are
    carrying or one in the room.

    Examples:
        put torch in pouch
        put dagger in chest
        put all in pouch
    """

    key = "put"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Put what where? Usage: |wput <item> in <container>|n")
            return

        # Parse "item in container"
        if " in " not in args.lower():
            caller.msg("Usage: |wput <item> in <container>|n")
            return

        idx = args.lower().index(" in ")
        item_query = args[:idx].strip()
        container_query = args[idx + 4:].strip()

        if not item_query or not container_query:
            caller.msg("Usage: |wput <item> in <container>|n")
            return

        # Find the container (check inventory first, then room)
        container = _find_one(caller, container_query, location=caller)
        if not container:
            container = _find_one(caller, container_query, location=caller.location)
        if not container:
            caller.msg(f"You don't see a container called '{container_query}'.")
            return

        # Check the container accepts items
        has_get_from = container.locks.check_lockstring(caller, "get_from:true()")
        is_container = hasattr(container, "at_pre_put_in") or has_get_from
        if not is_container:
            caller.msg(f"You can't put things in {container.key}.")
            return

        # Handle "put all in container"
        if item_query.lower() == "all":
            items = [
                obj for obj in caller.contents
                if obj != container and not getattr(obj.db, "worn", None)
            ]
            if not items:
                caller.msg("You have nothing to put in there.")
                return
            count = 0
            for item in items:
                if _try_put(caller, item, container):
                    count += 1
            if count:
                caller.msg(f"|gYou put {count} item(s) in {container.key}.|n")
            return

        # Find the item in inventory
        item = _find_one(caller, item_query, location=caller)
        if not item:
            caller.msg(f"You aren't carrying '{item_query}'.")
            return

        # Can't put the container in itself
        if item == container:
            caller.msg("You can't put something inside itself.")
            return

        if _try_put(caller, item, container):
            caller.msg(f"|gYou put {item.key} in {container.key}.|n")
            caller.location.msg_contents(
                f"|w{caller.name}|n puts {item.key} in {container.key}.",
                exclude=caller,
            )


def _find_one(caller, query, location=None):
    """
    Find a single object, auto-picking the first when all matches
    have the same key name.
    """
    results = caller.search(query, location=location, quiet=True)
    if not results:
        return None
    if isinstance(results, list):
        if len(results) > 1:
            unique_keys = set(r.key for r in results)
            if len(unique_keys) > 1:
                caller.msg(f"Which one? {', '.join(unique_keys)}")
                return None
        return results[0]
    return results


def _try_put(caller, item, container):
    """
    Attempt to move an item into a container, checking locks and
    capacity.

    Returns True on success.
    """
    # Check container's at_pre_put_in if it has one
    if hasattr(container, "at_pre_put_in"):
        if not container.at_pre_put_in(caller, item):
            return False

    # Move the item
    item.move_to(container, quiet=True)
    return True
