"""
DorfinMUD Combat Configuration
===============================

Pure data module — no Evennia imports. Safe to import from combat_rules.py
and anywhere else.

Contains:
    - Character level XP thresholds (1-90)
    - Stat point level milestones
    - Recommended mob XP formula
"""


# ---------------------------------------------------------------------------
# Character Leveling (1-90)
# ---------------------------------------------------------------------------

MAX_CHARACTER_LEVEL = 90

# XP required to reach each level (index = level, so [0] is unused).
# Formula: int(level ** 2.3 * 15)
CHARACTER_LEVEL_XP = [0] + [int(lvl ** 2.3 * 15) for lvl in range(1, MAX_CHARACTER_LEVEL + 1)]

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
