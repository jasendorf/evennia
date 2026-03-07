"""
AwtownCharacter — DorfinMUD Character Typeclass
================================================

Central hub that wires together:

    - ClothedCharacter   (evennia.contrib.game_systems.clothing)
    - TraitHandler       (evennia.contrib.rpg.traits)
    - BuffHandler        (evennia.contrib.rpg.buffs)
    - DorfinNeedsMixin   (contrib_dorfin.dorfin_needs)

Character stats (10):
    STR, DEX, AGI, CON, END, INT, WIS, PER, CHA, LCK

All stats are TraitHandler "static" traits with a base of 10.
HP is a "gauge" trait (min 0, max 100).

Currency:
    db.copper — integer, initialised to 0.
    The starter kit command (CmdClaimKit) grants 50 copper on first claim.

Equipment slots:
    db.equipment — dict mapping slot name to object dbref or None.
    Slots: weapon, offhand, head, chest, legs, feet, hands.

Starter kit flag:
    db.kit_claimed — bool, False until CmdClaimKit is used.
"""

from evennia.utils import lazy_property

# Clothing contrib — provides wear/remove commands and layering
try:
    from evennia.contrib.game_systems.clothing.clothing import ClothedCharacter
    _CLOTHING_AVAILABLE = True
except ImportError:
    from evennia.objects.objects import DefaultCharacter as ClothedCharacter
    _CLOTHING_AVAILABLE = False

# Traits contrib — HP and base stats
try:
    from evennia.contrib.rpg.traits import TraitHandler
    _TRAITS_AVAILABLE = True
except ImportError:
    TraitHandler = None
    _TRAITS_AVAILABLE = False

# Buffs contrib — founder buffs, armour mods, need penalties
try:
    from evennia.contrib.rpg.buffs import BuffHandler
    _BUFFS_AVAILABLE = True
except ImportError:
    BuffHandler = None
    _BUFFS_AVAILABLE = False

# DorfinMUD needs (hunger + thirst)
from contrib_dorfin.dorfin_needs import DorfinNeedsMixin


# ---------------------------------------------------------------------------
# Stat definitions
# ---------------------------------------------------------------------------

BASE_STATS = [
    ("str", "Strength",     "Carry weight, melee damage, grappling."),
    ("dex", "Dexterity",    "Precision: archery, lockpicking, sleight of hand."),
    ("agi", "Agility",      "Speed: dodge, flee chance, initiative."),
    ("con", "Constitution", "Hit points, disease/poison resistance."),
    ("end", "Endurance",    "Stamina: sustained effort, travel fatigue."),
    ("int", "Intelligence", "Spell power, learning speed, crafting complexity."),
    ("wis", "Wisdom",       "Mana pool, clerical power, mental resistance."),
    ("per", "Perception",   "Spot hidden exits, detect traps, scan range."),
    ("cha", "Charisma",     "NPC reactions, prices, persuasion."),
    ("lck", "Luck",         "Crits, rare drops, random event outcomes."),
]

BASE_STAT_VALUE = 10

EQUIPMENT_SLOTS = ["weapon", "offhand", "head", "chest", "legs", "feet", "hands"]


# ---------------------------------------------------------------------------
# AwtownCharacter
# ---------------------------------------------------------------------------

class AwtownCharacter(DorfinNeedsMixin, ClothedCharacter):
    """
    The DorfinMUD player character typeclass.

    Inherits (MRO order):
        DorfinNeedsMixin  -> NeedsCharacterMixin -> (needs system)
        ClothedCharacter  -> DefaultCharacter     -> (clothing + base Evennia)

    Properties available after at_object_creation:
        self.traits   -- TraitHandler (HP, 10 base stats)
        self.buffs    -- BuffHandler  (founder buffs, armour mods, need penalties)
        self.needs    -- NeedsHandler (hunger, thirst -- via DorfinNeedsMixin)

    Attributes set at creation:
        db.copper           -- int, currency (default 0)
        db.equipment        -- dict, worn weapon/armour slots
        db.kit_claimed      -- bool, starter kit flag
        db.founder_cooldowns -- dict, used by command_founder.py
    """

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    @lazy_property
    def traits(self):
        """TraitHandler for HP and base stats."""
        if _TRAITS_AVAILABLE:
            return TraitHandler(self, db_attribute_key="traits")
        return None

    @lazy_property
    def buffs(self):
        """BuffHandler for all temporary and permanent buffs."""
        if _BUFFS_AVAILABLE:
            return BuffHandler(self)
        return None

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def at_object_creation(self):
        """
        Called once when the character is first created.
        Sets up all systems with default values.
        """
        super().at_object_creation()  # DorfinNeedsMixin -> ClothedCharacter chain

        self._init_traits()
        self._init_currency()
        self._init_equipment()
        self._init_flags()

    def _init_traits(self):
        """Initialise HP gauge and the 10 base stats."""
        if not _TRAITS_AVAILABLE or self.traits is None:
            return

        # HP -- gauge trait (current / max)
        self.traits.add(
            "hp",
            trait_type="gauge",
            name="Health",
            min=0,
            max=100,
            base=100,
            desc="Hit points. Reach 0 and you die.",
        )

        # 10 base stats -- static traits (base value, modified by buffs/gear)
        for key, name, desc in BASE_STATS:
            self.traits.add(
                key,
                trait_type="static",
                name=name,
                base=BASE_STAT_VALUE,
                desc=desc,
            )

    def _init_currency(self):
        """Initialise copper to 0. Starter kit grants 50 on first claim."""
        if self.db.copper is None:
            self.db.copper = 0

    def _init_equipment(self):
        """Initialise all equipment slots to None."""
        if not self.db.equipment:
            self.db.equipment = {slot: None for slot in EQUIPMENT_SLOTS}

    def _init_flags(self):
        """Initialise one-time flags."""
        if self.db.kit_claimed is None:
            self.db.kit_claimed = False
        if not self.db.founder_cooldowns:
            self.db.founder_cooldowns = {}

    # ------------------------------------------------------------------
    # Reload / puppet hooks
    # ------------------------------------------------------------------

    def at_init(self):
        """
        Called on every server reload. Ensures BuffHandler is initialised
        before any hot-reload issues can arise.
        """
        super().at_init()
        if _BUFFS_AVAILABLE:
            _ = self.buffs

    def at_post_puppet(self, **kwargs):
        """
        Called after a player puppets this character.
        Restarts needs script and re-registers callbacks.
        """
        super().at_post_puppet(**kwargs)

    # ------------------------------------------------------------------
    # Stat helpers
    # ------------------------------------------------------------------

    def get_stat(self, stat_key):
        """
        Return the current (buff-modified) value of a base stat.

        Uses buffs.check() so any active Mod objects are applied.
        Falls back to the trait base value if buffs are unavailable.

        Args:
            stat_key (str): One of str/dex/agi/con/end/int/wis/per/cha/lck.

        Returns:
            int: The effective stat value.
        """
        if _TRAITS_AVAILABLE and self.traits:
            base = self.traits.get(stat_key)
            base_val = base.value if base else BASE_STAT_VALUE
        else:
            base_val = BASE_STAT_VALUE

        if _BUFFS_AVAILABLE and self.buffs:
            return int(self.buffs.check(base_val, stat_key))

        return base_val

    def get_hp(self):
        """Return current HP."""
        if _TRAITS_AVAILABLE and self.traits and self.traits.get("hp"):
            return int(self.traits.hp.current)
        return self.db.hp or 100

    def get_hp_max(self):
        """Return maximum HP."""
        if _TRAITS_AVAILABLE and self.traits and self.traits.get("hp"):
            return int(self.traits.hp.max)
        return 100

    def heal(self, amount):
        """
        Restore HP by amount, capped at max.

        Args:
            amount (int): HP to restore.

        Returns:
            int: New HP value.
        """
        if _TRAITS_AVAILABLE and self.traits and self.traits.get("hp"):
            self.traits.hp.current = min(
                self.traits.hp.max,
                self.traits.hp.current + amount
            )
            return int(self.traits.hp.current)
        return self.get_hp()

    def take_damage(self, amount, source=None):
        """
        Apply damage to this character, after checking buff modifiers.

        Args:
            amount (int): Raw incoming damage.
            source: The damage source (object, or None).

        Returns:
            int: Actual damage dealt (after mitigation).
        """
        if _BUFFS_AVAILABLE and self.buffs:
            actual = int(self.buffs.check(amount, "taken_damage"))
        else:
            actual = amount

        if _TRAITS_AVAILABLE and self.traits and self.traits.get("hp"):
            self.traits.hp.current = max(0, self.traits.hp.current - actual)
            if self.traits.hp.current <= 0:
                self.at_death()
        else:
            current = self.db.hp or 100
            self.db.hp = max(0, current - actual)

        return actual

    def at_death(self):
        """
        Called when HP reaches 0. Placeholder for Phase 5 (combat).
        Sends a message and restores HP to 1.
        """
        self.msg("|rYou have been defeated!|n")
        # Temporary -- full death handling in Phase 5
        if _TRAITS_AVAILABLE and self.traits and self.traits.get("hp"):
            self.traits.hp.current = 1

    # ------------------------------------------------------------------
    # Currency helpers
    # ------------------------------------------------------------------

    def give_copper(self, amount):
        """Add copper to this character's wallet."""
        self.db.copper = (self.db.copper or 0) + amount

    def spend_copper(self, amount):
        """
        Deduct copper. Returns True on success, False if insufficient funds.

        Args:
            amount (int): Amount to spend.

        Returns:
            bool: True if the character had enough copper.
        """
        current = self.db.copper or 0
        if current < amount:
            return False
        self.db.copper = current - amount
        return True

    # ------------------------------------------------------------------
    # Equipment helpers
    # ------------------------------------------------------------------

    def get_equipment(self):
        """Return the equipment dict, initialising if absent."""
        if not self.db.equipment:
            self._init_equipment()
        return self.db.equipment

    def equip(self, slot, item):
        """
        Place an item in an equipment slot.

        Args:
            slot (str): One of EQUIPMENT_SLOTS.
            item: The item object to equip, or None to clear the slot.

        Returns:
            bool: True on success.
        """
        eq = self.get_equipment()
        if slot not in eq:
            return False
        eq[slot] = item.dbref if item else None
        self.db.equipment = eq
        return True

    def unequip(self, slot):
        """Clear an equipment slot. Returns the item dbref that was there."""
        eq = self.get_equipment()
        old = eq.get(slot)
        eq[slot] = None
        self.db.equipment = eq
        return old

    def get_equipped(self, slot):
        """
        Return the item object currently in a slot, or None.

        Args:
            slot (str): Equipment slot name.

        Returns:
            Object or None.
        """
        eq = self.get_equipment()
        dbref = eq.get(slot)
        if not dbref:
            return None
        from evennia import search_object
        results = search_object(dbref)
        return results[0] if results else None


# ---------------------------------------------------------------------------
# Alias -- Evennia looks for `Character` in typeclasses.characters
# ---------------------------------------------------------------------------

Character = AwtownCharacter
