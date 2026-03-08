"""
DorfinMUD Item Typeclasses
==========================

Six item types used throughout Awtown and beyond.

    AwtownItem        -- Base item. All DorfinMUD objects inherit from this.
    AwtownClothing    -- Wearable item. Extends ContribClothing with stat mods.
    AwtownWeapon      -- Wieldable weapon. Goes into equipment slots.
    AwtownConsumable  -- Food or single-use drink. Deleted after consumption.
    AwtownDrinkable   -- Multi-sip drink container (waterskin, flask). Not
                         deleted — tracks remaining sips, can be refilled.
    AwtownContainer   -- Container that holds other items (belt pouch, chest).
                         Uses ContribContainer for put/get commands.

---

CLOTHING & STAT MODS
--------------------

AwtownClothing extends ContribClothing (which handles wear/remove/layering).
On top of that, items can carry stat modifiers via db.stat_mods.

    item.db.stat_mods = {"dex": -2, "armor_bonus": 15}

When worn, the item's stat mods are applied as a buff to the wearer.
When removed, the buff is cleared.

The buff key is derived from the item's dbref so each item has a unique buff:
    "armor_<dbref>"   e.g. "armor_#42"

---

CREATING ITEMS
--------------

Use evennia.create_object() with the appropriate typeclass:

    from evennia import create_object

    tunic = create_object("typeclasses.items.AwtownClothing", key="simple tunic", location=character)
    tunic.db.clothing_type = "top"
    tunic.db.desc = "A plain linen tunic."
    tunic.db.value = 2

    jerkin = create_object("typeclasses.items.AwtownClothing", key="leather jerkin", location=character)
    jerkin.db.clothing_type = "top"
    jerkin.db.stat_mods = {"armor_bonus": 8}
    jerkin.db.value = 40

    sword = create_object("typeclasses.items.AwtownWeapon", key="short sword", location=character)
    sword.db.slot = "weapon"
    sword.db.damage_dice = "1d6"
    sword.db.value = 25

    bread = create_object("typeclasses.items.AwtownConsumable", key="hunk of bread", location=character)
    bread.db.nutrition = 20
    bread.db.value = 1

---

CLOTHING TYPES
--------------

Valid values for db.clothing_type:
    hat, jewelry, cloak, top, undershirt, gloves, fullbody,
    bottom, underpants, socks, shoes, accessory
"""

from evennia.objects.objects import DefaultObject

try:
    from evennia.contrib.game_systems.clothing.clothing import ContribClothing
    _CLOTHING_AVAILABLE = True
except ImportError:
    ContribClothing = DefaultObject
    _CLOTHING_AVAILABLE = False

try:
    from evennia.contrib.rpg.buffs import BaseBuff, Mod, BuffHandler
    _BUFFS_AVAILABLE = True
except ImportError:
    BaseBuff = object
    Mod = None
    BuffHandler = None
    _BUFFS_AVAILABLE = False


# ---------------------------------------------------------------------------
# AwtownItem -- base
# ---------------------------------------------------------------------------

class AwtownItem(DefaultObject):
    """
    Base typeclass for all DorfinMUD items.

    Attributes:
        db.desc   (str) -- description shown when examined
        db.value  (int) -- base value in copper coins
        db.weight (int) -- weight in arbitrary units
    """

    def at_object_creation(self):
        super().at_object_creation()
        if self.db.value is None:
            self.db.value = 0
        if self.db.weight is None:
            self.db.weight = 1

    def get_display_name(self, looker, **kwargs):
        return f"|w{self.key}|n"

    def return_appearance(self, looker, **kwargs):
        desc = self.db.desc or "You see nothing remarkable about it."
        value = self.db.value or 0
        return f"|w{self.key}|n\n{desc}\n|yValue: {value} copper|n"


# ---------------------------------------------------------------------------
# AwtownClothing -- wearable with optional stat mods
# ---------------------------------------------------------------------------

class AwtownClothing(ContribClothing):
    """
    Wearable clothing or armour.

    Extends ContribClothing with stat modifier support. When worn, any
    stat_mods are applied to the wearer as a buff. When removed, cleared.

    Attributes:
        db.clothing_type (str)  -- clothing slot (hat/top/bottom/etc.)
        db.desc          (str)  -- description
        db.value         (int)  -- copper value
        db.weight        (int)  -- weight
        db.stat_mods     (dict) -- stat modifiers applied on wear
                                   e.g. {"armor_bonus": 10, "dex": -1}
    """

    def at_object_creation(self):
        super().at_object_creation()
        if self.db.value is None:
            self.db.value = 0
        if self.db.weight is None:
            self.db.weight = 1
        if self.db.stat_mods is None:
            self.db.stat_mods = {}

    def _buff_key(self):
        return f"armor_{self.dbref}"

    def wear(self, wearer, wearstyle, quiet=False):
        super().wear(wearer, wearstyle, quiet=quiet)
        self._apply_stat_mods(wearer)

    def remove(self, wearer, quiet=False):
        self._remove_stat_mods(wearer)
        super().remove(wearer, quiet=quiet)

    def _apply_stat_mods(self, wearer):
        if not _BUFFS_AVAILABLE:
            return
        if not hasattr(wearer, "buffs") or not wearer.buffs:
            return
        stat_mods = self.db.stat_mods or {}
        if not stat_mods:
            return
        buff_key = self._buff_key()
        mods = [Mod(stat, "add", val) for stat, val in stat_mods.items()]
        buff_cls = _make_armour_buff(buff_key, self.key, mods)
        wearer.buffs.add(buff_cls)

    def _remove_stat_mods(self, wearer):
        if not _BUFFS_AVAILABLE:
            return
        if not hasattr(wearer, "buffs") or not wearer.buffs:
            return
        buff_key = self._buff_key()
        if wearer.buffs.has(buff_key):
            wearer.buffs.remove(buff_key)

    def return_appearance(self, looker, **kwargs):
        desc = self.db.desc or "Ordinary clothing."
        value = self.db.value or 0
        stat_mods = self.db.stat_mods or {}
        lines = [f"|w{self.key}|n", desc]
        if stat_mods:
            mod_parts = []
            for stat, val in stat_mods.items():
                sign = "+" if val >= 0 else ""
                mod_parts.append(f"{stat} {sign}{val}")
            lines.append("|cStats: " + ", ".join(mod_parts) + "|n")
        lines.append(f"|yValue: {value} copper|n")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# AwtownWeapon -- wieldable weapon
# ---------------------------------------------------------------------------

class AwtownWeapon(AwtownItem):
    """
    A wieldable weapon for the weapon or offhand equipment slot.

    Attributes:
        db.slot          (str) -- "weapon" or "offhand"
        db.damage_dice   (str) -- e.g. "1d6", "2d4"
        db.damage_bonus  (int) -- flat bonus to damage rolls
        db.desc          (str) -- description
        db.value         (int) -- copper value
    """

    def at_object_creation(self):
        super().at_object_creation()
        if self.db.slot is None:
            self.db.slot = "weapon"
        if self.db.damage_dice is None:
            self.db.damage_dice = "1d4"
        if self.db.damage_bonus is None:
            self.db.damage_bonus = 0

    def return_appearance(self, looker, **kwargs):
        desc = self.db.desc or "A weapon of some kind."
        value = self.db.value or 0
        dice = self.db.damage_dice or "1d4"
        bonus = self.db.damage_bonus or 0
        bonus_str = f" +{bonus}" if bonus > 0 else (f" {bonus}" if bonus < 0 else "")
        lines = [
            f"|w{self.key}|n",
            desc,
            f"|cDamage: {dice}{bonus_str}|n",
            f"|yValue: {value} copper|n",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# AwtownConsumable -- food and drink
# ---------------------------------------------------------------------------

class AwtownConsumable(AwtownItem):
    """
    A consumable item -- food, drink, or healing potion.

    Consumed by CmdEat / CmdDrink (command_eat.py).
    The command calls character.restore_hunger() / restore_thirst()
    and character.heal(), then deletes the item.

    Attributes:
        db.nutrition  (int) -- hunger restored (0-100)
        db.hydration  (int) -- thirst restored (0-100)
        db.hp_restore (int) -- HP restored on consumption
        db.desc       (str) -- description
        db.value      (int) -- copper value
    """

    def at_object_creation(self):
        super().at_object_creation()
        if self.db.nutrition is None:
            self.db.nutrition = 0
        if self.db.hydration is None:
            self.db.hydration = 0
        if self.db.hp_restore is None:
            self.db.hp_restore = 0

    def return_appearance(self, looker, **kwargs):
        desc = self.db.desc or "Something edible."
        value = self.db.value or 0
        lines = [f"|w{self.key}|n", desc]
        details = []
        if self.db.nutrition:
            details.append(f"Hunger: +{self.db.nutrition}")
        if self.db.hydration:
            details.append(f"Thirst: +{self.db.hydration}")
        if self.db.hp_restore:
            details.append(f"Health: +{self.db.hp_restore}")
        if details:
            lines.append("|c" + "  ".join(details) + "|n")
        lines.append(f"|yValue: {value} copper|n")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# AwtownDrinkable -- multi-sip drink container
# ---------------------------------------------------------------------------

class AwtownDrinkable(AwtownItem):
    """
    A drink container with multiple sips (waterskin, flask, bottle).

    Unlike AwtownConsumable, this item is NOT destroyed after one use.
    Each drink reduces db.sips by 1. When sips reach 0, the item is
    empty and must be refilled (at a well, inn, etc.) or discarded.

    Consumed by CmdDrink (command_eat.py) which checks for this
    typeclass before checking AwtownConsumable.

    Attributes:
        db.sips           (int) -- remaining sips (default 5)
        db.sips_max       (int) -- maximum sips when full (default 5)
        db.hydration_per  (int) -- thirst restored per sip (default 10)
        db.hp_per         (int) -- HP restored per sip (default 0)
        db.desc           (str) -- description
        db.value          (int) -- copper value

    Creating:
        waterskin = create_object("typeclasses.items.AwtownDrinkable",
                                  key="Waterskin", location=character)
        waterskin.db.sips = 5
        waterskin.db.sips_max = 5
        waterskin.db.hydration_per = 10
    """

    def at_object_creation(self):
        super().at_object_creation()
        if self.db.sips is None:
            self.db.sips = 5
        if self.db.sips_max is None:
            self.db.sips_max = 5
        if self.db.hydration_per is None:
            self.db.hydration_per = 10
        if self.db.hp_per is None:
            self.db.hp_per = 0

    def drink_sip(self, drinker):
        """
        Consume one sip. Apply hydration and HP to the drinker.

        Args:
            drinker: The character drinking.

        Returns:
            tuple: (success: bool, message: str)
        """
        sips = self.db.sips or 0
        if sips <= 0:
            return False, f"{self.key} is empty."

        self.db.sips = sips - 1
        remaining = self.db.sips

        # Apply effects
        hydration = self.db.hydration_per or 0
        hp = self.db.hp_per or 0

        if hydration and hasattr(drinker, "restore_thirst"):
            new_thirst = drinker.restore_thirst(hydration)
            if new_thirst is not None and new_thirst > 75:
                drinker.msg("|gYou feel refreshed.|n")

        if hp and hasattr(drinker, "heal"):
            drinker.heal(hp)
            drinker.msg(f"|gYou recover {hp} health.|n")

        # Status message
        if remaining <= 0:
            status = f"|y{self.key} is now empty.|n"
        elif remaining == 1:
            status = f"|y{self.key} has one sip left.|n"
        else:
            status = f"{self.key} has {remaining} sips remaining."

        return True, status

    def refill(self, amount=None):
        """
        Refill the container.

        Args:
            amount (int): Sips to add. Defaults to full.

        Returns:
            int: New sip count.
        """
        if amount is None:
            self.db.sips = self.db.sips_max
        else:
            self.db.sips = min(self.db.sips_max, (self.db.sips or 0) + amount)
        return self.db.sips

    def return_appearance(self, looker, **kwargs):
        desc = self.db.desc or "A drink container."
        value = self.db.value or 0
        sips = self.db.sips or 0
        sips_max = self.db.sips_max or 5

        if sips <= 0:
            fill = "|rempty|n"
        elif sips >= sips_max:
            fill = "|gfull|n"
        else:
            fill = f"|y{sips}/{sips_max} sips|n"

        lines = [f"|w{self.key}|n", desc, f"  Status: {fill}"]
        if self.db.hydration_per:
            lines.append(f"  |cThirst per sip: +{self.db.hydration_per}|n")
        lines.append(f"|yValue: {value} copper|n")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# AwtownContainer -- items that hold other items
# ---------------------------------------------------------------------------

try:
    from evennia.contrib.game_systems.containers.containers import ContribContainer
    _CONTAINERS_AVAILABLE = True
except ImportError:
    ContribContainer = DefaultObject
    _CONTAINERS_AVAILABLE = False


class AwtownContainer(ContribContainer if _CONTAINERS_AVAILABLE else AwtownItem):
    """
    A container item that can hold other items inside it.

    Uses the ContribContainer from evennia.contrib.game_systems.containers
    which provides 'put X in Y' and 'get X from Y' commands.

    Attributes:
        db.capacity   (int) -- maximum number of items (default 10)
        db.desc       (str) -- description
        db.value      (int) -- copper value

    Creating:
        pouch = create_object("typeclasses.items.AwtownContainer",
                              key="Belt Pouch", location=character)
        pouch.db.capacity = 10
        pouch.db.desc = "A small leather pouch."

    Players can then:
        put coin in pouch
        get coin from pouch
        look in pouch
    """

    def at_object_creation(self):
        super().at_object_creation()
        if self.db.value is None:
            self.db.value = 0
        if self.db.weight is None:
            self.db.weight = 1
        if self.db.capacity is None:
            self.db.capacity = 10

    def at_pre_put_in(self, putter, obj_to_put, **kwargs):
        """
        Called before an object is put into this container.
        Checks capacity.
        """
        capacity = self.db.capacity or 10
        current = len([o for o in self.contents if o != self])
        if current >= capacity:
            putter.msg(f"{self.key} is full.")
            return False
        return True

    def get_display_name(self, looker, **kwargs):
        return f"|w{self.key}|n"

    def return_appearance(self, looker, **kwargs):
        desc = self.db.desc or "A container."
        value = self.db.value or 0
        lines = [f"|w{self.key}|n", desc]

        contents = [obj for obj in self.contents if obj != self]
        if contents:
            lines.append("\n|wContains:|n")
            for obj in contents:
                name = obj.get_display_name(looker) if hasattr(obj, "get_display_name") else obj.key
                lines.append(f"  {name}")
        else:
            lines.append("\n|xEmpty.|n")

        lines.append(f"|yValue: {value} copper|n")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Dynamic buff class factory
# ---------------------------------------------------------------------------

def _make_armour_buff(buff_key, item_name, mods):
    """
    Dynamically create a BaseBuff subclass for a specific item's stat mods.

    Each wearable item needs its own buff class with its own unique key,
    because BaseBuff stores config as class attributes, not instance attrs.

    Args:
        buff_key (str): Unique key derived from item dbref, e.g. "armor_#42".
        item_name (str): Human-readable item name.
        mods (list): List of Mod objects.

    Returns:
        type: A new BaseBuff subclass, or None if buffs unavailable.
    """
    if not _BUFFS_AVAILABLE:
        return None

    return type(
        f"ArmourBuff_{buff_key}",
        (BaseBuff,),
        {
            "key":      buff_key,
            "name":     f"{item_name} (equipped)",
            "flavor":   f"You are wearing {item_name}.",
            "duration": -1,
            "unique":   True,
            "refresh":  False,
            "mods":     mods,
        }
    )
