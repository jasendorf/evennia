# DorfinMUD — Login Menu & Character Creation

## Overview

Multi-character account system with a guided character creation wizard.
Players see a character-select menu on every login instead of being
auto-puppeted. New characters are created through an EvMenu-based flow
covering name, race, class, and stat allocation.

Built on two Evennia contribs:

- **character_creator** (`evennia.contrib.rpg.character_creator`) — provides
  the `charcreate` command, in-progress character tracking (`chargen_step`
  db attribute), and `ContribChargenAccount` base class.
- **fieldfill** pattern — stat allocation uses `stat = value` input syntax
  inspired by the fieldfill contrib, implemented inline within the chargen
  EvMenu (not as a separate EvMenu).

---

## Files

| File | Purpose |
|---|---|
| `world/chargen.py` | EvMenu nodes for character creation + all race/class/stat data |
| `world/login_menu.py` | EvMenu nodes for post-login character select screen |
| `commands/command_chargen.py` | `@chargen` admin command to re-run creation |
| `typeclasses/accounts.py` | Account typeclass — inherits `ContribChargenAccount`, overrides `at_post_login` |
| `typeclasses/characters.py` | Added `db.languages` default to `_init_flags()` |
| `commands/default_cmdsets.py` | Wires `ContribChargenCmdSet` (Account) + `CmdChargen` (Character) |

Settings in `configmap.yaml` → `game-settings.py`:

```python
AUTO_CREATE_CHARACTER_WITH_ACCOUNT = False
AUTO_PUPPET_ON_LOGIN = False
MAX_NR_CHARACTERS = 6
CHARGEN_MENU = "world.chargen"
```

---

## Login Menu Flow

```
Player authenticates (account + password)
    │
    ▼
Account.at_post_login()
    │
    ▼
EvMenu on Account → menunode_charselect
    │
    ├── play <name/#>  → puppet character, end menu
    ├── create         → charcreate command → chargen EvMenu
    ├── who            → show online players
    └── quit           → disconnect
```

### Display

```
=====================================
  Welcome back, John!
  The Land of Dorfin awaits.
=====================================

  Your characters:
    1. Yith (Level 5 Human Warrior)
    2. Kira [IN PROGRESS] (type create to continue)

  Character slots: 2/6

  Commands:
    play <name or #>    — enter the game
    create              — create a new character
    who                 — see who's online
    quit                — disconnect
```

### Key Details

- **Caller is the Account** (not a session or character).
- The `session` kwarg is passed through EvMenu nodes for puppeting.
- Pre-existing characters (no `chargen_step`, no `db.race`) display with
  whatever data is available — name and level at minimum.
- In-progress characters (with `chargen_step` set) show as `[IN PROGRESS]`.
- `create` delegates to the contrib's `charcreate` command, which handles
  creating the character object and launching the chargen EvMenu.
- If an in-progress character exists, `create` resumes it instead of
  starting a new one.

---

## Character Creation Flow

```
menunode_welcome
    │
    ▼
menunode_choose_name  ← validate: 3-20 chars, alpha only, unique
    │
    ▼
menunode_race_list    ← 12 starter races + 8 locked
    │
    ▼
menunode_race_detail  ← desc, stat mods, languages, traits → confirm
    │
    ▼
menunode_class_list   ← 24 classes in 3 categories
    │
    ▼
menunode_class_detail ← desc → confirm
    │
    ▼
menunode_stats        ← fieldfill-style: "str = 14", "reset", "done"
    │
    ▼
menunode_summary      ← full sheet → confirm / back / restart
    │
    ▼
menunode_end          ← apply stats, set languages, move to start room
```

### Important: Caller = Session

The character_creator contrib passes the **session** as the EvMenu caller
(not the Account). The character being created is accessed via
`caller.new_char`. This is different from the login menu where caller is
the Account.

### Character Lifecycle During Chargen

1. `charcreate` command creates a character with a random temporary key.
2. `chargen_step` is set to `"menunode_welcome"` — marks it as in-progress.
3. Each node updates `chargen_step` to its own name (for resume support).
4. At `menunode_choose_name`, the temp key is replaced with the player's
   chosen name.
5. Race/class choices are stored on `char.db` as they're made (for resume).
6. Stat allocations are stored in `char.db.wip_stats` dict during the
   allocation step.
7. At `menunode_end`, final stat values are written to `traits[key].base`,
   `chargen_step` is removed, and the character is moved to the start room.
8. The contrib's finish callback puppets the character via the `ic` command.

### Resume

If a player disconnects mid-chargen:
- The character object persists with `chargen_step` set.
- On next login, the login menu shows it as `[IN PROGRESS]`.
- Typing `create` runs `charcreate`, which finds the existing in-progress
  character and resumes at the saved `chargen_step` node.

---

## Races

### 12 Starter Races

| Race | Stat Mods | Languages | Racial Trait |
|---|---|---|---|
| Human | STR+1, CON+1, CHA+1 | Common | Fast learner: +10% XP gain |
| Elf | DEX+2, INT+1, CON-1 | Common, Elvish | Keen senses: Perception bonus in forests |
| Dwarf | CON+2, STR+1, AGI-1 | Common, Dwarvish | Stone-hearted: poison resistance |
| Halfling | AGI+2, LCK+1, STR-1 | Common, Halfling | Lucky: reroll one crit fail/day |
| Gnome | INT+2, DEX+1, STR-1 | Common, Dwarvish | Tinker's mind: crafting bonus |
| Half-Elf | CHA+2, PER+1, CON-1 | Common, Elvish | Diplomatic: Persuasion bonus |
| Half-Orc | STR+2, END+1, CHA-1 | Common, Orcish | Savage strikes: crit damage bonus |
| Orc | STR+2, CON+1, INT-1 | Common, Orcish | Battle fury: bonus damage below 25% HP |
| Goblin | AGI+2, PER+1, STR-1 | Common, Goblin | Scavenger: extra loot |
| Troll | CON+2, STR+1, DEX-1 | Common, Giant | Regeneration: HP regen out of combat |
| Hobgoblin | END+2, WIS+1, CHA-1 | Common, Goblin, Orcish | Tactical mind: initiative bonus |
| Lizardfolk | CON+2, PER+1, CHA-1 | Common, Draconic | Natural armor: +2 base armor |

### 8 Unlockable Races

Shown as locked in chargen with unlock hints:

- Dragonborn (level 20), Tabaxi (50 rooms), Kenku (5 languages),
  Goliath (solo boss), Firbolg (Herbalism), Changeling (Shadow Chamber quest),
  Dark Elf (level 30 Elf), Tortle (100 combats no flee)

---

## Classes (24)

### Martial (8)
Warrior, Paladin, Ranger, Barbarian, Knight, Monk, Samurai, Swashbuckler

### Magic (9)
Mage, Wizard, Sorcerer, Warlock, Necromancer, Illusionist, Elementalist,
Druid, Shaman

### Stealth & Support (7)
Rogue, Thief, Assassin, Bard, Cleric, Healer, Scout, Tinkerer

---

## Stats

10 stats, all base 10. Racial mods applied first, then 15 bonus points
to allocate freely.

| Stat | Abbr | Description |
|---|---|---|
| Strength | STR | Carry weight, melee damage, grappling |
| Dexterity | DEX | Precision: archery, lockpicking, fine work |
| Agility | AGI | Whole-body: speed, dodge, initiative |
| Constitution | CON | Raw toughness: HP, poison/disease resist |
| Endurance | END | Sustained effort: stamina, travel fatigue |
| Intelligence | INT | Spell power, learning, crafting |
| Wisdom | WIS | Inner insight: mana, willpower, faith |
| Perception | PER | Outward awareness: traps, hidden exits |
| Charisma | CHA | NPC reactions, prices, persuasion |
| Luck | LCK | Crits, rare drops, random events |

### Allocation Rules

- Min: 3 per stat (after all mods)
- Max: 20 per stat at creation
- Bonus points: 15 to distribute freely
- Input syntax: `str = 14`, `reset`, `done`

### Stat Split Explanations

- **DEX vs AGI**: DEX = precision (aim, fingers). AGI = movement (speed, dodge).
- **CON vs END**: CON = absorb punishment. END = keep going longer.
- **WIS vs PER**: WIS = inner insight (magic, willpower). PER = outward awareness.

---

## Character Attributes Set by Chargen

| Attribute | Example | Set When |
|---|---|---|
| `db.race` | `"elf"` | Race confirmed |
| `db.race_name` | `"Elf"` | Race confirmed |
| `db.char_class` | `"ranger"` | Class confirmed |
| `db.char_class_name` | `"Ranger"` | Class confirmed |
| `db.languages` | `{"common": 1.0, "elvish": 1.0}` | menunode_end |
| `db.wip_stats` | `{"str": 12, ...}` | During stat allocation (removed at end) |
| `traits[stat].base` | Modified values | menunode_end |
| `db.chargen_step` | `"menunode_stats"` | Each node (removed at end) |

### Pre-existing Characters

Characters that existed before chargen was added (like Yith) have no
`chargen_step` and no `db.race`. They are treated as complete:
- Login menu shows them normally (name + level, no race/class)
- They are never forced through chargen
- `db.chargen_step is None` → not in progress
- `db.race is None` → just omitted from display

---

## Starting Location

After chargen completes, `db.prelogout_location` is set to The Wayfarers'
Green (tag `"commons_nw"`, category `"awtown_dbkey"`). The character is
moved there when first puppeted.

---

## @chargen Admin Command

```
@chargen [<character>]
```

- Admin/Builder only
- Without args: runs on your current puppet
- With args: targets named character
- Resets race, class, stats (to base 10), and languages
- Starts chargen at the race step (skips name — character keeps its name)

---

## Testing Checklist

1. Create new account → see login menu, NOT auto-puppet
2. `create` → chargen starts at welcome
3. Walk through name → race → class → stats → summary → confirm
4. `score` → stats = base 10 + racial mods + allocations
5. Character lands at The Wayfarers' Green
6. Disconnect + reconnect → login menu shows character
7. `play 1` → puppets character
8. Create second character → slots show 2/6
9. Yith (pre-existing) shows in list, plays without issues
10. `@chargen` re-runs creation on existing character
11. Interrupt chargen (disconnect) → `[IN PROGRESS]`, `create` resumes
12. `@reload` mid-chargen → EvMenu survives
13. 7th character → blocked by MAX_NR_CHARACTERS
