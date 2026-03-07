"""
Shop commands: list, buy, sell.

These work by finding a merchant NPC in the caller's current room.
If multiple merchants are present, the player can specify which one.

Usage:
    list                  - list wares of the merchant in this room
    list <npc name>       - list wares of a specific merchant
    buy <item>            - buy an item
    buy <item> from <npc> - buy from a specific merchant
    sell <item>           - sell an item from your inventory
"""

from evennia.commands.command import Command
from evennia import create_object
from typeclasses.npcs import AwtownNPC


def _find_merchant(location, npc_name=None):
    """Return the first merchant NPC in the room, optionally filtered by name."""
    merchants = [
        obj for obj in location.contents
        if isinstance(obj, AwtownNPC)
        and obj.db.npc_role in ("merchant", "banker", "innkeeper", "founder")
        and obj.db.shop_inventory
    ]
    if not merchants:
        return None
    if npc_name:
        npc_name = npc_name.lower()
        for m in merchants:
            if npc_name in m.name.lower():
                return m
        return None
    return merchants[0]


class CmdList(Command):
    """
    List the wares of a merchant in your current room.

    Usage:
        list
        list <merchant name>

    Shows all items available for purchase and their prices.
    Prices are shown in gold (g), silver (s), and copper (c).

    Examples:
        list
        list Marta
    """

    key = "list"
    aliases = ["wares", "shop"]
    help_category = "Shopping"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        npc_name = self.args.strip() or None
        merchant = _find_merchant(caller.location, npc_name)

        if not merchant:
            caller.msg("There's no merchant here to buy from.")
            return

        inventory = merchant.db.shop_inventory or []
        if not inventory:
            caller.msg(f"{merchant.name} doesn't have anything for sale right now.")
            return

        lines = [f"|w{merchant.name}|n offers the following wares:\n"]
        lines.append(f"  {'Item':<30} {'Price':>10}")
        lines.append(f"  {'-'*30} {'-'*10}")
        for item in inventory:
            name = item.get("name", "???")
            price = item.get("price", 0)
            lines.append(f"  {name:<30} {price:>7} cp")
        lines.append("\nType |wbuy <item name>|n to purchase.")
        caller.msg("\n".join(lines))


class CmdBuy(Command):
    """
    Buy an item from a merchant in your current room.

    Usage:
        buy <item>
        buy <item> from <merchant name>

    The item name is matched against the merchant's inventory.
    Payment is deducted from your copper purse.

    Examples:
        buy torch
        buy simple tunic from Marta
    """

    key = "buy"
    help_category = "Shopping"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Buy what?")
            return

        # Parse "item from merchant"
        npc_name = None
        if " from " in args.lower():
            parts = args.lower().split(" from ", 1)
            item_query = parts[0].strip()
            npc_name = parts[1].strip()
        else:
            item_query = args.lower()

        merchant = _find_merchant(caller.location, npc_name)
        if not merchant:
            caller.msg("There's no merchant here to buy from.")
            return

        inventory = merchant.db.shop_inventory or []
        match = None
        for item in inventory:
            if item_query in item.get("name", "").lower():
                match = item
                break

        if not match:
            caller.msg(f"{merchant.name} doesn't carry anything called '{self.args.strip()}'.")
            return

        price = match.get("price", 0)
        purse = caller.db.copper or 0

        if purse < price:
            caller.msg(
                f"|r{merchant.name} says, \"|wThat'll be {price} copper. "
                f"You're {price - purse} short.\"|n"
            )
            return

        # Deduct cost
        caller.db.copper = purse - price

        # Create the item in the caller's inventory
        proto_key = match.get("key")
        item_name = match.get("name", "item")
        item_desc = match.get("desc", "A purchased item.")

        if proto_key:
            try:
                from evennia.utils import spawner
                objs = spawner.spawn(proto_key)
                if objs:
                    objs[0].move_to(caller, quiet=True)
                    caller.msg(
                        f"|g{merchant.name} hands you |w{item_name}|g for {price} copper.|n"
                    )
                    return
            except Exception:
                pass

        # Fallback: create a basic object
        from evennia import create_object
        from evennia.objects.objects import DefaultObject
        obj = create_object(DefaultObject, key=item_name, location=caller)
        obj.db.desc = item_desc
        caller.msg(f"|g{merchant.name} hands you |w{item_name}|g for {price} copper.|n")


class CmdSell(Command):
    """
    Sell an item from your inventory to a merchant.

    Usage:
        sell <item>

    The merchant pays you half the item's base value in copper.
    Not all merchants buy all items.

    Examples:
        sell torch
        sell old sword
    """

    key = "sell"
    help_category = "Shopping"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        query = self.args.strip().lower()

        if not query:
            caller.msg("Sell what?")
            return

        merchant = _find_merchant(caller.location)
        if not merchant:
            caller.msg("There's no merchant here to sell to.")
            return

        # Find item in caller's inventory
        match = caller.search(query, location=caller, quiet=True)
        if not match:
            caller.msg(f"You don't have anything called '{self.args.strip()}'.")
            return
        if isinstance(match, list):
            match = match[0]

        base_value = match.db.value or 2
        sell_price = max(1, base_value // 2)

        caller.db.copper = (caller.db.copper or 0) + sell_price
        match.delete()
        caller.msg(
            f"|g{merchant.name} takes your |w{match.name}|g and pays you {sell_price} copper.|n"
        )
