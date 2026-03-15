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
    - Weapon skill milestones (perks at 3, 7, 12, 18, 25)
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


# ---------------------------------------------------------------------------
# Weapon Skill Milestones (perks at 3, 7, 12, 18, 25)
# ---------------------------------------------------------------------------
#
# Each entry: (skill_level, effect_type, value, name)
#
# For upgrade chains (same effect_type at higher level), the resolver
# picks the highest-level entry at or below the combatant's skill.
#
# Effect types:
#   Passive (applied in combat_rules formulas):
#     passive_initiative  - flat initiative bonus
#     passive_accuracy    - flat attack roll bonus
#     passive_defense     - flat defense bonus
#     passive_damage      - flat damage bonus
#     passive_block       - block% without shield (like parry)
#     crit_chance_bonus   - flat crit% bonus
#     crit_multiplier     - override crit damage multiplier (default 1.5)
#     armor_ignore_pct    - % of target armor to bypass
#     execute_threshold   - +50% damage vs targets below this HP%
#     berserker           - (bonus_dmg, defense_penalty) tuple
#
#   Proc/Stateful (handled in combat_handler):
#     stun_chance         - % chance to stun on hit (skip next attack)
#     bonus_attack_chance - % chance of extra attack on hit
#     riposte_chance      - % counter-attack when enemy misses you
#     bleed               - (dmg_per_round, rounds) DoT on hit
#     armor_shatter       - reduce target defense on hit
#     defense_shatter     - (chance%, reduction) reduce all enemy defense
#     backstab_multiplier - first attack in combat damage multiplier
#     damage_reduction_chance - % chance to debuff target damage by 25%
#     on_kill_cleave      - on kill, deal N% damage to another enemy
#     on_kill_attack_all  - on kill, attack all remaining enemies
#     first_round_attack_all - first round, attack all enemies
#     first_attack_defense   - bonus defense until first hit received
#     unarmed_dice_upgrade   - upgrade non-monk unarmed dice (1d4 -> 1d6)

WEAPON_MILESTONES = {
    "sword": [
        (3,  "passive_defense",     3,    "Parry Stance"),
        (7,  "riposte_chance",      5,    "Riposte"),
        (12, "passive_block",       5,    "Parry"),
        (18, "bonus_attack_chance", 10,   "Blade Dance"),
        (25, "on_kill_attack_all",  True, "Whirlwind"),
    ],
    "dagger": [
        (3,  "passive_initiative",   3,   "Quick Hands"),
        (7,  "passive_initiative",   5,   "Quick Strike"),
        (12, "backstab_multiplier",  1.5, "Backstab"),
        (18, "crit_multiplier",      2.0, "Eviscerate"),
        (25, "crit_multiplier",      2.5, "Death Strike"),
    ],
    "axe": [
        (3,  "passive_damage",      2,      "Heavy Swing"),
        (7,  "on_kill_cleave",      50,     "Cleave"),
        (12, "bleed",              (3, 2),  "Rend"),
        (18, "execute_threshold",   25,     "Execute"),
        (25, "berserker",         (5, 5),   "Berserker"),
    ],
    "club": [
        (3,  "stun_chance",    3,  "Daze"),
        (7,  "stun_chance",    5,  "Stun"),
        (12, "armor_shatter",  3,  "Shatter"),
        (18, "stun_chance",    10, "Concuss"),
    ],
    "staff": [
        (3, "passive_defense",   3,      "Reach"),
        (7, "defense_shatter",  (5, 5),  "Sweep"),
    ],
    "polearm": [
        (3, "first_attack_defense", 5,  "Set"),
        (7, "first_attack_defense", 10, "Brace"),
    ],
    "bow": [
        (3,  "passive_accuracy",        3,    "Focus"),
        (7,  "passive_accuracy",        5,    "Steady Aim"),
        (12, "bonus_attack_chance",     15,   "Rapid Shot"),
        (18, "crit_chance_bonus",       10,   "Aimed Shot"),
        (25, "first_round_attack_all",  True, "Arrow Storm"),
    ],
    "crossbow": [
        (3,  "passive_damage",    2,   "Brace Shot"),
        (7,  "armor_ignore_pct",  50,  "Pierce"),
        (12, "crit_chance_bonus", 5,   "Headshot"),
        (18, "armor_ignore_pct",  100, "Siege Shot"),
    ],
    "unarmed": [
        (3,  "bonus_attack_chance",      10,   "Quick Jab"),
        (7,  "bonus_attack_chance",      15,   "Flurry"),
        (12, "unarmed_dice_upgrade",     True, "Iron Fist"),
        (18, "damage_reduction_chance",  5,    "Pressure Points"),
        (25, "bonus_attack_chance",      25,   "Thousand Fists"),
    ],
    "shield": [],
}
