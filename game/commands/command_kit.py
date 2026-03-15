"""
Starter kit commands — available at The Outfitter's Rest.

    claim / claim kit  -- claim your free starter kit (once per character)
    choose weapon      -- pick a free starter weapon from Marta

New characters can claim a free starter kit once. Marta hands out
basic clothing, food, a waterskin, torches, and 50 copper.

After claiming the kit, players can also choose one free starter weapon
appropriate to their fighting style:

    choose sword   -- a wooden practice sword (1d4, balanced)
    choose club    -- a crude wooden club (1d6, slow but heavy)
    choose staff   -- a light wooden staff (1d4, good reach)
    choose dagger  -- a dull iron dagger (1d3, fast)

Depends on:
    typeclasses.items.AwtownClothing     -- wearable clothing
    typeclasses.items.AwtownConsumable   -- food and drink
    typeclasses.items.AwtownItem         -- general items
    typeclasses.items.AwtownWeapon       -- weapons
"""

from evennia.commands.command import Command
from evennia import create_object


OUTFITTERS_TAG = "outfitters_rest"
ROOM_TAG_CAT   = "awtown_dbkey"


# ---------------------------------------------------------------------------
# Starter kit item definitions
# ---------------------------------------------------------------------------

STARTER_KIT_CLOTHING = [
    {
        "name": "Simple Tunic",
        "aliases": ["tunic"],
        "desc": "A plain but sturdy linen tunic. Comfortable for travel.",
        "value": 2,
        "clothing_type": "top",
    },
    {
        "name": "Simple Trousers",
        "aliases": ["trousers", "pants"],
        "desc": "Plain travelling trousers, well-made if unadorned.",
        "value": 2,
        "clothing_type": "bottom",
    },
]

STARTER_KIT_CONSUMABLES = [
    {
        "name": "Hunk of Bread",
        "aliases": ["bread", "hunk"],
        "desc": "A dense, filling hunk of bread. Not exciting, but it travels well.",
        "value": 1,
        "nutrition": 25,
        "hydration": 0,
        "hp_restore": 0,
    },
    {
        "name": "Hunk of Bread",
        "aliases": ["bread", "hunk"],
        "desc": "A dense, filling hunk of bread. Not exciting, but it travels well.",
        "value": 1,
        "nutrition": 25,
        "hydration": 0,
        "hp_restore": 0,
    },
]

STARTER_KIT_DRINKABLE = {
    "name": "Waterskin",
    "aliases": ["skin", "water"],
    "desc": "A leather waterskin, full of clean water. Good for several drinks.",
    "value": 3,
    "sips": 5,
    "sips_max": 5,
    "hydration_per": 10,
    "hp_per": 0,
}

STARTER_KIT_CONTAINER = {
    "name": "Belt Pouch",
    "aliases": ["pouch", "belt"],
    "desc": "A small leather pouch that attaches to a belt. Holds coins and small items.",
    "value": 5,
    "capacity": 10,
}

STARTER_KIT_ITEMS = [
    {
        "name": "Torch",
        "desc": "A wax-soaked torch that burns for about an hour.",
        "value": 1,
    },
    {
        "name": "Torch",
        "desc": "A wax-soaked torch that burns for about an hour.",
        "value": 1,
    },
    {
        "name": "Torch",
        "desc": "A wax-soaked torch that burns for about an hour.",
        "value": 1,
    },
]


# ---------------------------------------------------------------------------
# Starter weapons
# ---------------------------------------------------------------------------

STARTER_WEAPONS = {
    "sword": {
        "name": "Wooden Practice Sword",
        "aliases": ["sword", "practice sword"],
        "desc": (
            "A blunt-edged sword carved from hardwood. It won't cut anything, "
            "but it'll leave a bruise. Every adventurer starts somewhere."
        ),
        "value": 5,
        "slot": "weapon",
        "damage_dice": "1d4",
        "damage_bonus": 0,
        "weapon_category": "sword",
        "weapon_type": "melee",
        "hands": 1,
    },
    "club": {
        "name": "Crude Wooden Club",
        "aliases": ["club"],
        "desc": (
            "A heavy length of knotted oak with leather wrapped around one end "
            "for a grip. Simple, brutal, effective."
        ),
        "value": 4,
        "slot": "weapon",
        "damage_dice": "1d6",
        "damage_bonus": 0,
        "weapon_category": "club",
        "weapon_type": "melee",
        "hands": 1,
    },
    "staff": {
        "name": "Light Wooden Staff",
        "aliases": ["staff"],
        "desc": (
            "A smooth ash staff, head-height and well-balanced. Good for "
            "walking, better for cracking skulls. Mages and monks favor these."
        ),
        "value": 4,
        "slot": "weapon",
        "damage_dice": "1d4",
        "damage_bonus": 1,
        "weapon_category": "staff",
        "weapon_type": "melee",
        "hands": 2,
    },
    "dagger": {
        "name": "Dull Iron Dagger",
        "aliases": ["dagger"],
        "desc": (
            "A short iron blade that's seen better days. The edge is gone, "
            "but the point still works. Quick in the right hands."
        ),
        "value": 3,
        "slot": "weapon",
        "damage_dice": "1d3",
        "damage_bonus": 1,
        "weapon_category": "dagger",
        "weapon_type": "melee",
        "hands": 1,
    },
}


# ---------------------------------------------------------------------------
# Item creation helpers
# ---------------------------------------------------------------------------

def _create_clothing(data, location):
    """Create an AwtownClothing item."""
    from typeclasses.items import AwtownClothing
    obj = create_object(AwtownClothing, key=data["name"], location=location)
    obj.db.desc = data["desc"]
    obj.db.value = data.get("value", 0)
    obj.db.clothing_type = data.get("clothing_type", "accessory")
    obj.db.stat_mods = data.get("stat_mods", {})
    if data.get("aliases"):
        for alias in data["aliases"]:
            obj.aliases.add(alias)
    return obj


def _create_consumable(data, location):
    """Create an AwtownConsumable item."""
    from typeclasses.items import AwtownConsumable
    obj = create_object(AwtownConsumable, key=data["name"], location=location)
    obj.db.desc = data["desc"]
    obj.db.value = data.get("value", 0)
    obj.db.nutrition = data.get("nutrition", 0)
    obj.db.hydration = data.get("hydration", 0)
    obj.db.hp_restore = data.get("hp_restore", 0)
    if data.get("aliases"):
        for alias in data["aliases"]:
            obj.aliases.add(alias)
    return obj


def _create_item(data, location):
    """Create a basic AwtownItem."""
    from typeclasses.items import AwtownItem
    obj = create_object(AwtownItem, key=data["name"], location=location)
    obj.db.desc = data["desc"]
    obj.db.value = data.get("value", 0)
    if data.get("aliases"):
        for alias in data["aliases"]:
            obj.aliases.add(alias)
    return obj


def _create_drinkable(data, location):
    """Create an AwtownDrinkable (multi-sip drink container)."""
    from typeclasses.items import AwtownDrinkable
    obj = create_object(AwtownDrinkable, key=data["name"], location=location)
    obj.db.desc = data["desc"]
    obj.db.value = data.get("value", 0)
    obj.db.sips = data.get("sips", 5)
    obj.db.sips_max = data.get("sips_max", 5)
    obj.db.hydration_per = data.get("hydration_per", 10)
    obj.db.hp_per = data.get("hp_per", 0)
    if data.get("aliases"):
        for alias in data["aliases"]:
            obj.aliases.add(alias)
    return obj


def _create_container(data, location):
    """Create an AwtownContainer (holds other items)."""
    from typeclasses.items import AwtownContainer
    obj = create_object(AwtownContainer, key=data["name"], location=location)
    obj.db.desc = data["desc"]
    obj.db.value = data.get("value", 0)
    obj.db.capacity = data.get("capacity", 10)
    if data.get("aliases"):
        for alias in data["aliases"]:
            obj.aliases.add(alias)
    return obj


def _create_weapon(data, location):
    """Create an AwtownWeapon."""
    from typeclasses.items import AwtownWeapon
    obj = create_object(AwtownWeapon, key=data["name"], location=location)
    obj.db.desc = data["desc"]
    obj.db.value = data.get("value", 0)
    obj.db.slot = data.get("slot", "weapon")
    obj.db.damage_dice = data.get("damage_dice", "1d4")
    obj.db.damage_bonus = data.get("damage_bonus", 0)
    obj.db.weapon_category = data.get("weapon_category", "sword")
    obj.db.weapon_type = data.get("weapon_type", "melee")
    obj.db.hands = data.get("hands", 1)
    obj.db.block_chance = data.get("block_chance", 0)
    obj.db.armor_bonus = data.get("armor_bonus", 0)
    if data.get("aliases"):
        for alias in data["aliases"]:
            obj.aliases.add(alias)
    return obj


# ---------------------------------------------------------------------------
# claim command
# ---------------------------------------------------------------------------

class CmdClaimKit(Command):
    """
    Claim your free starter kit from Shopkeep Marta.

    Usage:
        claim kit
        claim

    Available only at The Outfitter's Rest. Every new adventurer may
    claim one starter kit — basic clothing, food, torches, a waterskin,
    and 50 copper pieces to get you started.

    After claiming, ask Marta about weapons with |wchoose weapon|n.
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

        # Give clothing
        for data in STARTER_KIT_CLOTHING:
            _create_clothing(data, caller)

        # Give consumables (food)
        for data in STARTER_KIT_CONSUMABLES:
            _create_consumable(data, caller)

        # Give waterskin (multi-sip)
        _create_drinkable(STARTER_KIT_DRINKABLE, caller)

        # Give belt pouch (container)
        _create_container(STARTER_KIT_CONTAINER, caller)

        # Give general items (torches)
        for data in STARTER_KIT_ITEMS:
            _create_item(data, caller)

        # Give starting copper
        caller.give_money(50)

        # Mark as claimed
        caller.db.kit_claimed = True

        caller.msg(
            "|cMarta|n bustles about, pulling items from shelves and handing "
            "them to you one by one.\n\n"
            "  |wSimple Tunic, Simple Trousers, Belt Pouch,|n\n"
            "  |wThree Torches, Waterskin, Two Hunks of Bread.|n\n\n"
            "She presses a small purse of coins into your hand too.\n\n"
            "|cMarta|n says, \"|wNow you listen to me — eat something before "
            "you go out there, keep those torches dry, and don't talk to "
            "anything that glows in the dark. Come back in one piece.\"\n\n"
            "She glances at your empty hands.\n\n"
            "|cMarta|n says, \"|wYou'll want something to defend yourself with, "
            "too. Type |ychoose weapon|w to see what I've got.|n\"\n\n"
            "|gYou received the starter kit and 50 copper pieces.|n\n"
            "|gType |wchoose weapon|g to pick a free starter weapon.|n"
        )
        caller.location.msg_contents(
            f"|cMarta|n fusses over |w{caller.name}|n, pressing a starter kit "
            f"and some coin into their hands.",
            exclude=caller,
        )


# ---------------------------------------------------------------------------
# choose weapon command
# ---------------------------------------------------------------------------

class CmdChooseWeapon(Command):
    """
    Choose a free starter weapon from Shopkeep Marta.

    Usage:
        choose weapon           -- see available weapons
        choose sword            -- a wooden practice sword (1d4)
        choose club             -- a crude wooden club (1d6)
        choose staff            -- a light wooden staff (1d4+1)
        choose dagger           -- a dull iron dagger (1d3+1)

    Available at The Outfitter's Rest after claiming your starter kit.
    You may choose one free weapon. Choose wisely!

    The sword is balanced and reliable. The club hits hardest but is
    slow. The staff has reach and a small damage bonus. The dagger is
    quick and nimble.
    """

    key = "choose"
    aliases = ["choose weapon"]
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip().lower()

        # Check location
        loc = caller.location
        if not loc or not loc.tags.get(OUTFITTERS_TAG, category=ROOM_TAG_CAT):
            caller.msg(
                "You need to be at |wThe Outfitter's Rest|n to choose a weapon."
            )
            return

        # Must have claimed kit first
        if not caller.db.kit_claimed:
            caller.msg(
                "Claim your starter kit first with |wclaim kit|n."
            )
            return

        # Check if already chosen
        if caller.db.weapon_claimed:
            caller.msg(
                "|yMarta shakes her head. 'One weapon per adventurer, dear. "
                "You've already made your choice.'|n"
            )
            return

        # No args or "weapon" — show options
        if not args or args == "weapon":
            lines = [
                "|cMarta|n gestures to a rack of well-worn weapons.\n",
                "|cMarta|n says, \"|wPick one, dear. They're not fancy, "
                "but they'll keep you alive.\"\n",
                "|w  Available starter weapons:|n\n",
            ]
            for key, data in STARTER_WEAPONS.items():
                dice = data["damage_dice"]
                bonus = data["damage_bonus"]
                bonus_str = f"+{bonus}" if bonus > 0 else ""
                lines.append(
                    f"  |w{key:<8}|n — {data['name']} "
                    f"(|c{dice}{bonus_str}|n damage)"
                )
            lines.append(
                f"\nType |wchoose <weapon>|n to pick one. "
                f"E.g. |wchoose sword|n"
            )
            caller.msg("\n".join(lines))
            return

        # Look up the weapon
        weapon_data = STARTER_WEAPONS.get(args)
        if not weapon_data:
            caller.msg(
                f"'{args}' is not available. Choose from: "
                f"|w{', '.join(STARTER_WEAPONS.keys())}|n"
            )
            return

        # Create and give the weapon
        weapon = _create_weapon(weapon_data, caller)
        caller.db.weapon_claimed = True

        caller.msg(
            f"\n|cMarta|n pulls a |w{weapon.key}|n from the rack and "
            f"hands it to you.\n\n"
            f"|cMarta|n says, \"|wTreat it well and it'll treat you well. "
            f"Probably. Don't come crying to me if it breaks.\"\n\n"
            f"|gYou received: |w{weapon.key}|n |c({weapon_data['damage_dice']}"
            f"{'+' + str(weapon_data['damage_bonus']) if weapon_data['damage_bonus'] else ''}"
            f" damage)|n\n"
            f"|gType |wwield {weapon.key.lower()}|g to equip it.|n"
        )
        caller.location.msg_contents(
            f"|cMarta|n hands |w{caller.name}|n a {weapon.key}.",
            exclude=caller,
        )
