"""
AwtownCharacter — DorfinMUD Character Typeclass
================================================

Central hub that wires together:

    - ClothedCharacter   (evennia.contrib.game_systems.clothing)
    - TraitHandler       (evennia.contrib.rpg.traits)
    - BuffHandler        (evennia.contrib.rpg.buffs)
    - CooldownHandler    (evennia.contrib.game_systems.cooldowns)
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

Combat (Phase 5):
    db.xp            — int, experience points (default 0)
    db.level         — int, character level (default 1)
    db.wimpy         — int, auto-flee HP threshold (0 = disabled)
    db.in_combat     — bool, set by CombatHandler during fights
    db.combat_target — obj ref, set by CombatHandler

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

# Cooldowns contrib — rescue cooldown, future ability cooldowns
try:
    from evennia.contrib.game_systems.cooldowns import CooldownHandler
    _COOLDOWNS_AVAILABLE = True
except ImportError:
    CooldownHandler = None
    _COOLDOWNS_AVAILABLE = False

# DorfinMUD needs (hunger + thirst)
from contrib_dorfin.dorfin_needs import DorfinNeedsMixin

# DorfinMUD party (autoassist, combat-aware callbacks)
from contrib_dorfin.dorfin_party import DorfinPartyMixin


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COPPER_PER_SILVER = 100
COPPER_PER_GOLD = 10000


def format_money(total_copper):
    """Format a copper amount as gold/silver/copper string (e.g. '2g 50s 10c')."""
    if total_copper <= 0:
        return "0c"
    gold = total_copper // COPPER_PER_GOLD
    silver = (total_copper % COPPER_PER_GOLD) // COPPER_PER_SILVER
    copper = total_copper % COPPER_PER_SILVER
    parts = []
    if gold:
        parts.append(f"{gold}g")
    if silver:
        parts.append(f"{silver}s")
    if copper or not parts:
        parts.append(f"{copper}c")
    return " ".join(parts)


XP_DEATH_PENALTY = 0.10   # lose 10% of XP on death
RESPAWN_HP_RATIO = 0.25   # respawn with 25% of max HP
RESPAWN_ROOM_TAG = "temple_nw"   # tag on the room to respawn in
RESPAWN_TAG_CATEGORY = "awtown_dbkey"


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

class AwtownCharacter(DorfinPartyMixin, DorfinNeedsMixin, ClothedCharacter):
    """
    The DorfinMUD player character typeclass.

    Inherits (MRO order):
        DorfinPartyMixin  -> PartyCharacterMixin -> (party system)
        DorfinNeedsMixin  -> NeedsCharacterMixin -> (needs system)
        ClothedCharacter  -> DefaultCharacter     -> (clothing + base Evennia)

    Properties available after at_object_creation:
        self.traits         -- TraitHandler    (HP, 10 base stats)
        self.buffs          -- BuffHandler     (founder buffs, armour mods, need penalties)
        self.needs          -- NeedsHandler    (hunger, thirst -- via DorfinNeedsMixin)
        self.cooldowns      -- CooldownHandler (rescue, future ability cooldowns)
        self.party_handler  -- PartyHandler    (party system -- via DorfinPartyMixin)

    Attributes set at creation:
        db.copper            -- int, currency (default 0)
        db.equipment         -- dict, worn weapon/armour slots
        db.kit_claimed       -- bool, starter kit flag
        db.founder_cooldowns -- dict, used by command_founder.py
        db.xp                -- int, experience points (default 0)
        db.level             -- int, character level (default 1)
        db.wimpy             -- int, auto-flee threshold (default 0 = disabled)
        db.in_combat         -- bool, currently in combat (managed by CombatHandler)
        db.combat_target     -- dbref, current combat target (managed by CombatHandler)
        db.autoassist        -- bool, auto-join party combat (default False)
        db.party_id          -- int, Party script ID if in a party (managed by PartyHandler)
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

    @lazy_property
    def cooldowns(self):
        """CooldownHandler for combat abilities and rate-limited actions."""
        if _COOLDOWNS_AVAILABLE:
            return CooldownHandler(self, db_attribute="cooldowns")
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
        self._init_combat()
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

    def _init_combat(self):
        """Initialise combat and party-related attributes."""
        if self.db.xp is None:
            self.db.xp = 0
        if self.db.level is None:
            self.db.level = 1
        if self.db.wimpy is None:
            self.db.wimpy = 0
        if self.db.in_combat is None:
            self.db.in_combat = False
        if self.db.combat_target is None:
            self.db.combat_target = None
        if self.db.autoassist is None:
            self.db.autoassist = False
        if self.db.party_id is None:
            self.db.party_id = None

    def _init_flags(self):
        """Initialise one-time flags."""
        if self.db.kit_claimed is None:
            self.db.kit_claimed = False
        if not self.db.founder_cooldowns:
            self.db.founder_cooldowns = {}
        if self.db.languages is None:
            self.db.languages = {"common": 1.0}
        if self.db.is_resting is None:
            self.db.is_resting = False
        if self.db.is_renting is None:
            self.db.is_renting = False

    # ------------------------------------------------------------------
    # Reload / puppet hooks
    # ------------------------------------------------------------------

    def at_init(self):
        """
        Called on every server reload. Ensures BuffHandler is initialised
        before any hot-reload issues can arise. Also cleans up orphaned
        rest/rent state left by non-persistent scripts lost during reload.
        """
        super().at_init()
        if _BUFFS_AVAILABLE:
            _ = self.buffs

        self._cleanup_orphaned_rest_rent()

    def _cleanup_orphaned_rest_rent(self):
        """Clear rest/rent flags left behind when non-persistent scripts are lost."""
        if self.db.is_resting and not self.scripts.get("RestScript"):
            self.db.is_resting = False
            try:
                self.cmdset.remove("RestCmdSet")
            except Exception:
                pass
        if self.db.is_renting and not self.scripts.get("RentScript"):
            self.db.is_renting = False
            try:
                self.cmdset.remove("RentCmdSet")
            except Exception:
                pass

    def at_post_puppet(self, **kwargs):
        """
        Called after a player puppets this character.
        Restarts needs script and re-registers callbacks.
        """
        super().at_post_puppet(**kwargs)
        self._cleanup_orphaned_rest_rent()

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

    def is_alive(self):
        """Return True if this character has HP remaining."""
        return self.get_hp() > 0

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

    # ------------------------------------------------------------------
    # Death
    # ------------------------------------------------------------------

    def at_death(self):
        """
        Called when HP reaches 0.

        Death flow:
            1. Lose XP_DEATH_PENALTY (10%) of current XP.
            2. Display death message.
            3. Teleport to The Nave (temple_nw).
            4. Restore HP to RESPAWN_HP_RATIO (25%) of max.
            5. Combat handler removes us from the fight.
        """
        # 1. XP penalty
        current_xp = self.db.xp or 0
        if current_xp > 0:
            xp_lost = max(1, int(current_xp * XP_DEATH_PENALTY))
            self.db.xp = max(0, current_xp - xp_lost)
            xp_msg = f"You lost |r{xp_lost}|n experience points."
        else:
            xp_msg = ""

        # 2. Death message
        self.msg(
            "\n|r" + "=" * 50 + "|n\n"
            "|r  You have been defeated!|n\n"
            "|r  The world goes dark...|n\n"
            "|r" + "=" * 50 + "|n\n"
        )
        if xp_msg:
            self.msg(xp_msg)

        # 3. Teleport to respawn point
        respawn_room = self._find_respawn_room()
        if respawn_room and respawn_room != self.location:
            # Move quietly — we'll describe the arrival ourselves
            self.move_to(respawn_room, quiet=True, move_type="teleport")
            self.msg(
                "\n|xYou awaken on a cold stone floor. Torchlight flickers above.\n"
                "The priests of the Temple have pulled you back from the brink.|n\n"
            )
            respawn_room.msg_contents(
                f"|x{self.name} materialises on the floor, gasping for breath.|n",
                exclude=[self],
            )

        # 4. Restore HP to 25% of max
        hp_max = self.get_hp_max()
        respawn_hp = max(1, int(hp_max * RESPAWN_HP_RATIO))
        if _TRAITS_AVAILABLE and self.traits and self.traits.get("hp"):
            self.traits.hp.current = respawn_hp
        else:
            self.db.hp = respawn_hp

        self.msg(f"|yYou have {respawn_hp}/{hp_max} HP. Rest and recover.|n")

        # 5. Clear combat state (CombatHandler also does this, but be safe)
        self.db.in_combat = False
        self.db.combat_target = None

    def _find_respawn_room(self):
        """
        Find the respawn room (The Nave — temple_nw).

        Returns:
            Room object, or None if not found.
        """
        try:
            import evennia
            results = evennia.search_tag(RESPAWN_ROOM_TAG, category=RESPAWN_TAG_CATEGORY)
            return results[0] if results else None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Currency helpers
    # ------------------------------------------------------------------

    def money_string(self):
        """Return this character's purse formatted as gold/silver/copper."""
        return format_money(self.db.copper or 0)

    def give_money(self, amount):
        """Add copper to this character's purse."""
        self.db.copper = (self.db.copper or 0) + amount

    give_copper = give_money  # alias

    def spend_money(self, amount):
        """
        Deduct copper. Returns True on success, False if insufficient funds.

        Args:
            amount (int): Amount in copper to spend.

        Returns:
            bool: True if the character had enough funds.
        """
        current = self.db.copper or 0
        if current < amount:
            return False
        self.db.copper = current - amount
        return True

    spend_copper = spend_money  # alias

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
