"""
DorfinMUD Character Creation — EvMenu Module
=============================================

Custom chargen menu for the character_creator contrib.
Pointed to by ``CHARGEN_MENU = "world.chargen"`` in settings.

Flow:
    welcome → choose name → choose race → race detail →
    choose class → class detail → allocate stats → summary → end

The contrib passes the **session** as the EvMenu caller.
Access the character being created via ``caller.new_char``.
"""

import random

import evennia
from evennia.utils import dedent
from evennia.utils.evtable import EvTable
from typeclasses.characters import Character

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_STAT = 10
BONUS_POINTS = 15
STAT_MIN = 3
STAT_MAX = 20

STAT_KEYS = ["str", "dex", "agi", "con", "end", "int", "wis", "per", "cha", "lck"]

BASE_STATS = {
    "str": {
        "name": "Strength",
        "abbr": "STR",
        "desc": "Carry weight, melee damage, breaking objects, grappling.",
    },
    "dex": {
        "name": "Dexterity",
        "abbr": "DEX",
        "desc": "Fine motor control, archery aim, lockpicking, sleight of hand.",
    },
    "agi": {
        "name": "Agility",
        "abbr": "AGI",
        "desc": "Movement speed, flee chance, combat initiative, acrobatics.",
    },
    "con": {
        "name": "Constitution",
        "abbr": "CON",
        "desc": "Hit points, disease resistance, poison tolerance, toughness.",
    },
    "end": {
        "name": "Endurance",
        "abbr": "END",
        "desc": "Stamina pool, travel fatigue, sustained effort, prolonged combat.",
    },
    "int": {
        "name": "Intelligence",
        "abbr": "INT",
        "desc": "Spell power, learning speed, crafting complexity, puzzle solving.",
    },
    "wis": {
        "name": "Wisdom",
        "abbr": "WIS",
        "desc": "Mana pool, clerical/druidic power, judgment, mental resistance.",
    },
    "per": {
        "name": "Perception",
        "abbr": "PER",
        "desc": "Spot hidden exits, detect traps, scan range, combat awareness.",
    },
    "cha": {
        "name": "Charisma",
        "abbr": "CHA",
        "desc": "NPC reactions, shop prices, persuasion, leadership.",
    },
    "lck": {
        "name": "Luck",
        "abbr": "LCK",
        "desc": "Critical hit chance, rare drops, random event outcomes.",
    },
}

# ---------------------------------------------------------------------------
# Races
# ---------------------------------------------------------------------------

STARTER_RACES = {
    "human": {
        "name": "Human",
        "desc": (
            "Versatile and adaptable, humans thrive in every corner of Dorfin. "
            "They lack the extremes of other races but learn faster than most. "
            "What they lack in specialization, they make up for in determination."
        ),
        "stat_mods": {"str": 1, "con": 1, "cha": 1, "lck": 1},
        "languages": ["common"],
        "traits": ["Fast learner: +10% XP gain"],
    },
    "elf": {
        "name": "Elf",
        "desc": (
            "Graceful and long-lived, elves are attuned to magic and the natural world. "
            "Their senses are sharp and their movements fluid, though they can be "
            "physically fragile compared to hardier races."
        ),
        "stat_mods": {"dex": 2, "int": 2, "per": 1, "agi": 1, "con": -2, "str": -2},
        "languages": ["common", "elvish"],
        "traits": ["Keen senses: bonus to Perception checks in forests"],
    },
    "dwarf": {
        "name": "Dwarf",
        "desc": (
            "Stout and unyielding, dwarves are born miners and crafters. "
            "They are naturally resistant to poison and disease, and their "
            "stubbornness is legendary -- for better or worse."
        ),
        "stat_mods": {"con": 3, "str": 2, "end": 1, "agi": -2, "cha": -1, "dex": -1},
        "languages": ["common", "dwarvish"],
        "traits": ["Stone-hearted: resistance to poison"],
    },
    "halfling": {
        "name": "Halfling",
        "desc": (
            "Small but surprisingly brave, halflings are nimble, socially charming, "
            "and extraordinarily lucky. They prefer comfort but rise to the occasion "
            "when adventure calls."
        ),
        "stat_mods": {"agi": 2, "lck": 3, "dex": 1, "cha": 1, "str": -3, "con": -2},
        "languages": ["common", "halfling"],
        "traits": ["Lucky: reroll one critical failure per day"],
    },
    "gnome": {
        "name": "Gnome",
        "desc": (
            "Clever, inventive, and endlessly curious, gnomes are natural tinkerers "
            "and scholars. Their small size belies a sharp mind and a knack for "
            "getting into -- and out of -- trouble."
        ),
        "stat_mods": {"int": 3, "dex": 2, "per": 1, "str": -2, "con": -1, "end": -1},
        "languages": ["common", "dwarvish"],
        "traits": ["Tinker's mind: bonus to crafting skill checks"],
    },
    "half_elf": {
        "name": "Half-Elf",
        "desc": (
            "Caught between two worlds, half-elves inherit the adaptability of humans "
            "and the grace of elves. They are natural diplomats and fit in almost "
            "anywhere, even if they never fully belong."
        ),
        "stat_mods": {"cha": 2, "per": 1, "dex": 1, "int": 1, "con": -1, "str": -1},
        "languages": ["common", "elvish"],
        "traits": ["Diplomatic: bonus to Persuasion"],
    },
    "half_orc": {
        "name": "Half-Orc",
        "desc": (
            "Born of two bloodlines, half-orcs combine human cunning with orcish "
            "strength. They are powerful fighters who often struggle for acceptance "
            "in both worlds."
        ),
        "stat_mods": {"str": 3, "end": 2, "con": 1, "int": -2, "cha": -2, "per": -1},
        "languages": ["common", "orcish"],
        "traits": ["Savage strikes: bonus to critical hit damage"],
    },
    "orc": {
        "name": "Orc",
        "desc": (
            "Raw physical power defines the orc. Tribal, fierce, and loyal to their "
            "own, orcs solve most problems with strength. Their culture values "
            "combat prowess above all."
        ),
        "stat_mods": {"str": 3, "con": 2, "end": 2, "int": -3, "cha": -2, "dex": -1, "wis": -1},
        "languages": ["common", "orcish"],
        "traits": ["Battle fury: bonus damage when below 25% HP"],
    },
    "goblin": {
        "name": "Goblin",
        "desc": (
            "Small, cunning, and endlessly resourceful, goblins survive by their "
            "wits. Underestimated by everyone, which suits them perfectly. "
            "They see opportunities where others see junk."
        ),
        "stat_mods": {"agi": 3, "per": 2, "lck": 1, "str": -3, "con": -1, "cha": -2},
        "languages": ["common", "goblin"],
        "traits": ["Scavenger: find extra loot from defeated enemies"],
    },
    "troll": {
        "name": "Troll",
        "desc": (
            "Large, tough, and surprisingly thoughtful -- trolls are not the mindless "
            "brutes legend paints them. Their regenerative abilities make them "
            "fearsome in prolonged combat."
        ),
        "stat_mods": {"con": 3, "str": 3, "end": 2, "dex": -3, "agi": -2, "int": -2, "cha": -1},
        "languages": ["common", "giant"],
        "traits": ["Regeneration: slowly recover HP outside of combat"],
    },
    "hobgoblin": {
        "name": "Hobgoblin",
        "desc": (
            "Disciplined, militaristic, and organized, hobgoblins are the soldiers "
            "of the goblinoid races. They value order, strategy, and martial "
            "excellence above all."
        ),
        "stat_mods": {"end": 3, "str": 1, "wis": 2, "con": 1, "cha": -3, "lck": -2},
        "languages": ["common", "goblin", "orcish"],
        "traits": ["Tactical mind: bonus to initiative"],
    },
    "lizardfolk": {
        "name": "Lizardfolk",
        "desc": (
            "Cold-blooded pragmatists from ancient swamp civilizations. Lizardfolk "
            "think in terms of survival, not sentiment. They are natural swimmers "
            "and their thick scales provide natural armor."
        ),
        "stat_mods": {"con": 3, "per": 2, "str": 1, "cha": -3, "int": -1, "lck": -1},
        "languages": ["common", "draconic"],
        "traits": ["Natural armor: +2 base armor bonus"],
    },
}

UNLOCKABLE_RACES = {
    "dragonborn": {
        "name": "Dragonborn",
        "desc": (
            "Proud descendants of dragons, dragonborn carry the elemental fury of "
            "their ancestors in their blood. Their breath weapon and draconic "
            "resilience make them formidable warriors and sorcerers alike."
        ),
        "unlock_hint": "Reach level 20 with any character.",
        "stat_mods": {"str": 2, "cha": 2, "con": 1, "end": 1, "dex": -2, "agi": -1, "lck": -1},
        "languages": ["common", "draconic"],
        "traits": ["Breath weapon: elemental cone attack (1/rest)"],
    },
    "tabaxi": {
        "name": "Tabaxi",
        "desc": (
            "Feline humanoids driven by an insatiable curiosity. Tabaxi are blindingly "
            "fast in short bursts and possess catlike reflexes. They collect stories "
            "and trinkets with equal enthusiasm."
        ),
        "unlock_hint": "Discover 50 unique rooms.",
        "stat_mods": {"agi": 3, "dex": 2, "per": 2, "str": -2, "con": -2, "wis": -1},
        "languages": ["common", "elvish"],
        "traits": ["Feline agility: double movement speed for one round (1/rest)"],
    },
    "kenku": {
        "name": "Kenku",
        "desc": (
            "Flightless corvid folk cursed to speak only in mimicked sounds. "
            "What they lack in original speech they make up for in cunning, "
            "stealth, and an uncanny talent for forgery and deception."
        ),
        "unlock_hint": "Learn 5 languages on any character.",
        "stat_mods": {"dex": 3, "wis": 2, "per": 1, "str": -2, "cha": -2, "con": -1},
        "languages": ["common"],
        "traits": ["Mimicry: perfectly replicate any sound or voice heard"],
    },
    "goliath": {
        "name": "Goliath",
        "desc": (
            "Mountain-born giants who live by a code of fierce competition. "
            "Every goliath measures themselves against their peers. Their massive "
            "frames shrug off blows that would fell lesser beings."
        ),
        "unlock_hint": "Defeat a boss enemy solo.",
        "stat_mods": {"str": 3, "con": 3, "end": 2, "agi": -3, "dex": -2, "int": -1},
        "languages": ["common", "giant"],
        "traits": ["Stone's endurance: reduce damage taken by half (1/rest)"],
    },
    "firbolg": {
        "name": "Firbolg",
        "desc": (
            "Gentle forest giants with a deep connection to the natural world. "
            "Firbolgs prefer solitude and the company of animals, using their "
            "innate magic to protect the wild places from corruption."
        ),
        "unlock_hint": "Master the Herbalism profession.",
        "stat_mods": {"wis": 3, "con": 2, "str": 2, "agi": -2, "cha": -2, "dex": -1},
        "languages": ["common", "elvish", "giant"],
        "traits": ["Hidden step: turn invisible for one round (1/rest)"],
    },
    "changeling": {
        "name": "Changeling",
        "desc": (
            "Shapeshifters who can alter their appearance at will. Changelings "
            "live in the margins of society, wearing faces like masks. Their true "
            "form is pale and featureless -- few ever see it."
        ),
        "unlock_hint": "Complete the Shadow Chamber questline.",
        "stat_mods": {"cha": 3, "dex": 2, "per": 1, "int": 1, "str": -3, "con": -2},
        "languages": ["common"],
        "traits": ["Shapechanger: alter appearance at will (cosmetic only)"],
    },
    "dark_elf": {
        "name": "Dark Elf",
        "desc": (
            "Subterranean elves shaped by centuries in the underdark. Their innate "
            "magic and darkvision make them deadly in the shadows. On the surface, "
            "they are mistrusted and feared -- often with good reason."
        ),
        "unlock_hint": "Reach level 30 with an Elf character.",
        "stat_mods": {"int": 3, "dex": 2, "cha": 1, "per": 1, "con": -3, "end": -1, "lck": -1},
        "languages": ["common", "elvish"],
        "traits": ["Superior darkvision: see perfectly in total darkness"],
    },
    "tortle": {
        "name": "Tortle",
        "desc": (
            "Shelled wanderers who carry their home on their back. Tortles are "
            "patient, long-lived, and nearly impossible to kill. They move slowly "
            "but methodically, and their natural shell is tougher than plate armor."
        ),
        "unlock_hint": "Survive 100 combats without fleeing.",
        "stat_mods": {"con": 3, "wis": 2, "end": 2, "str": 1, "agi": -3, "dex": -3},
        "languages": ["common"],
        "traits": ["Shell defense: withdraw into shell for +4 armor, can't move (toggle)"],
    },
}

# Ordered list of race keys for numbered display
_STARTER_RACE_LIST = list(STARTER_RACES.keys())

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

CLASSES = {
    "warrior": {
        "name": "Warrior",
        "category": "Martial",
        "desc": (
            "The backbone of any fighting force. Warriors master weapons and armor, "
            "excelling in direct combat. They can take hits and dish them out in equal measure."
        ),
    },
    "paladin": {
        "name": "Paladin",
        "category": "Martial",
        "desc": (
            "Holy warriors who channel divine power to heal allies and smite the unholy. "
            "They are armored protectors bound by an oath."
        ),
    },
    "ranger": {
        "name": "Ranger",
        "category": "Martial",
        "desc": (
            "Wilderness fighters and trackers. Rangers excel at ranged combat and "
            "thrive in the wild where others falter."
        ),
    },
    "barbarian": {
        "name": "Barbarian",
        "category": "Martial",
        "desc": (
            "Rage-fueled melee fighters who trade finesse for raw destructive power. "
            "Their fury in battle is terrifying."
        ),
    },
    "knight": {
        "name": "Knight",
        "category": "Martial",
        "desc": (
            "Armored defenders who follow a code of honor. Specialists in mounted "
            "combat and protecting those who cannot protect themselves."
        ),
    },
    "monk": {
        "name": "Monk",
        "category": "Martial",
        "desc": (
            "Disciplined martial artists who channel inner power through their body. "
            "Fast, precise, and deadly without a weapon."
        ),
    },
    "archer": {
        "name": "Archer",
        "category": "Martial",
        "desc": (
            "Masters of the bow who strike from a distance with deadly precision. "
            "Archers control the battlefield with sustained ranged damage, trick shots, "
            "and the ability to pin down enemies before they close the gap."
        ),
    },
    "hunter": {
        "name": "Hunter",
        "category": "Martial",
        "desc": (
            "Patient stalkers who combine ranged attacks with traps and animal companions. "
            "Hunters track their prey across any terrain and strike when the moment is right. "
            "Their bond with a beast companion makes them a two-front threat."
        ),
    },
    "swashbuckler": {
        "name": "Swashbuckler",
        "category": "Martial",
        "desc": (
            "Flashy duelists who fight with agility and charm rather than brute force. "
            "Quick on their feet and quicker with a blade."
        ),
    },
    "mage": {
        "name": "Mage",
        "category": "Magic",
        "desc": (
            "Generalist arcane casters with broad access to the schools of magic. "
            "Versatile but master of none."
        ),
    },
    "wizard": {
        "name": "Wizard",
        "category": "Magic",
        "desc": (
            "Scholarly spellcasters who memorize and prepare spells from vast libraries. "
            "Methodical, powerful, and research-driven."
        ),
    },
    "sorcerer": {
        "name": "Sorcerer",
        "category": "Magic",
        "desc": (
            "Born with innate magical power flowing through their blood. "
            "Raw talent over training -- less control, but devastating potential."
        ),
    },
    "warlock": {
        "name": "Warlock",
        "category": "Magic",
        "desc": (
            "Casters who draw power from a pact with a powerful patron. "
            "Their magic is granted, not learned -- and the patron always wants something in return."
        ),
    },
    "necromancer": {
        "name": "Necromancer",
        "category": "Magic",
        "desc": (
            "Masters of death magic who raise the dead and manipulate life force. "
            "Feared and mistrusted, but undeniably powerful."
        ),
    },
    "illusionist": {
        "name": "Illusionist",
        "category": "Magic",
        "desc": (
            "Deception is their weapon. Illusionists create false images and "
            "sensations to misdirect, confuse, and control the battlefield."
        ),
    },
    "elementalist": {
        "name": "Elementalist",
        "category": "Magic",
        "desc": (
            "Specialists in the raw elements -- fire, ice, lightning, and earth. "
            "Focused destructive power drawn from nature itself."
        ),
    },
    "druid": {
        "name": "Druid",
        "category": "Magic",
        "desc": (
            "Nature casters who draw power from the living world. They shapeshift, "
            "command animals, and protect the balance of nature."
        ),
    },
    "shaman": {
        "name": "Shaman",
        "category": "Magic",
        "desc": (
            "Spirit callers who commune with ancestral and nature spirits. "
            "They place totems, channel spirits, and walk between worlds."
        ),
    },
    "rogue": {
        "name": "Rogue",
        "category": "Stealth & Support",
        "desc": (
            "Versatile operators who blend stealth, traps, and moderate combat skill. "
            "The jack-of-all-trades of the shadows."
        ),
    },
    "thief": {
        "name": "Thief",
        "category": "Stealth & Support",
        "desc": (
            "Pure stealth specialists. Infiltration, theft, and vanishing without "
            "a trace are their stock in trade."
        ),
    },
    "assassin": {
        "name": "Assassin",
        "category": "Stealth & Support",
        "desc": (
            "Lethal killers who strike from the shadows. Poison, ambush, and "
            "devastating single-target damage define the assassin."
        ),
    },
    "bard": {
        "name": "Bard",
        "category": "Stealth & Support",
        "desc": (
            "Music and magic intertwined. Bards buff allies, debuff enemies, "
            "manipulate social situations, and always have a story to tell."
        ),
    },
    "cleric": {
        "name": "Cleric",
        "category": "Stealth & Support",
        "desc": (
            "Divine healers who channel the power of the gods. They heal the wounded, "
            "buff the faithful, and turn the undead."
        ),
    },
    "healer": {
        "name": "Healer",
        "category": "Stealth & Support",
        "desc": (
            "Pure support specialists. Healers restore health, remove debuffs, "
            "and keep their party alive through the worst encounters."
        ),
    },
    "scout": {
        "name": "Scout",
        "category": "Stealth & Support",
        "desc": (
            "Reconnaissance experts who move fast, survive in the wild, and "
            "gather information. They see trouble before it arrives."
        ),
    },
    "tinkerer": {
        "name": "Tinkerer",
        "category": "Stealth & Support",
        "desc": (
            "Gadgeteers and trap-makers who build mechanical solutions to every problem. "
            "Companions, explosives, and utility devices are their tools."
        ),
    },
}

# Ordered class list for numbered display
_CLASS_LIST = list(CLASSES.keys())

# ---------------------------------------------------------------------------
# Languages
# ---------------------------------------------------------------------------

LANGUAGES = {
    "common": {"name": "Common", "desc": "Universal trade language of Dorfin. Spoken by all races."},
    "elvish": {"name": "Elvish", "desc": "The flowing tongue of the elves. Dark Elves speak a dialect variant."},
    "dwarvish": {"name": "Dwarvish", "desc": "Sturdy language of dwarves and gnomes. Gnomish is a dialect."},
    "halfling": {"name": "Halfling", "desc": "Standalone language, rarely heard outside halfling communities."},
    "orcish": {"name": "Orcish", "desc": "Militaristic lingua franca of the warband races."},
    "goblin": {"name": "Goblin", "desc": "Quick, clipped speech. Hobgoblins speak both Goblin and Orcish."},
    "giant": {"name": "Giant", "desc": "The deep, rumbling tongue of trolls and goliaths."},
    "draconic": {"name": "Draconic", "desc": "Ancient reptilian language family. Spoken by dragonborn and lizardfolk."},
    "sylvan": {"name": "Sylvan", "desc": "Nature/fey tongue of firbolgs, tabaxi, and tortles."},
    "kenku": {"name": "Kenku", "desc": "Mimic-based communication. Kenku repeat sounds they've heard."},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _roll_base_stats():
    """Roll 3d6 for each stat, returning a dict of raw rolls."""
    return {s: sum(random.randint(1, 6) for _ in range(3)) for s in STAT_KEYS}


def _apply_racial_mods(rolls, race_key):
    """Apply racial modifiers to rolled base stats."""
    rdata = STARTER_RACES.get(race_key) or UNLOCKABLE_RACES.get(race_key, {})
    mods = rdata.get("stat_mods", {})
    return {s: max(STAT_MIN, rolls[s] + mods.get(s, 0)) for s in STAT_KEYS}


def _calc_points_spent(wip_stats, base_stats):
    """Return how many bonus points have been allocated beyond base."""
    return sum(wip_stats[s] - base_stats[s] for s in STAT_KEYS)


def _format_stat_table(wip_stats, base_stats):
    """Build a compact stat table with alternating highlight rows."""
    spent = _calc_points_spent(wip_stats, base_stats)
    remaining = BONUS_POINTS - spent

    lines = [f"  |w{'Stat':<5} {'Base':>4}  {'Alloc':>5}  {'Total':>5}|n"]
    lines.append("  " + "-" * 25)

    for i, s in enumerate(STAT_KEYS):
        base = base_stats[s]
        alloc = wip_stats[s] - base
        total = wip_stats[s]
        alloc_str = f"|g+{alloc}|n" if alloc > 0 else f"|r{alloc}|n" if alloc < 0 else "  -"
        # Alternate rows: dim background on odd rows
        if i % 2 == 1:
            lines.append(f"  |x{BASE_STATS[s]['abbr']:<5} {base:>4}  {alloc_str}|x  {total:>5}|n")
        else:
            lines.append(f"  |w{BASE_STATS[s]['abbr']:<5}|n {base:>4}  {alloc_str}  |w{total:>5}|n")

    lines.append("")
    lines.append(f"  |wBonus points remaining: {remaining}/{BONUS_POINTS}|n")
    return "\n".join(lines)


# ===================================================================
#  EvMenu Nodes
# ===================================================================

# -------------------------------------------------------------------
#  Welcome
# -------------------------------------------------------------------

def menunode_welcome(caller):
    """Starting page."""
    char = caller.new_char
    char.db.chargen_step = "menunode_welcome"

    text = dedent("""\
        |w=============================================
          Welcome to DorfinMUD Character Creation!
        =============================================|n

        You're about to create a new character for the Land of Dorfin.

        You'll choose a |wname|n, |wrace|n, |wclass|n, and allocate
        |wstats|n before entering the world.

        You can exit at any time and resume later by typing |wcharcreate|n.
    """)
    options = {"desc": "Let's begin!", "goto": "menunode_choose_name"}
    return text, options


# -------------------------------------------------------------------
#  Name
# -------------------------------------------------------------------

def menunode_choose_name(caller, raw_string="", **kwargs):
    """Choose a character name."""
    char = caller.new_char
    char.db.chargen_step = "menunode_choose_name"

    if error := kwargs.get("error"):
        prompt = f"|r{error}|n\n\nEnter a different name."
    else:
        prompt = "Enter your character's name."

    text = dedent(f"""\
        |wChoose a Name|n

        Names must be 3-20 characters, letters only, and not already taken.

        {prompt}

        Type |wback|n to return to the welcome screen.
    """)
    options = {"key": "_default", "goto": _check_name}
    return text, options


def _check_name(caller, raw_string, **kwargs):
    """Validate and set the character name."""
    name = raw_string.strip()

    if name.lower() in ("back", "b"):
        return "menunode_welcome"

    if not name.isalpha():
        return "menunode_choose_name", {"error": "Names must contain only letters."}
    if len(name) < 3:
        return "menunode_choose_name", {"error": "Name must be at least 3 characters."}
    if len(name) > 20:
        return "menunode_choose_name", {"error": "Name must be 20 characters or fewer."}

    # Capitalize properly
    name = name.capitalize()

    # Check uniqueness
    candidates = Character.objects.filter_family(db_key__iexact=name)
    # Exclude the current in-progress character (it has a random temp key)
    candidates = [c for c in candidates if c.id != caller.new_char.id]
    if candidates:
        return "menunode_choose_name", {"error": f"|w{name}|n is already taken."}

    caller.new_char.key = name
    return "menunode_race_list"


# -------------------------------------------------------------------
#  Race Selection
# -------------------------------------------------------------------

def menunode_race_list(caller, raw_string="", **kwargs):
    """Display the list of available races."""
    char = caller.new_char
    char.db.chargen_step = "menunode_race_list"

    # Build available race list: starters + any unlocked races for this account
    account = caller.account if hasattr(caller, "account") else None
    unlocked = account.db.unlocked_races or [] if account else []
    available_races = list(_STARTER_RACE_LIST)
    for rkey in unlocked:
        if rkey in UNLOCKABLE_RACES and rkey not in available_races:
            available_races.append(rkey)

    # Store on char so _select_race can use the same list
    char.db._available_races = available_races

    lines = ["|wChoose Your Race|n\n"]

    for i, rkey in enumerate(available_races, 1):
        rdata = STARTER_RACES.get(rkey) or UNLOCKABLE_RACES.get(rkey)
        mods = rdata.get("stat_mods", {})
        mods_str = ", ".join(
            f"{BASE_STATS[s]['abbr']} {'+' if v > 0 else ''}{v}"
            for s, v in mods.items()
        )
        if mods_str:
            lines.append(f"  |w{i:>2}|n. |c{rdata['name']:<12}|n  ({mods_str})")
        else:
            lines.append(f"  |w{i:>2}|n. |c{rdata['name']}|n")

    lines.append("\nEnter a number or race name to learn more, or |wback|n.")

    text = "\n".join(lines)
    options = {"key": "_default", "goto": _select_race}
    return text, options


def _select_race(caller, raw_string, **kwargs):
    """Parse race selection input."""
    choice = raw_string.strip().lower()
    available = caller.new_char.db._available_races or list(_STARTER_RACE_LIST)

    if choice in ("back", "b"):
        return "menunode_choose_name"

    # Try as number
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(available):
            return "menunode_race_detail", {"selected_race": available[idx]}
    except ValueError:
        pass

    # Try as name (search both starter and unlockable dicts)
    all_races = {**STARTER_RACES, **UNLOCKABLE_RACES}
    for rkey in available:
        rdata = all_races.get(rkey)
        if rdata and choice in (rkey, rdata["name"].lower()):
            return "menunode_race_detail", {"selected_race": rkey}

    caller.msg(f"|rInvalid choice.|n Enter a number (1-{len(available)}) or race name.")
    return "menunode_race_list"


def menunode_race_detail(caller, raw_string="", selected_race=None, **kwargs):
    """Show details for a selected race and confirm."""
    if not selected_race:
        return "menunode_race_list"

    rdata = STARTER_RACES.get(selected_race) or UNLOCKABLE_RACES.get(selected_race)
    mods_str = ", ".join(
        f"{BASE_STATS[s]['abbr']} {'+' if v > 0 else ''}{v}"
        for s, v in rdata.get("stat_mods", {}).items()
    )

    langs = ", ".join(LANGUAGES[l]["name"] for l in rdata["languages"])
    traits = "\n    ".join(rdata["traits"])

    text = (
        f"|w{rdata['name']}|n\n"
        f"\n"
        f"  {rdata['desc']}\n"
        f"\n"
        f"  |wStat Modifiers:|n {mods_str}\n"
        f"  |wLanguages:|n {langs}\n"
        f"  |wRacial Traits:|n\n"
        f"    {traits}\n"
    )

    options = [
        {
            "key": ("Choose", "choose", "c", "yes", "y"),
            "desc": f"Choose |c{rdata['name']}|n",
            "goto": (_confirm_race, {"selected_race": selected_race}),
        },
        {
            "key": ("Back", "back", "b"),
            "desc": "Go back to race list",
            "goto": "menunode_race_list",
        },
    ]
    return text, options


def _confirm_race(caller, raw_string, selected_race=None, **kwargs):
    """Set the chosen race on the character."""
    char = caller.new_char
    char.db.race = selected_race
    rdata = STARTER_RACES.get(selected_race) or UNLOCKABLE_RACES[selected_race]
    char.db.race_name = rdata["name"]
    # Clear any previous rolls so menunode_stats will re-roll with new race
    char.db.base_stats = None
    char.db.wip_stats = None
    return "menunode_class_list"


# -------------------------------------------------------------------
#  Class Selection
# -------------------------------------------------------------------

def menunode_class_list(caller, raw_string="", **kwargs):
    """Display classes in three side-by-side columns, one per category."""
    char = caller.new_char
    char.db.chargen_step = "menunode_class_list"

    lines = ["|wChoose Your Class|n\n"]

    # Build one column per category, preserving insertion order
    categories = {}
    for ckey, cdata in CLASSES.items():
        categories.setdefault(cdata["category"], []).append((ckey, cdata))

    cat_names = list(categories.keys())
    col_width = 24

    # Assign global numbering and build column data
    cat_entries = []
    idx = 0
    for cat_name in cat_names:
        col = []
        for ckey, cdata in categories[cat_name]:
            idx += 1
            col.append((idx, cdata["name"]))
        cat_entries.append(col)

    max_rows = max(len(col) for col in cat_entries)

    # Header row
    header_parts = []
    for cat_name in cat_names:
        header_parts.append(f"|w{cat_name:<{col_width}}|n")
    lines.append("  " + "".join(header_parts).rstrip())
    lines.append("  " + "-" * (col_width * len(cat_names) - 2))

    # Data rows
    for row in range(max_rows):
        row_parts = []
        for col in cat_entries:
            if row < len(col):
                num, name = col[row]
                entry = f"|w{num:>2}|n. |c{name}|n"
                visible_len = len(f"{num:>2}. {name}")
                pad = max(col_width - visible_len, 1)
                row_parts.append(entry + " " * pad)
            else:
                row_parts.append(" " * col_width)
        lines.append("  " + "".join(row_parts).rstrip())

    lines.append("\nEnter a number or class name to learn more, or |wback|n.")

    text = "\n".join(lines)
    options = {"key": "_default", "goto": _select_class}
    return text, options


def _select_class(caller, raw_string, **kwargs):
    """Parse class selection input."""
    choice = raw_string.strip().lower()

    if choice in ("back", "b"):
        return "menunode_race_list"

    # Try as number
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(_CLASS_LIST):
            return "menunode_class_detail", {"selected_class": _CLASS_LIST[idx]}
    except ValueError:
        pass

    # Try as name
    for ckey, cdata in CLASSES.items():
        if choice in (ckey, cdata["name"].lower()):
            return "menunode_class_detail", {"selected_class": ckey}

    caller.msg(f"|rInvalid choice.|n Enter a number (1-{len(_CLASS_LIST)}) or class name.")
    return "menunode_class_list"


def menunode_class_detail(caller, raw_string="", selected_class=None, **kwargs):
    """Show details for a selected class and confirm."""
    if not selected_class:
        return "menunode_class_list"

    cdata = CLASSES[selected_class]

    text = dedent(f"""\
        |w{cdata['name']}|n  |x({cdata['category']})|n

        {cdata['desc']}
    """)

    options = [
        {
            "key": ("Choose", "choose", "c", "yes", "y"),
            "desc": f"Choose |c{cdata['name']}|n",
            "goto": (_confirm_class, {"selected_class": selected_class}),
        },
        {
            "key": ("Back", "back", "b"),
            "desc": "Go back to class list",
            "goto": "menunode_class_list",
        },
    ]
    return text, options


def _confirm_class(caller, raw_string, selected_class=None, **kwargs):
    """Set the chosen class on the character."""
    char = caller.new_char
    char.db.char_class = selected_class
    char.db.char_class_name = CLASSES[selected_class]["name"]
    return "menunode_stats"


# -------------------------------------------------------------------
#  Stat Allocation (fieldfill-style)
# -------------------------------------------------------------------

def menunode_stats(caller, raw_string="", **kwargs):
    """Allocate bonus stat points on top of rolled base stats."""
    char = caller.new_char
    char.db.chargen_step = "menunode_stats"

    race_key = char.db.race

    # Roll base stats on first visit (or if rerolled)
    if not char.db.base_stats:
        rolls = _roll_base_stats()
        char.db.base_stats = _apply_racial_mods(rolls, race_key)
        char.db.wip_stats = dict(char.db.base_stats)

    base = char.db.base_stats
    wip = char.db.wip_stats
    stat_table = _format_stat_table(wip, base)

    help_text = (
        "|wStat Allocation Help|n\n\n"
        "|wDEX vs AGI:|n DEX = precision (aim, fingers, fine work).\n"
        "            AGI = whole-body movement (speed, dodging, acrobatics).\n"
        "|wCON vs END:|n CON = raw toughness (absorb punishment).\n"
        "            END = sustained effort (keep going longer).\n"
        "|wWIS vs PER:|n WIS = inner insight (magic attunement, willpower, faith).\n"
        "            PER = outward awareness (noticing things, spotting danger)."
    )

    text = (
        "|wAllocate Your Stats|n  (rolled 3d6 + racial mods)\n\n"
        f"  |wstat = value|n to set   |wreroll|n   |wreset|n   |wback|n   |wdone|n   |whelp|n\n"
        f"  Min: {STAT_MIN}  |  Max: {STAT_MAX}  |  Bonus points: {BONUS_POINTS}\n\n"
        f"{stat_table}"
    )

    options = {"key": "_default", "goto": _handle_stat_input}
    return (text, help_text), options


def _handle_stat_input(caller, raw_string, **kwargs):
    """Parse stat allocation commands."""
    char = caller.new_char
    race_key = char.db.race
    base = char.db.base_stats
    wip = char.db.wip_stats
    cmd = raw_string.strip().lower()

    if cmd in ("done", "d"):
        spent = _calc_points_spent(wip, base)
        if spent < BONUS_POINTS:
            caller.msg(
                f"|yWarning: you have {BONUS_POINTS - spent} unspent points.|n "
                "Type |wdone|n again to continue anyway, or keep allocating."
            )
            if kwargs.get("warned_unspent"):
                return "menunode_summary"
            return "menunode_stats", {"warned_unspent": True}
        return "menunode_summary"

    if cmd in ("back", "b"):
        return "menunode_class_list"

    if cmd in ("reroll", "roll", "re"):
        rolls = _roll_base_stats()
        char.db.base_stats = _apply_racial_mods(rolls, race_key)
        char.db.wip_stats = dict(char.db.base_stats)
        caller.msg("|yNew stats rolled!|n")
        return "menunode_stats"

    if cmd in ("reset", "r"):
        char.db.wip_stats = dict(char.db.base_stats)
        caller.msg("|yAllocations reset to base values.|n")
        return "menunode_stats"

    # Parse "stat = value"
    if "=" not in cmd:
        caller.msg("|rSyntax: stat = value|n  (e.g. |wstr = 14|n)  or |wreroll|n / |wreset|n / |wdone|n")
        return "menunode_stats"

    parts = cmd.split("=", 1)
    stat_name = parts[0].strip()
    value_str = parts[1].strip()

    # Match stat abbreviation
    matched_stat = None
    for s in STAT_KEYS:
        if stat_name in (s, BASE_STATS[s]["abbr"].lower(), BASE_STATS[s]["name"].lower()):
            matched_stat = s
            break

    if not matched_stat:
        caller.msg(f"|rUnknown stat '{stat_name}'.|n Valid: {', '.join(BASE_STATS[s]['abbr'] for s in STAT_KEYS)}")
        return "menunode_stats"

    try:
        new_val = int(value_str)
    except ValueError:
        caller.msg("|rPlease enter a number.|n")
        return "menunode_stats"

    if new_val < STAT_MIN:
        caller.msg(f"|rMinimum stat value is {STAT_MIN}.|n")
        return "menunode_stats"

    if new_val > STAT_MAX:
        caller.msg(f"|rMaximum stat value is {STAT_MAX}.|n")
        return "menunode_stats"

    # Check point budget
    old_val = wip[matched_stat]
    wip[matched_stat] = new_val
    spent = _calc_points_spent(wip, base)
    if spent > BONUS_POINTS:
        wip[matched_stat] = old_val
        caller.msg(f"|rNot enough points. That would require {spent}/{BONUS_POINTS} bonus points.|n")
        return "menunode_stats"

    # Don't allow lowering below base
    if new_val < base[matched_stat]:
        wip[matched_stat] = old_val
        caller.msg(f"|rCan't lower {BASE_STATS[matched_stat]['abbr']} below its base of {base[matched_stat]}.|n")
        return "menunode_stats"

    char.db.wip_stats = wip
    caller.msg(f"|w{BASE_STATS[matched_stat]['abbr']}|n set to |w{new_val}|n.")
    return "menunode_stats"


# -------------------------------------------------------------------
#  Summary
# -------------------------------------------------------------------

def menunode_summary(caller, raw_string="", **kwargs):
    """Show full character summary before confirming."""
    char = caller.new_char
    char.db.chargen_step = "menunode_summary"

    race_key = char.db.race
    rdata = STARTER_RACES.get(race_key) or UNLOCKABLE_RACES[race_key]
    cdata = CLASSES[char.db.char_class]
    wip = char.db.wip_stats

    langs = ", ".join(LANGUAGES[l]["name"] for l in rdata["languages"])
    traits = ", ".join(rdata["traits"])

    # Build two-column stat display (5 rows x 2 columns)
    stat_rows = []
    half = len(STAT_KEYS) // 2
    for i in range(half):
        left = STAT_KEYS[i]
        right = STAT_KEYS[i + half]
        stat_rows.append(
            f"    {BASE_STATS[left]['abbr']}: |w{wip[left]:>2}|n"
            f"        "
            f"{BASE_STATS[right]['abbr']}: |w{wip[right]:>2}|n"
        )
    stat_block = "\n".join(stat_rows)

    text = (
        f"|w=============================================\n"
        f"  Character Summary\n"
        f"=============================================|n\n"
        f"\n"
        f"  |wName:|n  {char.key}\n"
        f"  |wRace:|n  {rdata['name']}\n"
        f"  |wClass:|n {cdata['name']} ({cdata['category']})\n"
        f"\n"
        f"  |wStats:|n\n"
        f"{stat_block}\n"
        f"\n"
        f"  |wLanguages:|n {langs}\n"
        f"  |wTraits:|n    {traits}\n"
        f"\n"
        f"  |wConfirm this character?|n\n"
    )

    options = [
        {
            "key": ("Confirm", "confirm", "yes", "y"),
            "desc": "Confirm and enter the game",
            "goto": "menunode_end",
        },
        {
            "key": ("Back", "back", "b"),
            "desc": "Go back to stat allocation",
            "goto": "menunode_stats",
        },
        {
            "key": ("Restart", "restart"),
            "desc": "Start over from the beginning",
            "goto": _restart_chargen,
        },
    ]
    return text, options


def _restart_chargen(caller, raw_string, **kwargs):
    """Reset all chargen data and restart."""
    char = caller.new_char
    char.db.race = None
    char.db.race_name = None
    char.db.char_class = None
    char.db.char_class_name = None
    char.db.base_stats = None
    char.db.wip_stats = None
    return "menunode_choose_name"


# -------------------------------------------------------------------
#  End — finalize character
# -------------------------------------------------------------------

def menunode_end(caller, raw_string="", **kwargs):
    """Apply all chargen choices and finalize the character."""
    char = caller.new_char

    race_key = char.db.race
    rdata = STARTER_RACES.get(race_key) or UNLOCKABLE_RACES[race_key]
    wip = char.db.wip_stats

    # Apply final stat values to TraitHandler
    if hasattr(char, "traits") and char.traits:
        for s in STAT_KEYS:
            trait = char.traits.get(s)
            if trait:
                trait.base = wip[s]

    # Set languages
    char.db.languages = {lang: 1.0 for lang in rdata["languages"]}

    # Move to starting location
    try:
        start_rooms = evennia.search_tag("commons_nw", category="awtown_dbkey")
        if start_rooms:
            char.db.prelogout_location = start_rooms[0]
    except Exception:
        pass

    # Clean up work-in-progress data
    char.attributes.remove("base_stats")
    char.attributes.remove("wip_stats")
    char.attributes.remove("chargen_step")

    text = dedent(f"""\
        |w=============================================|n
        |g  {char.key} has been created!|n
        |w=============================================|n

          Race:  {rdata['name']}
          Class: {CLASSES[char.db.char_class]['name']}

        Welcome to the Land of Dorfin!
    """)

    return text, None
