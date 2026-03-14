"""
Container interaction commands: get, put, and drop
===================================================

Overrides the default get/drop and the containers contrib's put with
versions that handle duplicate item names, an 'all' modifier, and
numeric quantity prefixes.

GET syntax:
    get <item>                        -- pick up from room (standard)
    get <N> <item>                    -- pick up N matching items from room
    get <item> from <container>       -- get one item from container
    get all from <container>          -- get everything from container
    get all <item> from <container>   -- get all matching items from container
    get <N> <item> from <container>   -- get N matching items from container

PUT syntax:
    put <item> in <container>         -- put one item in container
    put <N> <item> in <container>     -- put N matching items in container
    put all in <container>            -- put everything in container
    put all <item> in <container>     -- put all matching items in container

DROP syntax:
    drop <item>                       -- drop one item into the room
    drop <N> <item>                   -- drop N matching items
    drop all                          -- drop everything you carry
    drop all <item>                   -- drop all matching items

Aliases:
    get = take
    put = place, store

When multiple items share the same name (e.g. three Torches), all
commands auto-pick the first match instead of asking "which one?"

Depends on:
    evennia.contrib.game_systems.containers  -- ContribContainer, get_from lock
"""

from evennia.commands.command import Command


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _parse_quantity(text):
    """
    Parse a quantity prefix from item text.

    Returns:
        (qty, item_query) where qty is int, "all", or 1 (default).
        item_query is None only when text is bare "all".

    Examples:
        '3 torch'   -> (3, 'torch')
        'all bread' -> ('all', 'bread')
        'all'       -> ('all', None)
        'sword'     -> (1, 'sword')
    """
    parts = text.split(None, 1)
    if not parts:
        return (1, text)
    if parts[0].lower() == "all":
        return ("all", parts[1] if len(parts) > 1 else None)
    if parts[0].isdigit():
        n = int(parts[0])
        if n > 0 and len(parts) > 1:
            return (n, parts[1])
    return (1, text)


def _find_one(searcher, query, candidates):
    """
    Find a single item from a list of candidates by partial name match.
    Auto-picks the first when all matches have the same key.

    Args:
        searcher: The character doing the search (for messaging).
        query (str): Search string.
        candidates (list): Objects to search through.

    Returns:
        Object or None.
    """
    query_lower = query.lower()
    matches = [
        obj for obj in candidates
        if query_lower in obj.key.lower()
        or any(query_lower in a.lower() for a in obj.aliases.all())
    ]

    if not matches:
        return None

    if len(matches) == 1:
        return matches[0]

    # Multiple matches — if all same name, pick first
    unique_keys = set(m.key for m in matches)
    if len(unique_keys) == 1:
        return matches[0]

    # Actually different items — ask
    searcher.msg(f"Which one? {', '.join(unique_keys)}")
    return None


def _find_all(query, candidates):
    """
    Find ALL items matching a query from a list of candidates.

    Args:
        query (str): Search string.
        candidates (list): Objects to search through.

    Returns:
        list: All matching objects.
    """
    query_lower = query.lower()
    return [
        obj for obj in candidates
        if query_lower in obj.key.lower()
        or any(query_lower in a.lower() for a in obj.aliases.all())
    ]


def _find_n(searcher, query, candidates, count):
    """
    Find up to *count* items matching query from candidates.

    Args:
        searcher: The character (for messaging).
        query (str): Search string.
        candidates (list): Objects to search through.
        count (int or "all"): How many to return.

    Returns:
        list: Matching objects (up to count).
    """
    matches = _find_all(query, candidates)
    if not matches:
        return []
    if count == "all":
        return matches
    if len(matches) < count:
        searcher.msg(f"(Only {len(matches)} found.)")
    return matches[:count]


def _find_container(caller, query):
    """
    Find a container by name — checks inventory first, then room.

    A valid container is anything with a get_from lock or an
    at_pre_put_in method.

    Args:
        caller: The character searching.
        query (str): Container name to search for.

    Returns:
        Object or None.
    """
    query_lower = query.lower()

    # Check inventory first
    for obj in caller.contents:
        if query_lower in obj.key.lower() or any(
            query_lower in a.lower() for a in obj.aliases.all()
        ):
            if _is_container(obj):
                return obj

    # Check room
    for obj in caller.location.contents:
        if obj == caller:
            continue
        if query_lower in obj.key.lower() or any(
            query_lower in a.lower() for a in obj.aliases.all()
        ):
            if _is_container(obj):
                return obj

    return None


def _is_container(obj):
    """Check if an object can act as a container."""
    if hasattr(obj, "at_pre_put_in"):
        return True
    if hasattr(obj, "locks"):
        try:
            return obj.locks.check_lockstring(None, "get_from:true()")
        except Exception:
            pass
    # Check if it has contents that aren't itself
    if hasattr(obj, "contents") and any(c != obj for c in obj.contents):
        return True
    return False


# ---------------------------------------------------------------------------
# CmdGet
# ---------------------------------------------------------------------------

class CmdGet(Command):
    """
    Pick up items or take items from containers.

    Usage:
        get <item>                        -- pick up from the room
        get <N> <item>                    -- pick up N matching items
        get <item> from <container>       -- take one item from a container
        get <N> <item> from <container>   -- take N matching items
        get all from <container>          -- take everything from a container
        get all <item> from <container>   -- take all matching items from container

    Aliases: take

    Examples:
        get sword
        get 3 torch
        get dagger from corpse
        get all from corpse
        get 2 bread from barrel
        get all torch from pouch
    """

    key = "get"
    aliases = ["take"]
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Get what?")
            return

        # Check for "from <container>" syntax
        if " from " in args.lower():
            self._get_from_container(args)
        else:
            self._get_from_room(args)

    def _get_from_room(self, args):
        """Pick up item(s) from the room."""
        caller = self.caller
        qty, item_query = _parse_quantity(args)

        # "get all" (no item filter) — pick up everything
        if qty == "all" and item_query is None:
            items = [
                obj for obj in caller.location.contents
                if obj != caller
                and not getattr(obj.db, "is_npc", False)
                and not getattr(obj.db, "is_mob", False)
                and obj not in caller.location.exits
                and obj.access(caller, "get")
            ]
            if not items:
                caller.msg("There's nothing here to pick up.")
                return
            count = 0
            for item in items:
                item.move_to(caller, quiet=True)
                count += 1
            caller.msg(f"|gYou pick up {count} item(s).|n")
            caller.location.msg_contents(
                f"|w{caller.name}|n picks up some items.",
                exclude=caller,
            )
            return

        # "get all <item>" or "get <N> <item>"
        if qty != 1:
            room_items = [
                obj for obj in caller.location.contents
                if obj != caller
                and obj not in caller.location.exits
                and obj.access(caller, "get")
            ]
            matches = _find_n(caller, item_query, room_items, qty)
            if not matches:
                caller.msg(f"You don't see any '{item_query}' here.")
                return
            for item in matches:
                item.move_to(caller, quiet=True)
            names = ", ".join(m.key for m in matches)
            caller.msg(f"|gYou pick up {len(matches)}x: {names}|n")
            caller.location.msg_contents(
                f"|w{caller.name}|n picks up some items.",
                exclude=caller,
            )
            return

        # Single item from room
        room_items = [
            obj for obj in caller.location.contents
            if obj != caller and obj not in caller.location.exits
        ]
        item = _find_one(caller, item_query, room_items)
        if not item:
            caller.msg(f"You don't see '{item_query}' here.")
            return

        if not item.access(caller, "get"):
            if item.db.get_err_msg:
                caller.msg(item.db.get_err_msg)
            else:
                caller.msg("You can't pick that up.")
            return

        item.move_to(caller, quiet=True)
        caller.msg(f"|gYou pick up {item.key}.|n")
        caller.location.msg_contents(
            f"|w{caller.name}|n picks up {item.key}.",
            exclude=caller,
        )

    def _get_from_container(self, args):
        """Get item(s) from a container."""
        caller = self.caller

        # Parse: "item from container"
        idx = args.lower().index(" from ")
        item_part = args[:idx].strip()
        container_query = args[idx + 6:].strip()

        if not container_query:
            caller.msg("Get from what?")
            return

        # Find the container
        container = _find_container(caller, container_query)
        if not container:
            caller.msg(f"You don't see a container called '{container_query}'.")
            return

        # Get container contents
        contents = [obj for obj in container.contents if obj != container]

        if not contents:
            caller.msg(f"{container.key} is empty.")
            return

        # Check at_pre_get_from if available
        def _check_get(item):
            if hasattr(container, "at_pre_get_from"):
                return container.at_pre_get_from(caller, item)
            return True

        qty, item_query = _parse_quantity(item_part)

        # "get all from container" (no item filter)
        if qty == "all" and item_query is None:
            count = 0
            taken = []
            for item in list(contents):
                if _check_get(item):
                    item.move_to(caller, quiet=True)
                    taken.append(item.key)
                    count += 1
            if taken:
                caller.msg(f"|gYou take from {container.key}: {', '.join(taken)}|n")
                caller.location.msg_contents(
                    f"|w{caller.name}|n takes items from {container.key}.",
                    exclude=caller,
                )
            else:
                caller.msg(f"You couldn't take anything from {container.key}.")
            return

        # "get all <item> from container" or "get <N> <item> from container"
        if qty != 1:
            matches = _find_n(caller, item_query, contents, qty)
            if not matches:
                caller.msg(f"You don't see any '{item_query}' in {container.key}.")
                return
            taken = []
            for item in matches:
                if _check_get(item):
                    item.move_to(caller, quiet=True)
                    taken.append(item.key)
            if taken:
                caller.msg(f"|gYou take {len(taken)}x from {container.key}: {', '.join(taken)}|n")
                caller.location.msg_contents(
                    f"|w{caller.name}|n takes items from {container.key}.",
                    exclude=caller,
                )
            else:
                caller.msg(f"Couldn't take any '{item_query}' from {container.key}.")
            return

        # Single item from container
        item = _find_one(caller, item_query, contents)
        if not item:
            caller.msg(f"You don't see '{item_query}' in {container.key}.")
            return

        if not _check_get(item):
            caller.msg(f"You can't take that from {container.key}.")
            return

        item.move_to(caller, quiet=True)
        caller.msg(f"|gYou take {item.key} from {container.key}.|n")
        caller.location.msg_contents(
            f"|w{caller.name}|n takes {item.key} from {container.key}.",
            exclude=caller,
        )


# ---------------------------------------------------------------------------
# CmdPut
# ---------------------------------------------------------------------------

class CmdPut(Command):
    """
    Put items into a container.

    Usage:
        put <item> in <container>         -- put one item
        put <N> <item> in <container>     -- put N matching items
        put all in <container>            -- put everything you carry
        put all <item> in <container>     -- put all matching items

    Aliases: place, store

    Examples:
        put torch in pouch
        put 3 bread in chest
        put all in chest
        put all torch in pouch
    """

    key = "put"
    aliases = ["place", "store"]
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
        item_part = args[:idx].strip()
        container_query = args[idx + 4:].strip()

        if not item_part or not container_query:
            caller.msg("Usage: |wput <item> in <container>|n")
            return

        # Find the container
        container = _find_container(caller, container_query)
        if not container:
            caller.msg(f"You don't see a container called '{container_query}'.")
            return

        # Get inventory (exclude the container itself and worn items)
        inventory = [
            obj for obj in caller.contents
            if obj != container
            and not getattr(obj.db, "worn", None)
        ]

        # Check at_pre_put_in if available
        def _check_put(item):
            if hasattr(container, "at_pre_put_in"):
                return container.at_pre_put_in(caller, item)
            return True

        qty, item_query = _parse_quantity(item_part)

        # "put all in container" (no item filter)
        if qty == "all" and item_query is None:
            if not inventory:
                caller.msg("You have nothing to put in there.")
                return
            count = 0
            for item in list(inventory):
                if _check_put(item):
                    item.move_to(container, quiet=True)
                    count += 1
            if count:
                caller.msg(f"|gYou put {count} item(s) in {container.key}.|n")
                caller.location.msg_contents(
                    f"|w{caller.name}|n puts items in {container.key}.",
                    exclude=caller,
                )
            else:
                caller.msg(f"Couldn't put anything in {container.key}.")
            return

        # "put all <item> in container" or "put <N> <item> in container"
        if qty != 1:
            matches = _find_n(caller, item_query, inventory, qty)
            if not matches:
                caller.msg(f"You aren't carrying any '{item_query}'.")
                return
            count = 0
            for item in matches:
                if item == container:
                    continue
                if _check_put(item):
                    item.move_to(container, quiet=True)
                    count += 1
            if count:
                caller.msg(
                    f"|gYou put {count}x {matches[0].key} in {container.key}.|n"
                )
                caller.location.msg_contents(
                    f"|w{caller.name}|n puts items in {container.key}.",
                    exclude=caller,
                )
            else:
                caller.msg(f"Couldn't put any '{item_query}' in {container.key}.")
            return

        # Single item
        item = _find_one(caller, item_query, inventory)
        if not item:
            caller.msg(f"You aren't carrying '{item_query}'.")
            return

        if item == container:
            caller.msg("You can't put something inside itself.")
            return

        if not _check_put(item):
            return

        item.move_to(container, quiet=True)
        caller.msg(f"|gYou put {item.key} in {container.key}.|n")
        caller.location.msg_contents(
            f"|w{caller.name}|n puts {item.key} in {container.key}.",
            exclude=caller,
        )


# ---------------------------------------------------------------------------
# CmdDrop
# ---------------------------------------------------------------------------

class CmdDrop(Command):
    """
    Drop items from your inventory into the room.

    Usage:
        drop <item>             -- drop one item
        drop <N> <item>         -- drop N matching items
        drop all                -- drop everything you carry
        drop all <item>         -- drop all matching items

    Examples:
        drop sword
        drop 2 torch
        drop all
        drop all torch
    """

    key = "drop"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Drop what?")
            return

        # Get droppable inventory (exclude worn items)
        inventory = [
            obj for obj in caller.contents
            if not getattr(obj.db, "worn", None)
        ]

        qty, item_query = _parse_quantity(args)

        # "drop all" (no item filter)
        if qty == "all" and item_query is None:
            if not inventory:
                caller.msg("You aren't carrying anything to drop.")
                return
            count = 0
            for item in list(inventory):
                item.move_to(caller.location, quiet=True)
                count += 1
            caller.msg(f"|gYou drop {count} item(s).|n")
            caller.location.msg_contents(
                f"|w{caller.name}|n drops some items.",
                exclude=caller,
            )
            return

        # "drop all <item>" or "drop <N> <item>"
        if qty != 1:
            matches = _find_n(caller, item_query, inventory, qty)
            if not matches:
                caller.msg(f"You aren't carrying any '{item_query}'.")
                return
            for item in matches:
                item.move_to(caller.location, quiet=True)
            caller.msg(
                f"|gYou drop {len(matches)}x {matches[0].key}.|n"
            )
            caller.location.msg_contents(
                f"|w{caller.name}|n drops some items.",
                exclude=caller,
            )
            return

        # Single item
        item = _find_one(caller, item_query, inventory)
        if not item:
            caller.msg(f"You aren't carrying '{item_query}'.")
            return

        item.move_to(caller.location, quiet=True)
        caller.msg(f"|gYou drop {item.key}.|n")
        caller.location.msg_contents(
            f"|w{caller.name}|n drops {item.key}.",
            exclude=caller,
        )
