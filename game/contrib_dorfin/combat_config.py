"""
DorfinMUD Combat Configuration
===============================

Pure data module — no Evennia imports. Safe to import from combat_rules.py
and anywhere else.

Contains:
    - Character level XP thresholds (1-90)
    - Stat point level milestones
    - Recommended mob XP formula
    - Weapon categories, tiers, and skill thresholds
    - Class proficiencies and opposed weapons
    - Race combat modifiers
    - Monk unarmed scaling
"""


# ---------------------------------------------------------------------------
# Character Leveling (1-90)
# ---------------------------------------------------------------------------

MAX_CHARACTER_LEVEL = 90

# XP required to reach each level (index = level, so [0] is unused).
# Blended formula: ((level^2.3 * 28) + (level^2.5 * 15)) / 2
CHARACTER_LEVEL_XP = [0] + [
    int(((lvl ** 2.3 * 28) + (lvl ** 2.5 * 15)) / 2)
    for lvl in range(1, MAX_CHARACTER_LEVEL + 1)
]

# Levels that grant a stat point (every 5 levels, 18 total)
STAT_POINT_LEVELS = list(range(5, MAX_CHARACTER_LEVEL + 1, 5))

# HP growth per level: +5 + CON // 2
HP_PER_LEVEL_BASE = 5


# ---------------------------------------------------------------------------
# Recommended mob XP (guideline for new content)
# ---------------------------------------------------------------------------

def recommended_xp(mob_level):
    """
    Suggested XP value for a mob of a given level.

    Level 1: 11, Level 10: 200, Level 30: 1200, Level 50: 3000, Level 90: 9000
    """
    return mob_level * 10 + mob_level ** 2


# ---------------------------------------------------------------------------
# Weapon Categories & Tiers
# ---------------------------------------------------------------------------

WEAPON_CATEGORIES = (
    "sword", "dagger", "axe", "club", "staff",
    "polearm", "bow", "crossbow", "unarmed", "shield",
)

WEAPON_TIERS = {
    "starter":   {"min_level": 1,  "max_level": 5},
    "common":    {"min_level": 6,  "max_level": 15},
    "uncommon":  {"min_level": 16, "max_level": 30},
    "rare":      {"min_level": 31, "max_level": 50},
    "epic":      {"min_level": 51, "max_level": 70},
    "legendary": {"min_level": 71, "max_level": 85},
    "mythic":    {"min_level": 86, "max_level": 90},
}


# ---------------------------------------------------------------------------
# Weapon Skills (0-30)
# ---------------------------------------------------------------------------

MAX_WEAPON_SKILL_LEVEL = 30

# Cumulative XP needed to reach each skill level (index = level).
WEAPON_SKILL_XP_THRESHOLDS = [
    0, 10, 25, 50, 80, 120, 170, 230, 300, 380, 470,          # 0-10
    570, 680, 800, 930, 1070, 1220, 1380, 1550, 1730, 1920,    # 11-20
    2130, 2360, 2610, 2880, 3170, 3490, 3840, 4220, 4630, 5100,  # 21-30
]

# Monk unarmed dice scale with unarmed weapon skill level.
MONK_UNARMED_DICE = {
    0: "1d6", 3: "1d6+2", 7: "1d8+1", 12: "1d10+2",
    18: "2d6+3", 25: "2d8+4", 30: "2d10+4",
}


# ---------------------------------------------------------------------------
# Class Proficiencies (three-tier: proficient / unfamiliar / opposed)
# ---------------------------------------------------------------------------

CLASS_PROFICIENCIES = {
    "warrior":      ["sword", "axe", "club", "polearm", "shield"],
    "paladin":      ["sword", "club", "shield", "polearm"],
    "ranger":       ["sword", "dagger", "bow"],
    "barbarian":    ["axe", "club", "unarmed"],
    "knight":       ["sword", "polearm", "shield"],
    "monk":         ["unarmed", "staff"],
    "archer":       ["bow", "crossbow", "dagger"],
    "hunter":       ["bow", "dagger", "axe"],
    "mage":         ["staff", "dagger"],
    "wizard":       ["staff", "dagger"],
    "sorcerer":     ["staff", "dagger"],
    "warlock":      ["staff", "dagger"],
    "necromancer":  ["staff", "dagger"],
    "illusionist":  ["staff", "dagger"],
    "elementalist": ["staff"],
    "druid":        ["staff", "club"],
    "shaman":       ["staff", "club"],
    "rogue":        ["dagger", "sword", "crossbow"],
    "thief":        ["dagger", "crossbow"],
    "assassin":     ["dagger", "crossbow", "sword"],
    "bard":         ["sword", "dagger", "staff"],
    "cleric":       ["club", "staff", "shield"],
    "healer":       ["staff", "club"],
    "scout":        ["bow", "dagger", "sword"],
    "tinkerer":     ["crossbow", "dagger"],
}

CLASS_OPPOSED = {
    "monk":         ["sword", "dagger", "axe", "club", "polearm",
                     "bow", "crossbow", "shield"],
    "paladin":      ["bow", "crossbow", "dagger"],
    "knight":       ["bow", "crossbow", "dagger"],
    "barbarian":    ["crossbow", "shield"],
    "archer":       ["club", "polearm", "shield"],
    "mage":         ["sword", "axe", "club", "polearm", "shield"],
    "wizard":       ["sword", "axe", "club", "polearm", "shield"],
    "sorcerer":     ["sword", "axe", "club", "polearm", "shield"],
    "warlock":      ["sword", "axe", "polearm", "shield"],
    "necromancer":  ["sword", "axe", "polearm", "shield"],
    "illusionist":  ["sword", "axe", "club", "polearm", "shield"],
    "elementalist": ["sword", "axe", "club", "polearm", "shield",
                     "dagger"],
    "druid":        ["sword", "axe", "crossbow"],
    "shaman":       ["sword", "axe", "crossbow"],
    "thief":        ["axe", "polearm", "shield"],
    "cleric":       ["sword", "dagger", "bow", "crossbow"],
    "healer":       ["sword", "dagger", "axe", "bow", "crossbow"],
}


# ---------------------------------------------------------------------------
# Race Combat Modifiers (attack roll bonus/penalty per weapon category)
# ---------------------------------------------------------------------------

RACE_COMBAT_MODS = {
    "human":     {"weapon_skill_xp_bonus": 0.10},
    "elf":       {"bow": 5, "sword": 2, "club": -3},
    "dwarf":     {"axe": 5, "club": 3, "bow": -5, "crossbow": -3},
    "halfling":  {"dagger": 5, "crossbow": 3, "polearm": -5},
    "gnome":     {"crossbow": 5, "dagger": 2, "axe": -3, "polearm": -5},
    "half_elf":  {"bow": 3, "sword": 2},
    "half_orc":  {"axe": 3, "club": 3, "bow": -5},
    "orc":       {"axe": 5, "club": 5, "bow": -8, "crossbow": -5},
    "goblin":    {"dagger": 5, "crossbow": 3, "polearm": -5},
    "troll":     {"unarmed": 8, "dagger": -5, "bow": -5},
    "hobgoblin": {"sword": 2, "polearm": 3, "shield": 2},
    "lizardfolk": {"unarmed": 5, "bow": -8, "crossbow": -5},
    "dark_elf":  {"crossbow": 5, "dagger": 3, "club": -3},
    "dragonborn": {"sword": 3, "polearm": 2, "dagger": -3},
    "tabaxi":    {"dagger": 5, "unarmed": 3, "polearm": -5},
    "kenku":     {"dagger": 3, "crossbow": 3, "club": -3},
    "goliath":   {"club": 5, "axe": 5, "dagger": -5},
    "firbolg":   {"staff": 5, "club": 3, "dagger": -3},
    "changeling": {"dagger": 3, "sword": 2},
    "tortle":    {"club": 3, "shield": 5, "bow": -5, "unarmed": 3},
}
