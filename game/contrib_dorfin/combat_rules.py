"""
DorfinMUD Combat Rules Engine
==============================

All combat math lives here. Pure functions — no commands, no scripts,
no message strings with game flavor. The combat handler and commands
call these functions to resolve actions.

Every function that takes a combatant expects an object with:
    get_stat(key)       -> int   (STR, DEX, AGI, CON, END, INT, WIS, PER, CHA, LCK)
    get_hp()            -> int
    get_hp_max()        -> int
    get_equipped(slot)  -> item object or None

Weapons are expected to have:
    db.damage_dice      -> str   (e.g. "1d6", "2d4+3")
    db.damage_bonus     -> int

This module has zero imports from DorfinMUD typeclasses — it works with
any object that satisfies the interface above.

Formulas
--------

    Initiative:     AGI + PER + rand(1,20) + LCK // 5
    Melee attack:   rand(1,100) + STR + DEX
    Defense:        50 + AGI + PER + armor_bonus
    Melee damage:   roll(weapon.damage_dice) + weapon.damage_bonus + STR // 3 + buff_damage_bonus
    Unarmed damage: 1d4 + STR // 4
    Flee chance:    (AGI + LCK) vs (opponent_PER + 10)  -> percentage
    Rescue:         STR + CHA + rand(1,20) vs mob_WIS + mob_level * 2 + 10
    Consider:       compare effective power -> qualitative string
"""

import re
from random import randint


# ---------------------------------------------------------------------------
# Dice roller
# ---------------------------------------------------------------------------

_DICE_RE = re.compile(
    r"^\s*(\d+)\s*[dD]\s*(\d+)"           # NdS  (required)
    r"(!!?p?(?:>[0-9]+)?)?"               # exploding: ! !! !p !!p !>5 etc.
    r"(?:([kd])([hl]?)(\d+))?"            # keep/drop: k3 kh2 kl1 d1 dl1
    r"(?:r(o?)([<>])(\d+))?"              # reroll: r<2 ro<3 r>5
    r"(?:\s*([+-])\s*(\d+))?\s*$"         # modifier: +3 -1
)

# Safety cap to prevent infinite loops on exploding dice.
_MAX_EXPLOSIONS = 100


def roll_dice(dice_str):
    """
    Parse and roll an extended dice notation string.

    Supports standard RPG dice notation plus modifiers:

        NdS         Basic roll: N dice with S sides, summed.
        NdS+M       Flat modifier added to total.
        NdS!        Exploding: max roll adds another die.
        NdS!!       Compounding: explosions sum into one die value.
        NdS!p       Penetrating: explosions subtract 1 per extra roll.
        NdS!>T      Exploding on T or higher (instead of max only).
        NdSkH       Keep highest H dice (e.g. 4d6k3).
        NdSkl1      Keep lowest 1 die (e.g. 2d20kl1).
        NdSdL       Drop lowest L dice (e.g. 4d6d1).
        NdSdh1      Drop highest 1 die.
        NdSr<T      Reroll any die below T (keep new value).
        NdSro<T     Reroll once below T (keep new even if still low).

    Modifiers can be combined: 4d6!k3+2

    Args:
        dice_str (str): Dice notation string.

    Returns:
        int: Total roll result (minimum 1).

    Raises:
        ValueError: If the dice string cannot be parsed.

    Examples:
        >>> roll_dice("1d6")        # 1-6
        >>> roll_dice("2d4+3")      # 5-11
        >>> roll_dice("1d8!")       # exploding d8
        >>> roll_dice("4d6k3")     # roll 4d6, keep best 3
        >>> roll_dice("1d6!>5+2")  # explode on 5+, then +2
    """
    match = _DICE_RE.match(str(dice_str))
    if not match:
        raise ValueError(f"Invalid dice string: '{dice_str}'")

    num = int(match.group(1))
    sides = int(match.group(2))
    explode_str = match.group(3) or ""
    kd_mode = match.group(4) or ""        # "k" or "d" or ""
    kd_end = match.group(5) or ""         # "h" or "l" or ""
    kd_count = int(match.group(6)) if match.group(6) else 0
    reroll_once = match.group(7) or ""    # "o" or ""
    reroll_cmp = match.group(8) or ""     # "<" or ">" or ""
    reroll_val = int(match.group(9)) if match.group(9) else 0
    sign = match.group(10)
    modifier = int(match.group(11)) if match.group(11) else 0

    if sign == "-":
        modifier = -modifier

    if num <= 0 or sides <= 0:
        raise ValueError(f"Invalid dice string: '{dice_str}'")

    # --- Determine exploding mode ---
    exploding = "!" in explode_str
    compounding = "!!" in explode_str
    penetrating = "p" in explode_str
    explode_threshold = sides  # default: explode on max
    thresh_match = re.search(r">(\d+)", explode_str)
    if thresh_match:
        explode_threshold = int(thresh_match.group(1))

    # --- Roll the dice ---
    rolls = []
    for _ in range(num):
        die_total = 0
        roll = randint(1, sides)

        if not exploding:
            # Simple roll, no explosions.
            rolls.append(roll)
            continue

        if compounding:
            # Compounding: all explosions sum into one value.
            die_total = roll
            explosions = 0
            while roll >= explode_threshold and explosions < _MAX_EXPLOSIONS:
                roll = randint(1, sides)
                if penetrating:
                    roll = max(1, roll - 1)
                die_total += roll
                explosions += 1
            rolls.append(die_total)
        else:
            # Standard exploding: each explosion is a separate "die".
            if penetrating:
                rolls.append(roll)
                explosions = 0
                while roll >= explode_threshold and explosions < _MAX_EXPLOSIONS:
                    roll = max(1, randint(1, sides) - 1)
                    rolls.append(roll)
                    explosions += 1
            else:
                rolls.append(roll)
                explosions = 0
                while roll >= explode_threshold and explosions < _MAX_EXPLOSIONS:
                    roll = randint(1, sides)
                    rolls.append(roll)
                    explosions += 1

    # --- Reroll ---
    if reroll_cmp:
        for i, r in enumerate(rolls):
            should_reroll = (
                (reroll_cmp == "<" and r < reroll_val)
                or (reroll_cmp == ">" and r > reroll_val)
            )
            if should_reroll:
                new_roll = randint(1, sides)
                if reroll_once:
                    # Reroll once: keep new value regardless.
                    rolls[i] = new_roll
                else:
                    # Reroll until it no longer triggers.
                    attempts = 0
                    while (
                        ((reroll_cmp == "<" and new_roll < reroll_val)
                         or (reroll_cmp == ">" and new_roll > reroll_val))
                        and attempts < _MAX_EXPLOSIONS
                    ):
                        new_roll = randint(1, sides)
                        attempts += 1
                    rolls[i] = new_roll

    # --- Keep / Drop ---
    if kd_mode and kd_count > 0:
        sorted_rolls = sorted(rolls)
        if kd_mode == "k":
            # Keep
            if kd_end == "l":
                rolls = sorted_rolls[:kd_count]
            else:
                # Default "k" or "kh" = keep highest
                rolls = sorted_rolls[-kd_count:]
        elif kd_mode == "d":
            # Drop
            if kd_end == "h":
                rolls = sorted_rolls[:-kd_count] if kd_count < len(sorted_rolls) else []
            else:
                # Default "d" or "dl" = drop lowest
                rolls = sorted_rolls[kd_count:]

    total = sum(rolls) + modifier
    return max(1, total)


# ---------------------------------------------------------------------------
# Stat access helpers
# ---------------------------------------------------------------------------

def _stat(combatant, key, default=10):
    """
    Safely read a stat from a combatant.

    Works with AwtownCharacter (get_stat method + buff system) and
    AwtownMob (get_stat method backed by db.stats dict).
    """
    if hasattr(combatant, "get_stat"):
        try:
            return combatant.get_stat(key)
        except Exception:
            return default
    return default


def _level(combatant, default=1):
    """Read a combatant's level."""
    if hasattr(combatant, "db") and hasattr(combatant.db, "level"):
        return combatant.db.level or default
    return default


def _weapon(combatant):
    """
    Return the weapon object in the combatant's main hand, or None.

    Works with any object that has get_equipped("weapon").
    """
    if hasattr(combatant, "get_equipped"):
        try:
            return combatant.get_equipped("weapon")
        except Exception:
            return None
    return None


def _armor_bonus(combatant, default=0):
    """
    Read the combatant's effective armor bonus.

    For player characters, armor_bonus flows through the BuffHandler
    (from worn AwtownClothing with stat_mods). We read it via
    buffs.check() if available. For mobs, it's a db attribute.
    """
    # Try buff system first (player characters)
    if hasattr(combatant, "buffs") and combatant.buffs:
        try:
            return int(combatant.buffs.check(0, "armor_bonus"))
        except Exception:
            pass

    # Fallback: db attribute (mobs)
    if hasattr(combatant, "db"):
        val = getattr(combatant.db, "armor_bonus", None)
        if val is not None:
            return val

    return default


def _damage_bonus(combatant, default=0):
    """
    Read the combatant's effective damage bonus from buffs.

    For player characters, damage_bonus comes from Hammerfall's Blessing
    and weapon bonuses, all flowing through the BuffHandler.
    For mobs, it's a db attribute.
    """
    if hasattr(combatant, "buffs") and combatant.buffs:
        try:
            return int(combatant.buffs.check(0, "damage_bonus"))
        except Exception:
            pass

    if hasattr(combatant, "db"):
        val = getattr(combatant.db, "damage_bonus", None)
        if val is not None:
            return val

    return default


# ---------------------------------------------------------------------------
# Initiative
# ---------------------------------------------------------------------------

def roll_initiative(combatant):
    """
    Roll initiative for turn ordering and first-strike determination.

    Formula: AGI + PER + rand(1,20) + LCK // 5

    Higher values act first.

    Args:
        combatant: Object with get_stat().

    Returns:
        int: Initiative value.
    """
    agi = _stat(combatant, "agi")
    per = _stat(combatant, "per")
    lck = _stat(combatant, "lck")
    return agi + per + randint(1, 20) + lck // 5


# ---------------------------------------------------------------------------
# Attack and defense
# ---------------------------------------------------------------------------

def get_attack_roll(attacker, defender):
    """
    Calculate an attack roll value for a melee attack.

    Formula: rand(1,100) + STR + DEX

    Args:
        attacker: The attacking combatant.
        defender: The defending combatant (unused in base formula,
                  passed for future expansion — e.g. flanking bonuses).

    Returns:
        int: Attack roll value, compared against defense value.
    """
    str_val = _stat(attacker, "str")
    dex_val = _stat(attacker, "dex")
    return randint(1, 100) + str_val + dex_val


def get_defense_value(defender):
    """
    Calculate the defense value an attack must meet or exceed to hit.

    Formula: 50 + AGI + PER + armor_bonus

    Args:
        defender: The defending combatant.

    Returns:
        int: Defense threshold.
    """
    agi = _stat(defender, "agi")
    per = _stat(defender, "per")
    armor = _armor_bonus(defender)
    return 50 + agi + per + armor


# ---------------------------------------------------------------------------
# Damage
# ---------------------------------------------------------------------------

def get_damage(attacker, defender):
    """
    Calculate damage dealt by a successful melee attack.

    With weapon:
        roll(weapon.damage_dice) + weapon.damage_bonus + STR // 3 + buff_damage_bonus

    Without weapon (unarmed):
        1d4 + STR // 4

    Args:
        attacker: The attacking combatant.
        defender: The defending combatant (unused in base formula,
                  passed for future expansion — e.g. damage resistance).

    Returns:
        int: Damage value (minimum 1).
    """
    weapon = _weapon(attacker)
    str_val = _stat(attacker, "str")
    buff_dmg = _damage_bonus(attacker)

    if weapon:
        dice_str = getattr(weapon.db, "damage_dice", "1d4") if hasattr(weapon, "db") else "1d4"
        weapon_bonus = getattr(weapon.db, "damage_bonus", 0) if hasattr(weapon, "db") else 0
        base = roll_dice(dice_str)
        total = base + weapon_bonus + str_val // 3 + buff_dmg
    else:
        # Unarmed
        base = roll_dice("1d4")
        total = base + str_val // 4

    return max(1, total)


def get_mob_damage(mob):
    """
    Calculate damage dealt by a mob's natural attack.

    Uses mob.db.damage_dice if set, otherwise falls back to 1d4.
    Adds STR // 3 as a bonus.

    Args:
        mob: The attacking mob.

    Returns:
        int: Damage value (minimum 1).
    """
    dice_str = "1d4"
    if hasattr(mob, "db"):
        dice_str = getattr(mob.db, "damage_dice", "1d4") or "1d4"

    # Mobs can also wield weapons
    weapon = _weapon(mob)
    str_val = _stat(mob, "str")
    buff_dmg = _damage_bonus(mob)

    if weapon:
        w_dice = getattr(weapon.db, "damage_dice", dice_str) if hasattr(weapon, "db") else dice_str
        w_bonus = getattr(weapon.db, "damage_bonus", 0) if hasattr(weapon, "db") else 0
        base = roll_dice(w_dice)
        total = base + w_bonus + str_val // 3 + buff_dmg
    else:
        base = roll_dice(dice_str)
        total = base + str_val // 3 + buff_dmg

    return max(1, total)


# ---------------------------------------------------------------------------
# Full attack resolution
# ---------------------------------------------------------------------------

def resolve_attack(attacker, defender):
    """
    Resolve a single attack: roll to hit, calculate damage if successful.

    Args:
        attacker: The attacking combatant.
        defender: The defending combatant.

    Returns:
        dict: Result with keys:
            hit (bool)       : Whether the attack landed.
            attack_roll (int): The attack roll value.
            defense (int)    : The defense threshold.
            damage (int)     : Damage dealt (0 on miss).
    """
    attack_roll = get_attack_roll(attacker, defender)
    defense = get_defense_value(defender)
    hit = attack_roll >= defense

    damage = 0
    if hit:
        # Use mob damage path if the attacker is a mob without get_equipped
        if hasattr(attacker, "db") and getattr(attacker.db, "is_mob", False):
            damage = get_mob_damage(attacker)
        else:
            damage = get_damage(attacker, defender)

    return {
        "hit": hit,
        "attack_roll": attack_roll,
        "defense": defense,
        "damage": damage,
    }


# ---------------------------------------------------------------------------
# Flee
# ---------------------------------------------------------------------------

def check_flee(fleer, opponents):
    """
    Determine whether a flee attempt succeeds.

    Formula: (AGI + LCK) vs (strongest_opponent_PER + 10)
    Rolled as a percentage check: succeed if rand(1,100) <= flee_chance.

    The flee chance is clamped between 10% (always some hope) and 90%
    (never guaranteed).

    Args:
        fleer: The combatant attempting to flee.
        opponents (list): List of combatants opposing the fleer.

    Returns:
        dict: Result with keys:
            success (bool)     : Whether the flee succeeded.
            flee_chance (int)  : The calculated flee percentage.
    """
    agi = _stat(fleer, "agi")
    lck = _stat(fleer, "lck")
    fleer_score = agi + lck

    # Strongest opponent's perception
    if opponents:
        best_per = max(_stat(opp, "per") for opp in opponents)
    else:
        best_per = 10

    opponent_score = best_per + 10

    # Convert to percentage: base 50%, shifted by the difference
    difference = fleer_score - opponent_score
    flee_chance = 50 + difference * 2
    flee_chance = max(10, min(90, flee_chance))

    roll = randint(1, 100)
    return {
        "success": roll <= flee_chance,
        "flee_chance": flee_chance,
    }


# ---------------------------------------------------------------------------
# Rescue
# ---------------------------------------------------------------------------

RESCUE_COOLDOWN = 15  # seconds


def check_rescue(rescuer, mob):
    """
    Determine whether a rescue attempt succeeds.

    Formula: STR + CHA + rand(1,20) vs mob_WIS + mob_level * 2 + 10

    Args:
        rescuer: The combatant attempting to rescue.
        mob: The mob whose aggro is being pulled.

    Returns:
        dict: Result with keys:
            success (bool)       : Whether the rescue succeeded.
            rescuer_roll (int)   : The rescuer's total roll.
            mob_threshold (int)  : The threshold to beat.
    """
    str_val = _stat(rescuer, "str")
    cha_val = _stat(rescuer, "cha")
    rescuer_roll = str_val + cha_val + randint(1, 20)

    mob_wis = _stat(mob, "wis")
    mob_lvl = _level(mob)
    mob_threshold = mob_wis + mob_lvl * 2 + 10

    return {
        "success": rescuer_roll >= mob_threshold,
        "rescuer_roll": rescuer_roll,
        "mob_threshold": mob_threshold,
    }


# ---------------------------------------------------------------------------
# Consider
# ---------------------------------------------------------------------------

def _effective_power(combatant):
    """
    Calculate a rough power rating for consider comparisons.

    Combines level, HP, and key combat stats into a single number.
    Not meant to be displayed — only used for relative comparison.
    """
    level = _level(combatant)
    hp_max = 100
    if hasattr(combatant, "get_hp_max"):
        try:
            hp_max = combatant.get_hp_max()
        except Exception:
            pass

    str_val = _stat(combatant, "str")
    dex_val = _stat(combatant, "dex")
    agi_val = _stat(combatant, "agi")
    con_val = _stat(combatant, "con")
    armor = _armor_bonus(combatant)

    return (
        level * 15
        + hp_max
        + str_val * 2
        + dex_val
        + agi_val
        + con_val * 2
        + armor
    )


# Consider result thresholds — (min_ratio, message)
# Ratio = target_power / player_power
CONSIDER_RATINGS = [
    (0.00, "You could kill {name} in your sleep."),
    (0.40, "{name} would be an easy fight."),
    (0.70, "{name} shouldn't pose much of a challenge."),
    (0.90, "{name} looks like an even match."),
    (1.10, "{name} looks like a tough fight."),
    (1.40, "{name} would be very dangerous."),
    (1.80, "{name} would obliterate you."),
]


def get_consider_message(character, target):
    """
    Return a qualitative difficulty assessment string.

    Compares effective power ratings between character and target.

    Args:
        character: The player character doing the considering.
        target: The mob or NPC being considered.

    Returns:
        str: A qualitative assessment string with {name} replaced
             by the target's display name.
    """
    player_power = _effective_power(character)
    target_power = _effective_power(target)

    if player_power <= 0:
        ratio = 999.0
    else:
        ratio = target_power / player_power

    # Walk the thresholds in reverse to find the highest matching bracket
    message = CONSIDER_RATINGS[-1][1]
    for min_ratio, msg in CONSIDER_RATINGS:
        if ratio < min_ratio + 0.001:
            break
        message = msg

    # Get target name
    name = "it"
    if hasattr(target, "get_display_name"):
        try:
            name = target.get_display_name(character)
        except Exception:
            name = getattr(target, "key", "it")
    elif hasattr(target, "key"):
        name = target.key

    return message.format(name=name)
