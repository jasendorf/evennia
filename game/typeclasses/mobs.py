"""
DorfinMUD Mob Typeclass
========================

AwtownMob extends AwtownNPC with combat capabilities: HP, stats, loot,
XP value, and death handling. This is the typeclass for all killable
creatures in DorfinMUD.

Mobs do NOT use TraitHandler or BuffHandler — their stats are stored as
simple db attributes for performance and simplicity. The combat rules
engine reads them via get_stat() / get_hp() / get_hp_max(), which match
the same interface as AwtownCharacter.

Creating a mob
--------------

    from evennia import create_object

    goblin = create_object(
        "typeclasses.mobs.AwtownMob",
        key="a goblin",
        location=some_room,
    )
    goblin.db.stats = {"str": 8, "dex": 12, "agi": 14, "con": 8,
                       "end": 8, "int": 6, "wis": 6, "per": 10,
                       "cha": 4, "lck": 8}
    goblin.db.hp_max = 30
    goblin.db.hp = 30
    goblin.db.level = 2
    goblin.db.xp_value = 50
    goblin.db.damage_dice = "1d6"
    goblin.db.armor_bonus = 2
    goblin.db.loot_table = [
        {"prototype": "rusty_dagger", "chance": 0.3},
        {"prototype": "copper_coins_small", "chance": 0.8},
    ]

Loot table
----------

Each entry in db.loot_table is a dict:
    prototype (str) : Prototype key to spawn via evennia.utils.spawner.
                      If spawner fails, a basic item is created from the
                      "name", "desc", "value" fields in the dict.
    chance (float)  : Drop probability, 0.0 to 1.0.
    name (str)      : Fallback item name if prototype is unavailable.
    desc (str)      : Fallback item description.
    value (int)     : Fallback copper value.

Death flow
----------

1. mob.take_damage() reduces HP to 0
2. mob.at_defeat() is called by the combat handler
3. XP is awarded to participants (handled by combat handler)
4. Corpse is spawned with rolled loot
5. Mob object is deleted
"""

from random import random

from evennia.utils.logger import log_err

from typeclasses.npcs import AwtownNPC


# Default stats for mobs that don't specify them
DEFAULT_MOB_STATS = {
    "str": 10, "dex": 10, "agi": 10, "con": 10, "end": 10,
    "int": 6, "wis": 6, "per": 10, "cha": 4, "lck": 8,
}


class AwtownMob(AwtownNPC):
    """
    A combat-capable mob (monster / hostile NPC).

    Extends AwtownNPC with HP, stats, loot, XP, and death handling.
    Uses simple db attributes instead of TraitHandler/BuffHandler for
    efficiency — mobs may be numerous and short-lived.

    db Attributes (inherited from AwtownNPC):
        is_npc         (bool)
        npc_role       (str)
        dialogue       (dict)

    db Attributes (new):
        is_mob         (bool)  : Always True. Used by combat rules to identify mobs.
        hp             (int)   : Current hit points.
        hp_max         (int)   : Maximum hit points.
        level          (int)   : Mob level (used by consider, rescue, XP scaling).
        stats          (dict)  : The 10 base stats {str: int, dex: int, ...}.
        xp_value       (int)   : XP awarded on kill (split among participants).
        damage_dice    (str)   : Natural attack dice (e.g. "1d6"). Used when unarmed.
        damage_bonus   (int)   : Flat damage bonus added to attacks.
        armor_bonus    (int)   : Flat defense bonus.
        loot_table     (list)  : List of loot dicts (see module docstring).
        aggro          (bool)  : Whether this mob attacks on sight (future use).
        combat_target  (obj)   : Current combat target (set by combat handler).
    """

    def at_object_creation(self):
        super().at_object_creation()

        # Identity
        self.db.is_mob = True
        self.db.npc_role = "mob"

        # Combat stats
        self.db.hp = 50
        self.db.hp_max = 50
        self.db.level = 1
        self.db.stats = dict(DEFAULT_MOB_STATS)

        # Offense / defense
        self.db.damage_dice = "1d4"
        self.db.damage_bonus = 0
        self.db.armor_bonus = 0

        # Rewards
        self.db.xp_value = 25
        self.db.loot_table = []

        # Behavior
        self.db.aggro = False
        self.db.combat_target = None
        self.db.wimpy = 0              # 0 = fight to the death

        # Movement
        self.db.move_mode = "stationary"   # "wander", "patrol", or "stationary"
        self.db.move_interval = 30         # seconds between movement ticks
        self.db.wander_chance = 0.5        # chance to move each wander tick
        self.db.patrol_route = []          # list of room dbrefs for patrol
        self.db.chase = False              # follow fleeing players
        self.db.chase_range = 3            # max rooms to chase before returning
        self.db.home_room = None           # dbref of home room (set on spawn)

        # Equipment dict (for mobs that wield weapons)
        self.db.equipment = {
            "weapon": None,
            "offhand": None,
        }

    # ------------------------------------------------------------------
    # Combat interface (matches AwtownCharacter signatures)
    # ------------------------------------------------------------------

    def get_stat(self, stat_key):
        """
        Return a base stat value.

        Args:
            stat_key (str): One of str/dex/agi/con/end/int/wis/per/cha/lck.

        Returns:
            int: The stat value.
        """
        stats = self.db.stats or DEFAULT_MOB_STATS
        return stats.get(stat_key, 10)

    def get_hp(self):
        """Return current HP."""
        return self.db.hp or 0

    def get_hp_max(self):
        """Return maximum HP."""
        return self.db.hp_max or 50

    def get_equipped(self, slot):
        """
        Return the item in an equipment slot, or None.

        Mobs can optionally wield weapons. Most use natural attacks
        (damage_dice) instead.
        """
        eq = self.db.equipment or {}
        dbref = eq.get(slot)
        if not dbref:
            return None
        from evennia import search_object
        results = search_object(dbref)
        return results[0] if results else None

    def heal(self, amount):
        """
        Restore HP by amount, capped at max.

        Args:
            amount (int): HP to restore.

        Returns:
            int: New HP value.
        """
        self.db.hp = min(self.db.hp_max, (self.db.hp or 0) + amount)
        return self.db.hp

    def take_damage(self, amount, source=None):
        """
        Apply damage to this mob.

        Does NOT run through BuffHandler (mobs don't use it).
        armor_bonus is already factored into defense by the combat rules.

        Args:
            amount (int): Damage to apply.
            source: The damage source (attacker object, or None).

        Returns:
            int: Actual damage dealt.
        """
        actual = max(0, amount)
        self.db.hp = max(0, (self.db.hp or 0) - actual)
        return actual

    def is_alive(self):
        """Return True if this mob still has HP remaining."""
        return (self.db.hp or 0) > 0

    # ------------------------------------------------------------------
    # Death and loot
    # ------------------------------------------------------------------

    def at_defeat(self):
        """
        Called when this mob is killed in combat.

        Spawns a corpse with rolled loot, then deletes the mob.
        XP distribution is handled by the combat handler, not here.

        Returns:
            Corpse object, or None if corpse creation failed.
        """
        location = self.location
        if not location:
            self.delete()
            return None

        corpse = self._spawn_corpse(location)
        self._roll_loot(corpse)

        # Announce
        location.msg_contents(
            f"|x{self.name} collapses to the ground, dead.|n"
        )

        # Clean up the mob
        self.delete()
        return corpse

    def _spawn_corpse(self, location):
        """
        Create a Corpse object at the given location.

        Returns:
            Corpse object.
        """
        from typeclasses.corpse import Corpse

        corpse = None
        try:
            from evennia import create_object
            corpse = create_object(
                Corpse,
                key=f"corpse of {self.key}",
                location=location,
            )
            corpse.db.desc = (
                f"The lifeless remains of {self.key} lie here. "
                f"You might find something useful if you search it."
            )
            corpse.db.mob_key = self.key
            corpse.db.mob_level = self.db.level
        except Exception as err:
            log_err(f"AwtownMob._spawn_corpse: failed to create corpse: {err}")

        return corpse

    def _roll_loot(self, corpse):
        """
        Roll the loot table and place drops into the corpse.

        If no corpse is available, drops fall on the ground (mob's location).

        Args:
            corpse: The Corpse object to receive loot, or None.
        """
        loot_table = self.db.loot_table or []
        if not loot_table:
            return

        drop_location = corpse if corpse else self.location
        if not drop_location:
            return

        for entry in loot_table:
            chance = entry.get("chance", 0)
            if random() > chance:
                continue

            item = self._create_loot_item(entry, drop_location)
            if item and self.location:
                self.location.msg_contents(
                    f"  |y{item.key}|n tumbles from the corpse."
                )

    def _create_loot_item(self, entry, location):
        """
        Create a single loot item from a loot table entry.

        Tries to spawn from prototype first, falls back to basic object.

        Args:
            entry (dict): Loot table entry.
            location: Where to place the item.

        Returns:
            Object or None.
        """
        from evennia import create_object

        # Try prototype spawner first
        proto_key = entry.get("prototype")
        if proto_key:
            try:
                from evennia.utils.spawner import spawn
                objs = spawn(proto_key)
                if objs:
                    objs[0].move_to(location, quiet=True)
                    return objs[0]
            except Exception:
                pass

        # Fallback: create a basic item (with decay support)
        name = entry.get("name", "something")
        desc = entry.get("desc", "A dropped item.")
        value = entry.get("value", 1)

        try:
            from typeclasses.items import AwtownItem
            obj = create_object(
                AwtownItem,
                key=name,
                location=location,
            )
            obj.db.desc = desc
            obj.db.value = value
            obj.db.item_level = self.db.level or 1
            return obj
        except Exception as err:
            log_err(f"AwtownMob._create_loot_item: failed: {err}")
            return None

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def get_display_name(self, looker, **kwargs):
        """Mobs display in red when alive, gray when dead."""
        if self.is_alive():
            return f"|r{self.name}|n"
        return f"|x{self.name}|n"

    def return_appearance(self, looker, **kwargs):
        """Show mob description with a health indicator."""
        desc = self.db.desc or "You see a creature."
        hp = self.get_hp()
        hp_max = self.get_hp_max()

        # Health indicator
        if hp >= hp_max:
            condition = "|gis in perfect health|n"
        elif hp > hp_max * 0.75:
            condition = "|ghas a few scratches|n"
        elif hp > hp_max * 0.50:
            condition = "|yis moderately wounded|n"
        elif hp > hp_max * 0.25:
            condition = "|yis badly wounded|n"
        elif hp > 0:
            condition = "|ris nearly dead|n"
        else:
            condition = "|xis dead|n"

        return f"|r{self.name}|n\n{desc}\n{self.name} {condition}."
