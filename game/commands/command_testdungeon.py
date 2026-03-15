"""
@testdungeon - Create an isolated, comprehensive test area.

Creates a multi-room dungeon disconnected from the game world that exercises
every major system: combat, weapons, equipment, shops, consumables, loot,
flee, rest, party combat, weapon skills, and leveling.

Usage:
    @testdungeon            Create the dungeon and teleport there.
    @testdungeon/teardown   Destroy the test dungeon and return home.
"""

from evennia.commands.command import Command
from evennia import create_object, search_object
from evennia.objects.models import ObjectDB


# Tag used to identify all test dungeon objects for cleanup.
_TAG = "testdungeon"
_TAG_CATEGORY = "testdungeon"


def _tag(obj):
    """Mark an object as part of the test dungeon."""
    obj.tags.add(_TAG, category=_TAG_CATEGORY)


def _exit(src, dest, key, aliases=None):
    """Create a tagged exit between two rooms."""
    from evennia import DefaultExit
    ex = create_object(
        DefaultExit, key=key,
        location=src, destination=dest,
        aliases=aliases or [],
    )
    _tag(ex)
    return ex


def _room(key, desc, is_safe=True, room_type="arena"):
    """Create a tagged test room."""
    from typeclasses.rooms import AwtownRoom
    room = create_object(AwtownRoom, key=key)
    room.db.desc = desc
    room.db.is_safe = is_safe
    room.db.room_type = room_type
    room.db.is_outdoor = False
    _tag(room)
    return room


def _mob(room, name, hp, level, damage_dice="1d4", xp_value=10,
         armor_bonus=0, stats=None, loot_table=None, respawn=30,
         move_mode="stationary", wander_chance=0.5, chase=False,
         chase_range=3):
    """Spawn a tagged mob with respawn."""
    from contrib_dorfin.mob_spawner import spawn_and_track
    mob, script = spawn_and_track(
        room, name=name, hp=hp, level=level,
        damage_dice=damage_dice, xp_value=xp_value,
        armor_bonus=armor_bonus, respawn_delay=respawn,
        move_mode=move_mode, wander_chance=wander_chance,
        chase=chase, chase_range=chase_range,
    )
    if stats:
        mob.db.stats.update(stats)
    if loot_table:
        mob.db.loot_table = loot_table
    _tag(mob)
    if script:
        _tag(script)
    return mob


def _weapon(room, name, dice, bonus=0, category="sword",
            wtype="melee", hands=1, block_chance=0, armor_bonus=0,
            slot="weapon"):
    """Create a tagged weapon on the ground."""
    from typeclasses.items import AwtownWeapon
    wpn = create_object(AwtownWeapon, key=name, location=room)
    wpn.db.desc = f"A test {name}."
    wpn.db.damage_dice = dice
    wpn.db.damage_bonus = bonus
    wpn.db.weapon_category = category
    wpn.db.weapon_type = wtype
    wpn.db.hands = hands
    wpn.db.block_chance = block_chance
    wpn.db.armor_bonus = armor_bonus
    wpn.db.slot = slot
    wpn.db.value = 0
    _tag(wpn)
    return wpn


def _clothing(room, name, clothing_type, stat_mods=None):
    """Create a tagged clothing item on the ground."""
    from typeclasses.items import AwtownClothing
    item = create_object(AwtownClothing, key=name, location=room)
    item.db.desc = f"A test {name}."
    item.db.clothing_type = clothing_type
    item.db.value = 0
    if stat_mods:
        item.db.stat_mods = stat_mods
    _tag(item)
    return item


def _food(room, name, nutrition=25, hydration=0, hp_restore=0, count=1):
    """Create tagged consumable food."""
    from typeclasses.items import AwtownConsumable
    items = []
    for _ in range(count):
        item = create_object(AwtownConsumable, key=name, location=room)
        item.db.desc = f"A test {name}."
        item.db.nutrition = nutrition
        item.db.hydration = hydration
        item.db.hp_restore = hp_restore
        item.db.value = 0
        _tag(item)
        items.append(item)
    return items


def _drink(room, name, sips=5, hydration_per=10, hp_per=0):
    """Create a tagged drinkable."""
    from typeclasses.items import AwtownDrinkable
    item = create_object(AwtownDrinkable, key=name, location=room)
    item.db.desc = f"A test {name}."
    item.db.sips = sips
    item.db.sips_max = sips
    item.db.hydration_per = hydration_per
    item.db.hp_per = hp_per
    item.db.value = 0
    _tag(item)
    return item


def _container(room, name, capacity=10):
    """Create a tagged container."""
    from typeclasses.items import AwtownContainer
    item = create_object(AwtownContainer, key=name, location=room)
    item.db.desc = f"A test {name}."
    item.db.capacity = capacity
    item.db.value = 0
    _tag(item)
    return item


def _npc(room, name, role="merchant", shop_inventory=None, dialogue=None):
    """Create a tagged NPC."""
    from typeclasses.npcs import AwtownNPC
    npc = create_object(AwtownNPC, key=name, location=room)
    npc.db.npc_role = role
    if shop_inventory:
        npc.db.shop_inventory = shop_inventory
    if dialogue:
        npc.db.dialogue = dialogue
    _tag(npc)
    return npc


# -------------------------------------------------------------------------
# Dungeon builder
# -------------------------------------------------------------------------

def build_test_dungeon(caller):
    """Build the full test dungeon and return the hub room."""

    # ------------------------------------------------------------------
    # 1. HUB — safe starting room with instructions
    # ------------------------------------------------------------------
    hub = _room(
        "|wTest Dungeon Hub|n",
        "A circular stone chamber lit by floating orbs. Doorways lead "
        "in every direction, each marked with a glowing sign. This room "
        "is |gsafe|n — no combat can start here.\n\n"
        "|yDirections:|n\n"
        "  |cnorth|n  — Weapon Armory (pick up & wield weapons)\n"
        "  |ceast|n   — Easy Combat (level 1 dummy)\n"
        "  |csouth|n  — Equipment Room (armor & clothing)\n"
        "  |cwest|n   — Shop & Consumables\n"
        "  |cup|n     — Loot Testing (mob with drops)\n"
        "  |cdown|n   — Advanced Combat Wing\n"
        "  |cnortheast|n — Level-Up Chamber (500 XP pinata)\n"
        "  |csoutheast|n — Class & Race Testing (proficiency/milestones)",
        is_safe=True,
    )

    # ------------------------------------------------------------------
    # 2. WEAPON ARMORY — every weapon type on the ground
    # ------------------------------------------------------------------
    armory = _room(
        "|wWeapon Armory|n",
        "Racks of weapons line every wall. Test picking up and wielding "
        "different weapon types.\n\n"
        "|yTests:|n wield, unwield, wield offhand, eq, look <weapon>\n"
        "|yInstructions:|n\n"
        "  1. |cget sword|n then |cwield sword|n — check eq\n"
        "  2. |cwield dagger offhand|n — dual wield\n"
        "  3. |cunwield|n and |cunwield offhand|n\n"
        "  4. |cwield staff|n — 2H weapon\n"
        "  5. |clook shield|n — should show block%/armor\n"
        "  6. |clook bow|n — should show 'ranged' type",
        is_safe=True,
    )
    # One of every category
    _weapon(armory, "test sword", "1d6", category="sword")
    _weapon(armory, "test dagger", "1d3+1", category="dagger")
    _weapon(armory, "test axe", "1d8", category="axe")
    _weapon(armory, "test club", "1d6", category="club")
    _weapon(armory, "test staff", "1d4+1", category="staff", hands=2)
    _weapon(armory, "test polearm", "1d8", category="polearm", hands=2)
    _weapon(armory, "test bow", "1d6", category="bow", wtype="ranged", hands=2)
    _weapon(armory, "test crossbow", "1d8", category="crossbow", wtype="ranged", hands=2)
    # Offhand weapons
    _weapon(armory, "offhand dagger", "1d3", category="dagger", slot="offhand")
    # Shield
    _weapon(armory, "test shield", "1d2", category="shield", wtype="shield",
            slot="offhand", block_chance=15, armor_bonus=5)
    # Strong 2H weapon for later rooms
    _weapon(armory, "heavy greatsword", "2d6+2", bonus=1, category="sword", hands=2)

    _exit(hub, armory, "north", ["armory", "weapons", "n"])
    _exit(armory, hub, "south", ["hub", "back", "s"])

    # ------------------------------------------------------------------
    # 3. EASY COMBAT — single weak mob
    # ------------------------------------------------------------------
    easy = _room(
        "|wEasy Combat Room|n",
        "A dirt-floored sparring pit. A straw dummy shuffles about.\n\n"
        "|yTests:|n kill, combat ticks, damage, XP award, level-up, "
        "score, corpse, loot\n"
        "|yInstructions:|n\n"
        "  1. |ckill dummy|n — watch combat ticks (4s each)\n"
        "  2. After kill: |cscore|n — check XP gained\n"
        "  3. |cloot|n — grab anything from corpse\n"
        "  4. Wait 30s — dummy respawns\n"
        "  5. |cconsider dummy|n — check difficulty rating",
        is_safe=False,
    )
    _mob(easy, "a training dummy", hp=20, level=1, damage_dice="1d4",
         xp_value=15, stats={"str": 8, "dex": 8, "agi": 8, "per": 8})

    _exit(hub, easy, "east", ["easy", "combat", "e"])
    _exit(easy, hub, "west", ["hub", "back", "w"])

    # ------------------------------------------------------------------
    # 4. EQUIPMENT ROOM — armor and clothing with stat mods
    # ------------------------------------------------------------------
    equip_room = _room(
        "|wEquipment Room|n",
        "Mannequins display various pieces of armor and clothing.\n\n"
        "|yTests:|n wear, remove, eq, stat mod application/removal\n"
        "|yInstructions:|n\n"
        "  1. |cget chainmail|n then |cwear chainmail|n\n"
        "  2. |ceq|n — should show worn item\n"
        "  3. |cscore|n — check if armor_bonus changed\n"
        "  4. |cremove chainmail|n then |cscore|n — bonus should revert\n"
        "  5. Try the |cspeed boots|n — should boost AGI\n"
        "  6. Try the |cheavy plate|n — has a DEX penalty",
        is_safe=True,
    )
    _clothing(equip_room, "test chainmail", "top", {"armor_bonus": 5})
    _clothing(equip_room, "speed boots", "shoes", {"agi": 3})
    _clothing(equip_room, "heavy plate", "top", {"armor_bonus": 10, "dex": -2})
    _clothing(equip_room, "lucky hat", "hat", {"lck": 5})
    _clothing(equip_room, "leather gloves", "gloves", {"str": 1})

    _exit(hub, equip_room, "south", ["equipment", "armor", "s"])
    _exit(equip_room, hub, "north", ["hub", "back", "n"])

    # ------------------------------------------------------------------
    # 5. SHOP & CONSUMABLES — merchant NPC + food/drink on ground
    # ------------------------------------------------------------------
    shop = _room(
        "|wShop & Consumables|n",
        "A cluttered market stall. A merchant eyes you from behind the "
        "counter. Food and drink are scattered on a table nearby.\n\n"
        "|yTests:|n list, buy, sell, eat, drink, fill\n"
        "|yInstructions:|n\n"
        "  1. |clist|n — see merchant wares\n"
        "  2. |cbuy bread|n — purchase something\n"
        "  3. |csell test sword|n — if you have one\n"
        "  4. |ceat ration|n — test single-use consumable\n"
        "  5. |cdrink canteen|n — test multi-sip drinkable\n"
        "  6. |cdrink 3 canteen|n — multiple sips at once\n"
        "  7. |ceat healing salve|n — test HP restore",
        is_safe=True,
    )
    _npc(shop, "a test merchant", role="merchant", shop_inventory=[
        {"name": "Iron Sword", "price": 50, "desc": "A sturdy iron sword.",
         "key": "iron sword"},
        {"name": "Health Potion", "price": 30, "desc": "Restores some HP.",
         "key": "health potion"},
        {"name": "Bread Loaf", "price": 5, "desc": "Fresh bread.",
         "key": "bread loaf"},
        {"name": "Leather Cap", "price": 20, "desc": "Basic head protection.",
         "key": "leather cap"},
    ], dialogue={
        "hello": "Welcome to my shop! Type |clist|n to see my wares.",
        "help": "Use |cbuy <item>|n to purchase, |csell <item>|n to sell.",
    })
    # Consumables on the ground
    _food(shop, "test ration", nutrition=25, count=3)
    _food(shop, "healing salve", nutrition=0, hp_restore=20, count=2)
    _drink(shop, "test canteen", sips=5, hydration_per=15)
    _container(shop, "test sack", capacity=5)

    _exit(hub, shop, "west", ["shop", "market", "w"])
    _exit(shop, hub, "east", ["hub", "back", "e"])

    # ------------------------------------------------------------------
    # 6. LOOT TESTING — mob with guaranteed drops
    # ------------------------------------------------------------------
    loot_room = _room(
        "|wLoot Testing Room|n",
        "A chamber strewn with bones. Something lurks in the shadows.\n\n"
        "|yTests:|n loot tables, corpse creation, corpse decay, "
        "get from corpse\n"
        "|yInstructions:|n\n"
        "  1. |ckill goblin|n — mob has guaranteed loot drops\n"
        "  2. |cloot|n or |cget gold from corpse|n\n"
        "  3. Wait 2 minutes — corpse should decay\n"
        "  4. Mob respawns in 30s — kill again to verify loot",
        is_safe=False,
    )
    _mob(loot_room, "a loot goblin", hp=25, level=2, damage_dice="1d4",
         xp_value=25, loot_table=[
             {"name": "gold coin", "desc": "A shiny gold coin.", "value": 50,
              "chance": 1.0},
             {"name": "goblin ear", "desc": "A severed ear. Gross.", "value": 5,
              "chance": 1.0},
             {"name": "rare gem", "desc": "A glittering ruby.", "value": 200,
              "chance": 0.25},
         ])

    _exit(hub, loot_room, "up", ["loot", "u"])
    _exit(loot_room, hub, "down", ["hub", "back", "d"])

    # ------------------------------------------------------------------
    # 7. ADVANCED COMBAT WING — secondary hub
    # ------------------------------------------------------------------
    wing = _room(
        "|wAdvanced Combat Wing|n",
        "A long corridor with heavy doors on each side.\n\n"
        "|yDirections:|n\n"
        "  |cnorth|n — Flee Testing (fast mob, test flee/wimpy)\n"
        "  |ceast|n  — Multi-Mob Room (party/assist/rescue)\n"
        "  |csouth|n — Tough Fight (armored mob, test damage)\n"
        "  |cwest|n      — Weapon Skill Grind (weak mobs, farm XP)\n"
        "  |cnorthwest|n — Rest Room (safe, test rest command)\n"
        "  |csouthwest|n — Wander & Chase (mobs that move)\n"
        "  |cnortheast|n — Level-Up Chamber (500 XP pinata)\n"
        "  |cup|n        — Back to Hub",
        is_safe=True,
    )
    _exit(hub, wing, "down", ["advanced", "wing", "d"])
    _exit(wing, hub, "up", ["hub", "back", "u"])

    # ------------------------------------------------------------------
    # 8. FLEE TESTING — fast mob hard to flee from
    # ------------------------------------------------------------------
    flee_room = _room(
        "|wFlee Testing Room|n",
        "A narrow passage. A hawk-eyed sentinel blocks the way.\n\n"
        "|yTests:|n flee, wimpy auto-flee\n"
        "|yInstructions:|n\n"
        "  1. |ckill sentinel|n — it hits hard\n"
        "  2. |cflee|n — sentinel has high PER, hard to escape\n"
        "  3. |cwimpy 50|n then fight again — auto-flee at 50 HP\n"
        "  4. |cwimpy 0|n to disable",
        is_safe=False,
    )
    _mob(flee_room, "a hawk-eyed sentinel", hp=60, level=5,
         damage_dice="1d8+2", xp_value=80, armor_bonus=3,
         stats={"per": 25, "agi": 15, "str": 14, "dex": 12})

    _exit(wing, flee_room, "north", ["flee", "n"])
    _exit(flee_room, wing, "south", ["back", "s"])

    # ------------------------------------------------------------------
    # 9. MULTI-MOB ROOM — party combat, assist, rescue
    # ------------------------------------------------------------------
    multi = _room(
        "|wMulti-Mob Arena|n",
        "A wide arena with three opponents circling. Bring friends.\n\n"
        "|yTests:|n party combat, assist, rescue, autoassist, "
        "multiple targets\n"
        "|yInstructions:|n\n"
        "  1. Have a friend |cparty create|n, |cparty invite <you>|n\n"
        "  2. |cparty accept|n, |cautoassist|n\n"
        "  3. |ckill brute|n — party should auto-join\n"
        "  4. |cassist <friend>|n — switch to their target\n"
        "  5. |crescue <friend>|n — pull aggro from them\n"
        "  6. Solo: |ckill|n each mob individually to test target switching",
        is_safe=False,
    )
    _mob(multi, "a pit brute", hp=40, level=3, damage_dice="1d6+1",
         xp_value=50, stats={"str": 15, "con": 14})
    _mob(multi, "a pit archer", hp=25, level=2, damage_dice="1d6",
         xp_value=35, stats={"dex": 15, "per": 14})
    _mob(multi, "a pit healer", hp=30, level=2, damage_dice="1d4",
         xp_value=30, stats={"wis": 15, "cha": 12})

    _exit(wing, multi, "east", ["multi", "party", "e"])
    _exit(multi, wing, "west", ["back", "w"])

    # ------------------------------------------------------------------
    # 10. TOUGH FIGHT — high armor, high HP
    # ------------------------------------------------------------------
    tough = _room(
        "|wTough Fight Room|n",
        "A reinforced chamber. An armored golem stands motionless, "
        "waiting for a challenger.\n\n"
        "|yTests:|n armor_bonus effect on defense, sustained combat, "
        "consider accuracy\n"
        "|yInstructions:|n\n"
        "  1. |cconsider golem|n — should show 'tough' or 'dangerous'\n"
        "  2. |ckill golem|n — it has high armor, expect many misses\n"
        "  3. Try different weapons — 2H greatsword vs dagger\n"
        "  4. Note: golem hits back hard but slowly",
        is_safe=False,
    )
    _mob(tough, "an armored golem", hp=100, level=8, damage_dice="2d6",
         xp_value=200, armor_bonus=10,
         stats={"str": 18, "con": 20, "end": 16, "agi": 6, "dex": 8,
                "per": 10})

    _exit(wing, tough, "south", ["tough", "golem", "s"])
    _exit(tough, wing, "north", ["back", "n"])

    # ------------------------------------------------------------------
    # 11. WEAPON SKILL GRIND — weak mobs for farming weapon XP
    # ------------------------------------------------------------------
    grind = _room(
        "|wWeapon Skill Training|n",
        "Rows of straw targets animate when struck. They fall easily "
        "but keep coming back.\n\n"
        "|yTests:|n weapon skill XP gain, skill level-ups, milestones\n"
        "|yInstructions:|n\n"
        "  1. Equip a weapon of the category you want to train\n"
        "  2. |ckill target|n — weak, fast kills\n"
        "  3. |cskills|n — check weapon skill progress\n"
        "  4. |cskills <category>|n — see milestones and XP bar\n"
        "  5. At skill 3: first milestone unlocks!\n"
        "  6. Targets respawn every 15 seconds",
        is_safe=False,
    )
    _mob(grind, "a straw target", hp=10, level=1, damage_dice="1d3",
         xp_value=5, respawn=15,
         stats={"str": 5, "dex": 5, "agi": 5, "per": 5, "con": 5})
    _mob(grind, "a wooden target", hp=10, level=1, damage_dice="1d3",
         xp_value=5, respawn=15,
         stats={"str": 5, "dex": 5, "agi": 5, "per": 5, "con": 5})
    _mob(grind, "a padded target", hp=10, level=1, damage_dice="1d3",
         xp_value=5, respawn=15,
         stats={"str": 5, "dex": 5, "agi": 5, "per": 5, "con": 5})

    _exit(wing, grind, "west", ["grind", "skill", "w"])
    _exit(grind, wing, "east", ["back", "e"])

    # ------------------------------------------------------------------
    # 12. REST ROOM — safe, for testing rest command
    # ------------------------------------------------------------------
    rest_room = _room(
        "|wRest Room|n",
        "A quiet alcove with a cot and a water basin. Safe and calm.\n\n"
        "|yTests:|n rest, HP recovery\n"
        "|yInstructions:|n\n"
        "  1. Take some damage in a combat room first\n"
        "  2. Come here and type |crest|n\n"
        "  3. Wait 10 seconds — should recover ~5%% of max HP\n"
        "  4. |cscore|n — verify HP increased\n"
        "  5. Start resting, then type a command — should warn/cancel\n"
        "  |cse|n to go back to the Advanced Wing.",
        is_safe=True,
    )
    _exit(wing, rest_room, "northwest", ["rest", "nw"])
    _exit(rest_room, wing, "southeast", ["back", "se"])

    # ------------------------------------------------------------------
    # 13. WANDER & CHASE — mobs that move between rooms
    # ------------------------------------------------------------------
    wander_a = _room(
        "|wWander Room - West|n",
        "An open field. A rat scurries about aimlessly. A wolf stalks "
        "prey and will chase if you flee.\n\n"
        "|yTests:|n mob movement, wander, chase on flee\n"
        "|yInstructions:|n\n"
        "  1. Wait — the |cwandering rat|n should move between rooms\n"
        "  2. |ckill wolf|n then |cflee|n — wolf should follow\n"
        "  3. Move between east/west to watch mob behavior",
        is_safe=False,
    )
    wander_b = _room(
        "|wWander Room - East|n",
        "Another open stretch. Mobs may wander in from the west.\n\n"
        "|yTests:|n mob arrival/departure messages, chase continuation",
        is_safe=False,
    )

    _exit(wing, wander_a, "southwest", ["wander", "chase", "sw"])
    _exit(wander_a, wing, "northeast", ["back", "ne"])
    _exit(wander_a, wander_b, "east", ["e"])
    _exit(wander_b, wander_a, "west", ["w"])
    _exit(wander_b, wing, "north", ["back", "n"])

    _mob(wander_a, "a wandering rat", hp=12, level=1, damage_dice="1d3",
         xp_value=10, move_mode="wander", wander_chance=0.7, respawn=20)
    _mob(wander_a, "a stalking wolf", hp=30, level=3, damage_dice="1d6+1",
         xp_value=45, chase=True, chase_range=2, respawn=25,
         stats={"agi": 14, "per": 14, "str": 13})

    # ------------------------------------------------------------------
    # 14. LEVEL-UP ROOM — high XP mob for testing level-ups
    # ------------------------------------------------------------------
    levelup = _room(
        "|wLevel-Up Chamber|n",
        "A summoning circle glows on the floor. An XP pinata awaits.\n\n"
        "|yTests:|n XP gain, level-up, HP growth, stat point awards\n"
        "|yInstructions:|n\n"
        "  1. |cscore|n — note current XP and level\n"
        "  2. |ckill pinata|n — very weak but gives 500 XP\n"
        "  3. |cscore|n — check if you leveled up\n"
        "  4. If you got stat points: |ctrain str|n (or any stat)\n"
        "  5. Respawns in 20s — grind to test multi-level-up",
        is_safe=False,
    )
    _mob(levelup, "an XP pinata", hp=5, level=1, damage_dice="1d2",
         xp_value=500, respawn=20,
         stats={"str": 3, "dex": 3, "agi": 3, "per": 3, "con": 3})

    # Connect to wing — use a named direction with aliases
    _exit(wing, levelup, "northeast", ["levelup", "xp", "pinata", "ne"])
    _exit(levelup, wing, "southwest", ["back", "out", "sw"])

    # Also connect directly from hub for convenience
    _exit(hub, levelup, "northeast", ["levelup", "xp", "ne"])
    _exit(levelup, hub, "northwest", ["hub", "nw"])

    # ------------------------------------------------------------------
    # 15. CLASS & RACE TESTING — proficiency, race mods, milestones
    # ------------------------------------------------------------------
    classrace = _room(
        "|wClass & Race Testing|n",
        "A hall of mirrors reflecting different versions of yourself. "
        "Weapon racks line the walls with one of every type.\n\n"
        "|yTests:|n class proficiency warnings, race mods, score display, "
        "skills display, milestone effects\n"
        "|yInstructions:|n\n"
        "  1. |cscore|n — check your class, race, and combat stats\n"
        "  2. |cskills|n — see weapon skill summary\n"
        "  3. |cskills sword|n — see milestones for a category\n"
        "  4. |cwield test sword|n — proficient classes: no warning\n"
        "  5. |cwield test bow|n — check for unfamiliar/opposed warning\n"
        "  6. Try different weapons to see proficiency messages\n"
        "  7. Kill dummies in other rooms, then come back to check\n"
        "     skill progress and unlocked milestones\n\n"
        "|yClass Tiers:|n\n"
        "  |gProficient|n — no penalty (weapons your class knows)\n"
        "  |yUnfamiliar|n — -15 attack, -3 damage\n"
        "  |rOpposed|n    — -25 attack, -5 damage (e.g. monk + sword)\n\n"
        "|yRace Mods:|n flat attack bonus/penalty per weapon type\n"
        "  (e.g. elf: +5 bow, +2 sword, -3 club)",
        is_safe=True,
    )
    # One of every weapon category for testing proficiency warnings
    _weapon(classrace, "test sword", "1d6", category="sword")
    _weapon(classrace, "test dagger", "1d3+1", category="dagger")
    _weapon(classrace, "test axe", "1d8", category="axe")
    _weapon(classrace, "test club", "1d6", category="club")
    _weapon(classrace, "test staff", "1d4+1", category="staff", hands=2)
    _weapon(classrace, "test polearm", "1d8", category="polearm", hands=2)
    _weapon(classrace, "test bow", "1d6", category="bow", wtype="ranged", hands=2)
    _weapon(classrace, "test crossbow", "1d8", category="crossbow", wtype="ranged", hands=2)
    _weapon(classrace, "test shield", "1d2", category="shield", wtype="shield",
            slot="offhand", block_chance=15, armor_bonus=5)

    _exit(hub, classrace, "southeast", ["class", "race", "se"])
    _exit(classrace, hub, "northwest", ["hub", "back", "nw"])

    return hub


# -------------------------------------------------------------------------
# Teardown
# -------------------------------------------------------------------------

def teardown_test_dungeon(caller):
    """Delete all objects tagged as testdungeon."""
    tagged = ObjectDB.objects.filter(
        db_tags__db_key=_TAG, db_tags__db_category=_TAG_CATEGORY
    )
    count = tagged.count()
    if count == 0:
        caller.msg("|yNo test dungeon found.|n")
        return 0

    # Also clean up any scripts on tagged objects
    for obj in tagged:
        for script in obj.scripts.all():
            script.stop()
            script.delete()

    tagged.delete()
    caller.msg(f"|gDeleted {count} test dungeon objects.|n")
    return count


# -------------------------------------------------------------------------
# Command
# -------------------------------------------------------------------------

class CmdTestDungeon(Command):
    """
    Create or destroy an isolated test dungeon.

    Usage:
        @testdungeon            Build the dungeon and teleport there.
        @testdungeon/teardown   Destroy all test dungeon objects.

    The test dungeon is completely disconnected from the game world.
    It contains rooms testing: weapons, combat, equipment, shops,
    consumables, loot, flee/wimpy, rest, party combat, mob movement,
    weapon skills, and leveling.

    All objects are tagged for easy cleanup.
    """

    key = "@testdungeon"
    aliases = ["@td"]
    locks = "cmd:perm(Admin) or perm(Builder)"
    help_category = "Admin"

    def func(self):
        if "teardown" in self.switches:
            # Remember where they were before the dungeon
            saved = self.caller.attributes.get("_testdungeon_return")
            teardown_test_dungeon(self.caller)
            if saved:
                return_room = search_object(f"#{saved}")
                if return_room:
                    self.caller.move_to(return_room[0], quiet=True)
                    self.caller.msg("|gReturned to your previous location.|n")
                self.caller.attributes.remove("_testdungeon_return")
            return

        # Check if dungeon already exists
        existing = ObjectDB.objects.filter(
            db_tags__db_key=_TAG, db_tags__db_category=_TAG_CATEGORY
        ).count()
        if existing > 0:
            self.caller.msg(
                f"|yA test dungeon already exists ({existing} objects). "
                f"Use |w@testdungeon/teardown|y first.|n"
            )
            return

        # Save current location for return
        if self.caller.location:
            self.caller.db._testdungeon_return = self.caller.location.id

        self.caller.msg("|cBuilding test dungeon...|n")
        hub = build_test_dungeon(self.caller)
        self.caller.move_to(hub, quiet=True)
        self.caller.msg(
            "\n|g=== Test Dungeon Created ===|n\n"
            f"|w15 rooms|n with mobs, weapons, armor, shops, and consumables.\n"
            "Everything is tagged — use |w@testdungeon/teardown|n to clean up.\n"
            "Type |wlook|n to see the hub directions.\n"
        )
