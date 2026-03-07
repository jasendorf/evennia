"""
DorfinMUD Item Typeclasses
==========================

Four item types used throughout Awtown and beyond.

    AwtownItem        -- Base item. All DorfinMUD objects inherit from this.
    AwtownClothing    -- Wearable item. Extends ContribClothing with stat mods.
    AwtownWeapon      -- Wieldable weapon. Goes into equipment slots.
    AwtownConsumable  -- Food or drink. Restores hunger/thirst/HP when eaten.

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
