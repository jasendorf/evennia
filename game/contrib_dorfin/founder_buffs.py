"""
Founder Buffs
=============

The three Founders of Awtown each grant a daily buff to adventurers
who visit them. These are implemented as proper BaseBuff subclasses
using evennia.contrib.rpg.buffs.

Buffs:
    MalgraveRallyBuff      — Persuasion +5, Leadership +5, Morale +10
    HammerfallBlessingBuff — damage_bonus +10, armor_bonus +10
    OndrelInsightBuff      — xp_bonus +15, lore_bonus +10

Each buff:
    - Lasts 1 real hour (duration=3600)
    - Is unique (only one instance active at a time)
    - Does NOT refresh if applied again while active (refresh=False)
    - Has a 24-hour cooldown tracked via character db attribute

Cooldown storage:
    character.db.founder_cooldowns = {
        "malgrave": <unix timestamp of last grant>,
        "hammerfall": <unix timestamp of last grant>,
        "ondrel": <unix timestamp of last grant>,
    }

Usage in commands:
    character.buffs.add(MalgraveRallyBuff)

Usage in systems (e.g. XP gain):
    bonus = character.buffs.check(0, "xp_bonus")   # returns total mod value
"""

import time

from evennia.utils.utils import time_format

try:
    from evennia.contrib.rpg.buffs import BaseBuff, Mod
    _BUFFS_AVAILABLE = True
except ImportError:
    _BUFFS_AVAILABLE = False
    BaseBuff = object
    Mod = None


COOLDOWN_DURATION = 86400   # 24 hours in seconds
BUFF_DURATION     = 3600    # 1 hour in seconds


# ---------------------------------------------------------------------------
# Buff classes
# ---------------------------------------------------------------------------

if _BUFFS_AVAILABLE:

    class MalgraveRallyBuff(BaseBuff):
        """
        Malgrave's Rally — granted by Jorvyn Malgrave.

        Boosts Persuasion, Leadership, and party morale. Reflects Jorvyn's
        energetic, people-focused leadership style.
        """
        key      = "malgrave_rally"
        name     = "Malgrave's Rally"
        flavor   = "Jorvyn's confidence is infectious. You feel ready for anything."
        duration = BUFF_DURATION
        unique   = True
        refresh  = False

        mods = [
            Mod("persuasion_bonus", "add", 5),
            Mod("leadership_bonus", "add", 5),
            Mod("morale_bonus",     "add", 10),
        ]

        def at_apply(self, *args, **kwargs):
            if self.owner:
                self.owner.msg(
                    "Jorvyn grabs your hand and shakes it firmly. "
                    "'You've got this. Seriously. Now go.'\n"
                    "|gYou feel a surge of confidence. "
                    "Malgrave's Rally is active for 1 hour.|n"
                )

        def at_remove(self, *args, **kwargs):
            if self.owner:
                self.owner.msg("|yMalgrave's Rally has faded.|n")

        def at_expire(self, *args, **kwargs):
            self.at_remove()


    class HammerfallBlessingBuff(BaseBuff):
        """
        Hammerfall's Blessing — granted by Marro Hammerfall.

        Boosts weapon damage and armour durability. Marro's gift is
        entirely practical — he doesn't say much, but your gear is better
        for having had his hands on it.
        """
        key      = "hammerfall_blessing"
        name     = "Hammerfall's Blessing"
        flavor   = "Your weapons feel sharper. Your armour sits truer on your frame."
        duration = BUFF_DURATION
        unique   = True
        refresh  = False

        mods = [
            Mod("damage_bonus", "add", 10),
            Mod("armor_bonus",  "add", 10),
        ]

        def at_apply(self, *args, **kwargs):
            if self.owner:
                self.owner.msg(
                    "Marro doesn't look up. He reaches over and tightens "
                    "something on your gear. 'Better. Now go.'\n"
                    "|gYour weapons feel sharper and your armour heavier. "
                    "Hammerfall's Blessing is active for 1 hour.|n"
                )

        def at_remove(self, *args, **kwargs):
            if self.owner:
                self.owner.msg("|yHammerfall's Blessing has faded.|n")

        def at_expire(self, *args, **kwargs):
            self.at_remove()


    class OndrelInsightBuff(BaseBuff):
        """
        Ondrel's Insight — granted by Joleth Ondrel.

        Boosts XP gain and Lore skill checks. Joleth's gift is knowledge —
        she can't stop you from getting hurt, but she can make sure you
        learn something from it.
        """
        key      = "ondrel_insight"
        name     = "Ondrel's Insight"
        flavor   = "Your mind feels sharp. Details you'd normally overlook stand out clearly."
        duration = BUFF_DURATION
        unique   = True
        refresh  = False

        mods = [
            Mod("xp_bonus",   "add", 15),
            Mod("lore_bonus",  "add", 10),
        ]

        def at_apply(self, *args, **kwargs):
            if self.owner:
                self.owner.msg(
                    "Joleth looks up from her book with a warm smile. "
                    "'I've been reading about where you're heading. "
                    "Fascinating history. The short version: pay attention.'\n"
                    "|gYour mind feels sharp and ready. "
                    "Ondrel's Insight is active for 1 hour.|n"
                )

        def at_remove(self, *args, **kwargs):
            if self.owner:
                self.owner.msg("|yOndrel's Insight has faded.|n")

        def at_expire(self, *args, **kwargs):
            self.at_remove()

else:
    # Stubs when Buffs contrib is not installed
    class MalgraveRallyBuff: pass
    class HammerfallBlessingBuff: pass
    class OndrelInsightBuff: pass


# ---------------------------------------------------------------------------
# Founder registry
# ---------------------------------------------------------------------------

FOUNDER_REGISTRY = {
    "npc_malgrave": {
        "buff_class":   MalgraveRallyBuff,
        "buff_key":     "malgrave_rally",
        "cooldown_key": "malgrave",
        "name":         "Malgrave's Rally",
        "msg_active":   (
            "Jorvyn smiles. 'Still going strong, I see. The Rally is holding.'\n"
            "|yYou can receive this blessing again in {remaining}.|n"
        ),
        "msg_cooldown": (
            "Jorvyn claps you on the shoulder. 'You've had my blessing already today. "
            "Come back tomorrow.'\n"
            "|yAvailable again in {remaining}.|n"
        ),
    },
    "npc_hammerfall": {
        "buff_class":   HammerfallBlessingBuff,
        "buff_key":     "hammerfall_blessing",
        "cooldown_key": "hammerfall",
        "name":         "Hammerfall's Blessing",
        "msg_active":   (
            "[doesn't look up] 'Still holding. Gear's fine. Come back tomorrow.'\n"
            "|yAvailable again in {remaining}.|n"
        ),
        "msg_cooldown": (
            "Marro shakes his head without looking up. 'Tomorrow.'\n"
            "|yAvailable again in {remaining}.|n"
        ),
    },
    "npc_ondrel": {
        "buff_class":   OndrelInsightBuff,
        "buff_key":     "ondrel_insight",
        "cooldown_key": "ondrel",
        "name":         "Ondrel's Insight",
        "msg_active":   (
            "Joleth tilts her head. 'You still have the Insight — I can see it. "
            "Come back tomorrow.'\n"
            "|yAvailable again in {remaining}.|n"
        ),
        "msg_cooldown": (
            "Joleth marks her page carefully. "
            "'You've already received today's Insight. Rest. Return tomorrow.'\n"
            "|yAvailable again in {remaining}.|n"
        ),
    },
}


# ---------------------------------------------------------------------------
# Cooldown helpers
# ---------------------------------------------------------------------------

def get_cooldowns(character):
    """Return the founder_cooldowns dict, initialising if absent."""
    cd = character.db.founder_cooldowns
    if not cd:
        cd = {}
        character.db.founder_cooldowns = cd
    return cd


def is_on_cooldown(character, cooldown_key):
    """
    Return (on_cooldown: bool, remaining_seconds: float).
    remaining_seconds is 0 if not on cooldown.
    """
    cd = get_cooldowns(character)
    last = cd.get(cooldown_key, 0)
    if last == 0:
        return False, 0
    elapsed = time.time() - last
    if elapsed < COOLDOWN_DURATION:
        return True, COOLDOWN_DURATION - elapsed
    return False, 0


def set_cooldown(character, cooldown_key):
    """Record the current time as the last grant time for this Founder."""
    cd = get_cooldowns(character)
    cd[cooldown_key] = time.time()
    character.db.founder_cooldowns = cd


def get_founder_data(location):
    """
    Search a room for a Founder NPC and return (npc, registry_entry).
    Returns (None, None) if no Founder is present.
    """
    try:
        from typeclasses.npcs import AwtownNPC
    except ImportError:
        return None, None

    for obj in location.contents:
        if not isinstance(obj, AwtownNPC):
            continue
        for tag_key, data in FOUNDER_REGISTRY.items():
            if obj.tags.get(tag_key, category="awtown_npc"):
                return obj, data
    return None, None
