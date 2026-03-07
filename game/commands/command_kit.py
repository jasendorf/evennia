"""
Starter kit claim command — available at The Outfitter's Rest.

New characters can claim a free starter kit once. Marta hands it out
with appropriate grandmotherly concern.
"""

from evennia.commands.command import Command
from evennia import create_object
from evennia.objects.objects import DefaultObject

STARTER_KIT = [
    {"name": "Simple Tunic",    "desc": "A plain but sturdy linen tunic. Comfortable for travel.", "value": 2},
    {"name": "Simple Trousers", "desc": "Plain travelling trousers, well-made if unadorned.", "value": 2},
    {"name": "Belt Pouch",      "desc": "A small leather pouch that attaches to a belt. Holds coins and small items.", "value": 5},
    {"name": "Torch",           "desc": "A wax-soaked torch that burns for about an hour.", "value": 1},
    {"name": "Torch",           "desc": "A wax-soaked torch that burns for about an hour.", "value": 1},
    {"name": "Torch",           "desc": "A wax-soaked torch that burns for about an hour.", "value": 1},
    {"name": "Waterskin",       "desc": "A leather waterskin, full of clean water.", "value": 3},
    {"name": "Hunk of Bread",   "desc": "A dense, filling hunk of bread. Not exciting, but it travels well.", "value": 1},
]

OUTFITTERS_TAG = "outfitters_rest"
ROOM_TAG_CAT   = "awtown_dbkey"


class CmdClaimKit(Command):
    """
    Claim your free starter kit from Shopkeep Marta.

    Usage:
        claim kit
        claim

    Available only at The Outfitter's Rest. Every new adventurer may
    claim one starter kit — a set of basic clothing, three torches,
    a waterskin, and a hunk of bread.

    You also receive 50 copper pieces to get you started.
    """

    key = "claim"
    aliases = ["claim kit"]
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller

        # Check location
        loc = caller.location
        if not loc or not loc.tags.get(OUTFITTERS_TAG, category=ROOM_TAG_CAT):
            caller.msg(
                "You need to be at |wThe Outfitter's Rest|n to claim your starter kit. "
                "It's south of The Gilded Passage, just inside the Grand Gate."
            )
            return

        # Check if already claimed
        if caller.db.kit_claimed:
            caller.msg(
                "|yMarta smiles warmly. 'You've already picked up your kit, dear. "
                "I hope it's serving you well out there.'|n"
            )
            return

        # Give items
        for item_data in STARTER_KIT:
            obj = create_object(DefaultObject, key=item_data["name"], location=caller)
            obj.db.desc = item_data["desc"]
            obj.db.value = item_data["value"]

        # Give starting copper
        caller.db.copper = (caller.db.copper or 0) + 50

        # Mark as claimed
        caller.db.kit_claimed = True

        caller.msg(
            "|cMarta|n bustles about, pulling items from shelves and handing them to you one by one.\n\n"
            "  |wSimple Tunic, Simple Trousers, Belt Pouch,|n\n"
            "  |wThree Torches, Waterskin, Hunk of Bread.|n\n\n"
            "She presses a small purse of coins into your hand too.\n\n"
            "|gMarta says, \"|wNow you listen to me — eat something before you go out there, "
            "keep those torches dry, and don't talk to anything that glows in the dark. "
            "Come back in one piece.\"|n\n"
            "|gYou received the starter kit and 50 copper pieces.|n"
        )
        caller.location.msg_contents(
            f"|cMarta|n fusses over |w{caller.name}|n, pressing a starter kit and some coin into their hands.",
            exclude=caller
        )
