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
        "stat_mods": {"str": 1, "con": 1, "cha": 1},
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
        "stat_mods": {"dex": 2, "int": 1, "con": -1},
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
        "stat_mods": {"con": 2, "str": 1, "agi": -1},
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
        "stat_mods": {"agi": 2, "lck": 1, "str": -1},
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
        "stat_mods": {"int": 2, "dex": 1, "str": -1},
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
        "stat_mods": {"cha": 2, "per": 1, "con": -1},
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
        "stat_mods": {"str": 2, "end": 1, "cha": -1},
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
        "stat_mods": {"str": 2, "con": 1, "int": -1},
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
        "stat_mods": {"agi": 2, "per": 1, "str": -1},
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
        "stat_mods": {"con": 2, "str": 1, "dex": -1},
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
        "stat_mods": {"end": 2, "wis": 1, "cha": -1},
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
        "stat_mods": {"con": 2, "per": 1, "cha": -1},
        "languages": ["common", "draconic"],
        "traits": ["Natural armor: +2 base armor bonus"],
    },
}

UNLOCKABLE_RACES = {
    "dragonborn": {
        "name": "Dragonborn",
        "desc": "Draconic heritage, breath weapon, proud culture.",
        "unlock_hint": "Reach level 20 with any character.",
    },
    "tabaxi": {
        "name": "Tabaxi",
        "desc": "Feline agility, curiosity-driven, natural explorers.",
        "unlock_hint": "Discover 50 unique rooms.",
    },
    "kenku": {
        "name": "Kenku",
        "desc": "Flightless corvids, mimic speech rather than speak naturally.",
        "unlock_hint": "Learn 5 languages on any character.",
    },
    "goliath": {
        "name": "Goliath",
        "desc": "Mountain-born giants, competitive, endurance-focused.",
        "unlock_hint": "Defeat a boss enemy solo.",
    },
    "firbolg": {
        "name": "Firbolg",
        "desc": "Gentle forest giants, druidic affinity, reclusive.",
        "unlock_hint": "Master the Herbalism profession.",
    },
    "changeling": {
        "name": "Changeling",
        "desc": "Shapeshifters, identity-fluid, socially dangerous.",
        "unlock_hint": "Complete the Shadow Chamber questline.",
    },
    "dark_elf": {
        "name": "Dark Elf",
        "desc": "Subterranean elves, magic-touched, mistrusted on the surface.",
        "unlock_hint": "Reach level 30 with an Elf character.",
    },
    "tortle": {
        "name": "Tortle",
        "desc": "Shelled wanderers, patient, long-lived, natural survivalists.",
        "unlock_hint": "Survive 100 combats without fleeing.",
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
    "samurai": {
        "name": "Samurai",
        "category": "Martial",
        "desc": (
            "Precision swordsmen bound by a warrior's honor. They specialize in "
            "devastating burst damage and single-combat duels."
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

def _get_racial_base(race_key):
    """Return a dict of stat values with racial mods applied to base 10."""
    mods = STARTER_RACES[race_key]["stat_mods"]
    return {s: BASE_STAT + mods.get(s, 0) for s in STAT_KEYS}


def _calc_points_spent(wip_stats, race_key):
    """Return how many bonus points have been allocated."""
    racial = _get_racial_base(race_key)
    return sum(wip_stats[s] - racial[s] for s in STAT_KEYS)


def _format_stat_table(wip_stats, race_key):
    """Build an EvTable showing current stat allocation."""
    racial = _get_racial_base(race_key)
    spent = _calc_points_spent(wip_stats, race_key)
    remaining = BONUS_POINTS - spent

    table = EvTable(
        "|wStat|n", "|wBase|n", "|wRacial|n", "|wAlloc|n", "|wTotal|n",
        border="cells", align="c", width=60,
    )
    for s in STAT_KEYS:
        mod = racial[s] - BASE_STAT
        alloc = wip_stats[s] - racial[s]
        mod_str = f"+{mod}" if mod > 0 else str(mod) if mod != 0 else " "
        alloc_str = f"+{alloc}" if alloc > 0 else str(alloc) if alloc != 0 else " "
        table.add_row(
            f"|w{BASE_STATS[s]['abbr']}|n",
            str(BASE_STAT),
            mod_str,
            alloc_str,
            str(wip_stats[s]),
        )
    return str(table) + f"\n\n  |wBonus points remaining: {remaining}/{BONUS_POINTS}|n"


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
    """)
    options = {"key": "_default", "goto": _check_name}
    return text, options


def _check_name(caller, raw_string, **kwargs):
    """Validate and set the character name."""
    name = raw_string.strip()

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

    lines = ["|wChoose Your Race|n\n"]

    for i, rkey in enumerate(_STARTER_RACE_LIST, 1):
        rdata = STARTER_RACES[rkey]
        mods = ", ".join(
            f"{BASE_STATS[s]['abbr']} {'+' if v > 0 else ''}{v}"
            for s, v in rdata["stat_mods"].items()
        )
        lines.append(f"  |w{i:>2}|n. |c{rdata['name']:<12}|n  ({mods})")

    lines.append("\n  |x--- Locked Races ---|n")
    for rdata in UNLOCKABLE_RACES.values():
        lines.append(f"  |x    {rdata['name']:<12}  [locked: {rdata['unlock_hint']}]|n")

    lines.append("\nEnter a number or race name to learn more.")

    text = "\n".join(lines)
    options = {"key": "_default", "goto": _select_race}
    return text, options


def _select_race(caller, raw_string, **kwargs):
    """Parse race selection input."""
    choice = raw_string.strip().lower()

    # Try as number
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(_STARTER_RACE_LIST):
            return "menunode_race_detail", {"selected_race": _STARTER_RACE_LIST[idx]}
    except ValueError:
        pass

    # Try as name
    for rkey, rdata in STARTER_RACES.items():
        if choice in (rkey, rdata["name"].lower()):
            return "menunode_race_detail", {"selected_race": rkey}

    # Check if they tried a locked race
    for rkey, rdata in UNLOCKABLE_RACES.items():
        if choice in (rkey, rdata["name"].lower()):
            caller.msg(f"|r{rdata['name']} is locked.|n {rdata['unlock_hint']}")
            return "menunode_race_list"

    caller.msg("|rInvalid choice.|n Enter a number (1-12) or race name.")
    return "menunode_race_list"


def menunode_race_detail(caller, raw_string="", selected_race=None, **kwargs):
    """Show details for a selected race and confirm."""
    if not selected_race:
        return "menunode_race_list"

    rdata = STARTER_RACES[selected_race]
    mods_lines = []
    for s, v in rdata["stat_mods"].items():
        sign = "+" if v > 0 else ""
        mods_lines.append(f"    {BASE_STATS[s]['abbr']}: {sign}{v}")

    langs = ", ".join(LANGUAGES[l]["name"] for l in rdata["languages"])
    traits = "\n    ".join(rdata["traits"])

    text = dedent(f"""\
        |w{rdata['name']}|n

        {rdata['desc']}

        |wStat Modifiers:|n
        {chr(10).join(mods_lines)}

        |wLanguages:|n {langs}
        |wRacial Traits:|n
            {traits}
    """)

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
    char.db.race_name = STARTER_RACES[selected_race]["name"]
    # Initialize wip_stats with racial mods
    char.db.wip_stats = _get_racial_base(selected_race)
    return "menunode_class_list"


# -------------------------------------------------------------------
#  Class Selection
# -------------------------------------------------------------------

def menunode_class_list(caller, raw_string="", **kwargs):
    """Display classes grouped by category."""
    char = caller.new_char
    char.db.chargen_step = "menunode_class_list"

    lines = ["|wChoose Your Class|n\n"]

    categories = {}
    for ckey, cdata in CLASSES.items():
        categories.setdefault(cdata["category"], []).append((ckey, cdata))

    idx = 0
    for cat_name, class_list in categories.items():
        lines.append(f"\n  |w--- {cat_name} ---|n")
        for ckey, cdata in class_list:
            idx += 1
            lines.append(f"  |w{idx:>2}|n. |c{cdata['name']}|n")

    lines.append("\nEnter a number or class name to learn more.")

    text = "\n".join(lines)
    options = {"key": "_default", "goto": _select_class}
    return text, options


def _select_class(caller, raw_string, **kwargs):
    """Parse class selection input."""
    choice = raw_string.strip().lower()

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

    caller.msg("|rInvalid choice.|n Enter a number (1-24) or class name.")
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
    """Allocate bonus stat points using field = value syntax."""
    char = caller.new_char
    char.db.chargen_step = "menunode_stats"

    race_key = char.db.race

    # Ensure wip_stats exist (resume case)
    if not char.db.wip_stats:
        char.db.wip_stats = _get_racial_base(race_key)

    wip = char.db.wip_stats
    stat_table = _format_stat_table(wip, race_key)

    help_text = dedent("""\
        |wStat Allocation Help|n

        |wDEX vs AGI:|n DEX = precision (aim, fingers, fine work).
                    AGI = whole-body movement (speed, dodging, acrobatics).
        |wCON vs END:|n CON = raw toughness (absorb punishment).
                    END = sustained effort (keep going longer).
        |wWIS vs PER:|n WIS = inner insight (magic attunement, willpower, faith).
                    PER = outward awareness (noticing things, spotting danger).
    """)

    text = dedent(f"""\
        |wAllocate Your Stats|n

        Set stats by typing:  |wstat = value|n  (e.g. |wstr = 14|n)
        Other commands:       |wreset|n  |wdone|n  |whelp|n

        Min: {STAT_MIN}  |  Max: {STAT_MAX}  |  Bonus points: {BONUS_POINTS}

        {stat_table}
    """)

    options = {"key": "_default", "goto": _handle_stat_input}
    return (text, help_text), options


def _handle_stat_input(caller, raw_string, **kwargs):
    """Parse stat allocation commands."""
    char = caller.new_char
    race_key = char.db.race
    wip = char.db.wip_stats
    cmd = raw_string.strip().lower()

    if cmd in ("done", "d"):
        spent = _calc_points_spent(wip, race_key)
        if spent < BONUS_POINTS:
            caller.msg(
                f"|yWarning: you have {BONUS_POINTS - spent} unspent points.|n "
                "Type |wdone|n again to continue anyway, or keep allocating."
            )
            # Set a flag so second 'done' proceeds
            if kwargs.get("warned_unspent"):
                return "menunode_summary"
            return "menunode_stats", {"warned_unspent": True}
        return "menunode_summary"

    if cmd in ("reset", "r"):
        char.db.wip_stats = _get_racial_base(race_key)
        caller.msg("|yStats reset to racial base values.|n")
        return "menunode_stats"

    # Parse "stat = value"
    if "=" not in cmd:
        caller.msg("|rSyntax: stat = value|n  (e.g. |wstr = 14|n)  or |wreset|n / |wdone|n")
        return "menunode_stats"

    parts = cmd.split("=", 1)
    stat_name = parts[0].strip()
    value_str = parts[1].strip()

    # Match stat abbreviation
    matched_stat = None
    for s in STAT_KEYS:
        if stat_name == s or stat_name == BASE_STATS[s]["abbr"].lower() or stat_name == BASE_STATS[s]["name"].lower():
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
    spent = _calc_points_spent(wip, race_key)
    if spent > BONUS_POINTS:
        wip[matched_stat] = old_val
        caller.msg(f"|rNot enough points. That would require {spent}/{BONUS_POINTS} bonus points.|n")
        return "menunode_stats"

    # Check racial minimum
    racial_base = _get_racial_base(race_key)
    if new_val < racial_base[matched_stat] - (BASE_STAT - STAT_MIN):
        wip[matched_stat] = old_val
        caller.msg(f"|rCan't lower {BASE_STATS[matched_stat]['abbr']} below {STAT_MIN}.|n")
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
    rdata = STARTER_RACES[race_key]
    cdata = CLASSES[char.db.char_class]
    wip = char.db.wip_stats

    langs = ", ".join(LANGUAGES[l]["name"] for l in rdata["languages"])
    traits = ", ".join(rdata["traits"])

    stat_lines = []
    for s in STAT_KEYS:
        stat_lines.append(f"    {BASE_STATS[s]['abbr']}: |w{wip[s]:>2}|n")

    text = dedent(f"""\
        |w=============================================
          Character Summary
        =============================================|n

          |wName:|n  {char.key}
          |wRace:|n  {rdata['name']}
          |wClass:|n {cdata['name']} ({cdata['category']})

        |wStats:|n
        {chr(10).join(stat_lines)}

        |wLanguages:|n {langs}
        |wTraits:|n    {traits}

        |wConfirm this character?|n
    """)

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
    char.db.wip_stats = None
    return "menunode_choose_name"


# -------------------------------------------------------------------
#  End — finalize character
# -------------------------------------------------------------------

def menunode_end(caller, raw_string="", **kwargs):
    """Apply all chargen choices and finalize the character."""
    char = caller.new_char

    race_key = char.db.race
    rdata = STARTER_RACES[race_key]
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
