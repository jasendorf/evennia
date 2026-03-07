"""
batch_awtown_dialogue.py  —  DorfinMUD Phase 3
Populates NPC dialogue dicts and shop inventories.
Run with:  @batchcode world.batch_awtown_dialogue

Safe to re-run; overwrites dialogue/inventory on existing NPCs.
"""

# HEADER

import evennia

NPC_TAG = "awtown_npc"

def _npc(db_key):
    results = evennia.search_tag(db_key, category=NPC_TAG)
    return results[0] if results else None

def _set(db_key, dialogue=None, inventory=None):
    npc = _npc(db_key)
    if not npc:
        caller.msg(f"|r  Warning: NPC not found: {db_key}|n")
        return
    if dialogue is not None:
        npc.db.dialogue = dialogue
    if inventory is not None:
        npc.db.shop_inventory = inventory


# =============================================================================
# CODE — Gate & Guard NPCs
# =============================================================================

caller.msg("|y[batch_dialogue] Setting gate & guard NPC dialogue...|n")

_set("npc_vonn", dialogue={
    "hello":    "Welcome to Awtown. Keep your weapons sheathed inside the walls and we'll get along fine.",
    "help":     "New to Awtown? Head northeast to the Herald's Hall — Bramwick will sort you out.",
    "quest":    "Not my department. Talk to Herald Bramwick inside.",
    "job":      "Not my department. Talk to Herald Bramwick inside.",
    "danger":   "Awtown is safe. What's outside the walls is your own business.",
    "gate":     "The Grand Gate is open from dawn to dusk. After dark, knock twice.",
    "town":     "Founder's Walk runs east-west through the middle of town. Everything worth finding is off it.",
})

_set("npc_tessa", dialogue={
    "hello":    "Oh! Hi. Welcome to Awtown. It's a good town, mostly.",
    "rumour":   "I heard something moved in the Old Graves last night. Enid says it's nothing. I'm not so sure.",
    "help":     "I'm on duty, but Herald Bramwick inside the Hall will help you more than I can.",
    "guard":    "Captain Vonn runs a tight gate. I'm still learning the ropes.",
    "night":    "The Garden's a bit strange after dark. Nothing dangerous in town, though — probably.",
})

_set("npc_crabb", dialogue={
    "hello":    "I know your face now. Don't give me a reason to remember it.",
    "help":     "Keep moving. The stables are north if you need to board a mount.",
    "stable":   "North through the gate. Oswin runs a good yard.",
    "town":     "You want Founder's Walk. East from here.",
})

_set("npc_birch", dialogue={
    "hello":    "Oh — sorry, I was reading. Welcome to Awtown's south gate.",
    "book":     "It's about the founding of Dorfin. Fascinating, actually. Did you know the three Founders nearly called it something else entirely?",
    "garden":   "The Garden of Remembrance is just south. Beautiful place. A bit eerie at night, but beautiful.",
    "help":     "I'm gate staff, not a guide — but the Herald's Hall is your best bet for getting oriented.",
    "lore":     "Ask me about the founding, the Founders, or the garden. I've been reading up.",
    "founding": "Awtown was established about a hundred and forty years ago. The Founders — Malgrave, Hammerfall, and Ondrel — each contributed something essential. Malgrave the diplomacy, Hammerfall the walls, Ondrel the records.",
})


# =============================================================================
# Herald's Hall, Outfitter's Rest, Vault
# =============================================================================

caller.msg("|y[batch_dialogue] Setting hub NPC dialogue...|n")

_set("npc_bramwick", dialogue={
    "hello":    "Welcome to Awtown! I'm Herald Bramwick — if you need anything, anything at all, I'm your man. Town map? Right here. Quest board? On your left. First time? Let me give you the tour.",
    "help":     "You've come to the right place. Check the Quest Board on the wall for available work. Talk to the Founders on Founder's Walk for buffs before you head out. The Outfitter's Rest south of here has a free starter kit for new arrivals.",
    "quest":    "The Quest Board has everything we've got posted. First-timers: look for the 'First Adventure' notices — good starting work, safe, pays decently.",
    "map":      "I'll get you a map! One moment — Scribe Dilly, a map for our friend here, please.",
    "founder":  "The three Founders have offices on Founder's Walk. Malgrave's Parlour, Hammerfall's Workshop, and Ondrel's Study. Visit all three before you head out — their buffs stack.",
    "buff":     "Visit the Founders on Founder's Walk. Each one has a daily blessing. Type 'buff' when you're in their office.",
    "kit":      "The Outfitter's Rest is just south through the Gilded Passage. Tell Marta you're new — type 'claim' and she'll sort you out.",
    "job":      "The Quest Board on the wall has everything. First-timers should look at the 'First Adventure' postings.",
    "town":     "Founder's Walk runs east-west through the north of town. The Temple's in the centre, the Inn just south of it. The Grand Forge is south. You'll find everything eventually.",
})

_set("npc_dilly", dialogue={
    "hello":    "Hello! Map? Guild registration form? I have both ready.",
    "map":      "Here's a town map. It covers all of Awtown's roads and major buildings.",
    "guild":    "Guild registration requires a minimum of three members and a charter fee of 200 copper. Speak to Registrar Brom at the Round Table when you're ready.",
    "help":     "Herald Bramwick handles the quests. I handle the paperwork. What do you need?",
})

_set("npc_marta", dialogue={
    "hello":    "Oh, come in, come in! New to Awtown? You look like you could use a decent set of clothes and maybe a torch or three.",
    "kit":      "Type 'claim' and I'll get you sorted! Every new adventurer gets a starter kit — free of charge. Jorvyn's standing order.",
    "claim":    "Type 'claim' to receive your kit, dear.",
    "help":     "I sell basic supplies — torches, rations, rope, that sort of thing. If you haven't claimed your starter kit yet, type 'claim'.",
    "buy":      "Have a look at my stock — type 'list' to see what I've got. Or type 'claim' if you're a new arrival.",
    "torch":    "Always keep at least two. Type 'list' to see what I have in stock.",
    "food":     "A hunk of bread and a full waterskin. That's all you need. Type 'list' to see my stock.",
},
inventory=[
    {"key": None, "name": "Torch",          "price": 3,  "desc": "A wax-soaked torch. Burns for about an hour."},
    {"key": None, "name": "Waterskin",      "price": 8,  "desc": "An empty leather waterskin."},
    {"key": None, "name": "Hunk of Bread",  "price": 2,  "desc": "Dense and filling. Travels well."},
    {"key": None, "name": "Hemp Rope",      "price": 10, "desc": "Thirty feet of strong hemp rope."},
    {"key": None, "name": "Tinderbox",      "price": 5,  "desc": "Flint, steel, and tinder. Lights fires reliably."},
    {"key": None, "name": "Belt Pouch",     "price": 8,  "desc": "A small leather pouch for coins and small items."},
    {"key": None, "name": "Simple Tunic",   "price": 12, "desc": "A plain but sturdy linen tunic."},
    {"key": None, "name": "Travelling Cloak","price": 20,"desc": "A weatherproof wool cloak with a deep hood."},
])

_set("npc_guildred", dialogue={
    "hello":    "Account number? No account? Step to the side and fill out form G-7. I'll be with you in 0.3 minutes.",
    "bank":     "Deposits, withdrawals, exchange, and safe deposit boxes. Standard fee of 1% on withdrawals above 500 copper. Quite reasonable.",
    "deposit":  "Deposits are processed immediately. No fee. Funds are secured in our vault — Holt sees to that.",
    "withdraw": "Withdrawals above 500 copper carry a 1% processing fee. Below that, no charge. Quite reasonable.",
    "help":     "I handle banking. Holt handles everything else.",
    "exchange": "We exchange gold, silver, and copper at standard Dorfin rates: 100 copper to the silver, 100 silver to the gold.",
    "loan":     "Loans are available to established account holders. 12% per month, compounded. Read form L-3 carefully.",
})

_set("npc_holt", dialogue={
    "hello":    "...",
    "help":     "...",
    "bank":     "Ask Guildred.",
})


# =============================================================================
# Founders
# =============================================================================

caller.msg("|y[batch_dialogue] Setting Founder dialogue...|n")

_set("npc_malgrave", dialogue={
    "hello":    "Ah! Perfect timing. I was just thinking about someone like you. Heading out? Let me give you something to take with you. Type 'buff' to receive Malgrave's Rally.",
    "buff":     "Type 'buff' and I'll give you Malgrave's Rally. Good for persuasion, leadership, keeping your party's spirits up.",
    "blessing": "Type 'buff' — that's the word. Go on.",
    "rally":    "Malgrave's Rally boosts your Persuasion and Leadership for an hour. Type 'buff' to receive it.",
    "help":     "I coordinate the town. If something's wrong, I want to hear about it. If you need a boost before heading out, type 'buff'.",
    "town":     "Awtown runs well because everyone does their part. Hammerfall built the walls, Ondrel keeps the records, I keep the people talking to each other.",
    "founder":  "Three of us founded this place. Hammerfall's office is east of here, Ondrel's is a bit further. Visit all three — our blessings stack.",
})

_set("npc_hammerfall", dialogue={
    "hello":    "[doesn't look up] 'Your gear's got some gaps. Hold still.' [tightens something] 'Better. Type buff if you want Hammerfall's Blessing before you go.'",
    "buff":     "Type 'buff'. Hammerfall's Blessing. Weapon damage and armour. One hour. Come back tomorrow.",
    "blessing": "Type 'buff'.",
    "forge":    "The Grand Forge is south of Founder's Walk. Brondal runs the iron work. Tell him I sent you — he won't care, but tell him anyway.",
    "help":     "I build things and I break things. If a wall needs fixing or something needs making, I'm here. For buffs, type 'buff'.",
    "founder":  "Malgrave talks, Ondrel writes it down, I make sure the walls hold. That's how this works.",
})

_set("npc_ondrel", dialogue={
    "hello":    "Oh — yes — I've been reading about the region you're probably heading to. Fascinating history. The short version: don't touch the old stones. The long version is forty pages. I've summarised it. Type 'buff' when you're ready for Ondrel's Insight.",
    "buff":     "Ondrel's Insight. XP gain and Lore checks, for one hour. Type 'buff' to receive it. Pay attention out there — knowledge compounds.",
    "blessing": "Type 'buff', dear.",
    "insight":  "Ondrel's Insight sharpens your mind for an hour — you'll learn faster and notice more. Type 'buff'.",
    "lore":     "The Crystal Repository has deeper lore stored. Archivist Quellan can help you access it. But for general knowledge, ask me anything.",
    "history":  "Awtown was founded approximately 140 years ago. The founding document is in the Deed Hall. I've cross-referenced it with four other sources. Registrar Voss has the original.",
    "help":     "I keep the records. If you need to know something about this region's history, ask me. For the buff, type 'buff'.",
})


# =============================================================================
# Temple NPCs
# =============================================================================

caller.msg("|y[batch_dialogue] Setting Temple dialogue...|n")

_set("npc_edwyn_lux", dialogue={
    "hello":    "Welcome to the Temple of the Eternal Flame. All are welcome here. What brings you to us?",
    "help":     "The Sanctuary to the east offers healing. Brother Aldwin in the Vestry trains Clerics. Thane Dusk at the Bell Tower trains Paladins. I offer blessings and resurrection services.",
    "heal":     "Sister Sera handles day-to-day healing in the Sanctuary. For more serious restoration, speak to me.",
    "resurrect":"Resurrection is possible, but costly — 500 copper for the service. The Flame remembers those it has touched.",
    "blessing": "A minor blessing costs 20 copper and provides protection for an hour. A greater blessing is 100 copper.",
    "cleric":   "Brother Aldwin handles Cleric training in the Vestry. He is demanding but thorough.",
    "paladin":  "Thane Dusk is at the Bell Tower. He'll evaluate your commitment before he agrees to teach.",
    "flame":    "The Eternal Flame has burned here for as long as Awtown has stood. No one has ever seen it go out.",
},
inventory=[
    {"key": None, "name": "Minor Blessing Scroll", "price": 20,  "desc": "A scroll bearing a minor protective prayer. Provides a small defensive bonus for one hour."},
    {"key": None, "name": "Greater Blessing Scroll","price": 100, "desc": "A scroll bearing a powerful prayer. Significant defensive and restorative bonus for one hour."},
    {"key": None, "name": "Healing Potion",         "price": 50,  "desc": "A vial of temple-blessed restorative draught. Restores a moderate amount of health."},
])

_set("npc_sister_sera", dialogue={
    "hello":    "Oh, hello! Are you hurt? Even a little? I've been practising. Mostly successfully.",
    "help":     "I can patch you up for a small donation to the Temple. I'm still learning a few of the more advanced spells, but the basics I have down. Mostly.",
    "heal":     "I can heal you for 15 copper donation. Type 'buy healing' to receive treatment.",
    "cleric":   "Brother Aldwin is in the Vestry if you want to train as a Cleric. He's very serious. I find that intimidating. You might not.",
    "flame":    "I've been here three years and I still find the Eternal Flame beautiful every morning.",
},
inventory=[
    {"key": None, "name": "Minor Healing",  "price": 15, "desc": "Sister Sera tends your wounds carefully. Restores a small amount of health."},
    {"key": None, "name": "Healing Potion", "price": 40, "desc": "A blessed healing draught prepared in the Sanctuary."},
])

_set("npc_aldwin", dialogue={
    "hello":    "This is the Vestry. If you are here to train as a Cleric, demonstrate your commitment first. If you are here out of curiosity, the Nave is through the door.",
    "train":    "Cleric training is available to those who demonstrate genuine faith and purpose. What draws you to the cloth?",
    "cleric":   "Clerics serve through healing, protection, and knowledge. It is not a path for those seeking power alone.",
    "help":     "I train Clerics. If that is what you seek, ask me to train you and be prepared to answer for your motivations.",
})

_set("npc_thane_dusk", dialogue={
    "hello":    "You've climbed to the Bell Tower. That's something. What do you want?",
    "train":    "Paladin training is not something I offer casually. Come back when you've done something worth recognising.",
    "paladin":  "A Paladin serves something greater than themselves. Show me you understand that and we'll talk about training.",
    "help":     "I train Paladins. The standard is high. The bell tower has good acoustics for thinking about whether you're ready.",
    "bell":     "It rings at dawn and dusk. I've been here for both, most days, for eleven years.",
})


# =============================================================================
# Inn, Forge, Crafters
# =============================================================================

caller.msg("|y[batch_dialogue] Setting Inn, Forge, crafter dialogue...|n")

_set("npc_bess", dialogue={
    "hello":    "Welcome to the Hearthstone. I'm Bess. Sit anywhere, Finn will see you right. Need a room, come find me at the counter.",
    "room":     "A room is 20 copper a night. You get a key, a real bed, and breakfast if you're up before ninth bell. Come to the Inn Counter and type 'rent room'.",
    "rent":     "Go to the Inn Counter to the south and type 'rent room'. 20 copper a night.",
    "food":     "Finn handles drinks and bar food. Cook Darra runs the kitchen — we do a full hot meal at sixth and twelfth bell.",
    "rumour":   "Heard something odd earlier. A traveller came in from the north road saying he'd seen lights in the hills. Doesn't mean anything, probably. Probably.",
    "help":     "Food, drink, and a bed — that's what we offer. Finn at the bar for drinks; me at the counter for rooms.",
    "gossip":   "Something's been moving in the Old Graves at night. Enid says it's the wind. The wind doesn't leave footprints.",
})

_set("npc_finn", dialogue={
    "hello":    "What'll it be?",
    "drink":    "Ale, wine, or something stronger? Type 'list' to see the board.",
    "rumour":   "Had a merchant in last week who wouldn't say what he was carrying. Paid in gold too. Nobody pays in gold for a room and a meal.",
    "help":     "I pour drinks and hear things. Both free of charge. Well, the drinks aren't free.",
    "job":      "Not my territory — Herald Bramwick at the hall handles official work. Sal at the Posting Board handles the unofficial kind.",
},
inventory=[
    {"key": None, "name": "Pint of Ale",     "price": 3,  "desc": "A pint of Hearthstone house ale. Reliably decent."},
    {"key": None, "name": "Cup of Wine",     "price": 6,  "desc": "A cup of rough red wine. Better than it sounds."},
    {"key": None, "name": "Spirits",         "price": 10, "desc": "A measure of something strong and unspecified. Effective."},
    {"key": None, "name": "Bowl of Stew",    "price": 8,  "desc": "Hot stew from Darra's kitchen. Changes daily. Always good."},
    {"key": None, "name": "Hunk of Bread",   "price": 2,  "desc": "Dense bread from the kitchen. Good for mopping up stew."},
])

_set("npc_cobble", dialogue={
    "hello":    "Ah, a new face! I'm Cobble. I play every night. Requests are theoretically welcome.",
    "song":     "I take requests, though I reserve the right to play something better instead.",
    "music":    "I've been playing the Hearthstone for three seasons now. Bess tolerates me. I consider that a ringing endorsement.",
    "help":     "I play music. I don't do quests. I barely do requests.",
})

_set("npc_darra", dialogue={
    "hello":    "Get out of my kitchen.",
    "food":     "Get out of my kitchen.",
    "help":     "GET OUT OF MY KITCHEN.",
    "please":   "...The stew is at sixth bell. Now get out.",
})

_set("npc_brondal", dialogue={
    "hello":    "[looks up from the anvil, assesses you in two seconds, goes back to work] 'What do you need?'",
    "train":    "Smithing training is available. It's not fast, it's not easy, and I don't repeat myself. Understood?",
    "weapon":   "I make weapons. I also repair them. Type 'list' for current stock. Quality costs what it costs.",
    "armour":   "Armour's available. What kind of work do you do? Matters for the fit.",
    "help":     "Weapons, armour, repair. That's the Iron Forge. Type 'list' for stock.",
},
inventory=[
    {"key": None, "name": "Short Sword",    "price": 80,  "desc": "A well-balanced short sword. Good for a first blade."},
    {"key": None, "name": "Hand Axe",       "price": 60,  "desc": "A sturdy hand axe. Reliable in close quarters."},
    {"key": None, "name": "Iron Dagger",    "price": 30,  "desc": "A plain iron dagger. Light and practical."},
    {"key": None, "name": "Leather Armour", "price": 120, "desc": "A set of boiled leather armour. Good starter protection."},
    {"key": None, "name": "Iron Shield",    "price": 90,  "desc": "A round iron shield. Heavier than wood, worth it."},
    {"key": None, "name": "Weapon Repair",  "price": 20,  "desc": "Brondal examines and repairs a damaged weapon."},
])

_set("npc_wynn", dialogue={
    "hello":    "Come in, come in! I'm just finishing a bow — well, starting it, really. The wood needs another day. Are you after something specific?",
    "train":    "Carpentry and leatherwork — I teach both. Come back when you have some time to commit.",
    "bow":      "A good bow takes three days minimum. I don't rush the wood. Type 'list' for what's ready now.",
    "help":     "Bows, shields, wooden gear, leather work. Type 'list' for current stock.",
},
inventory=[
    {"key": None, "name": "Shortbow",       "price": 70,  "desc": "A well-made shortbow. Accurate at medium range."},
    {"key": None, "name": "Quiver of Arrows","price": 15, "desc": "Twenty standard arrows. Good fletching, iron tips."},
    {"key": None, "name": "Wooden Shield",  "price": 40,  "desc": "A sturdy wooden shield with an iron boss."},
    {"key": None, "name": "Leather Satchel","price": 25,  "desc": "A roomy leather satchel with multiple pockets."},
])

_set("npc_mira", dialogue={
    "hello":    "Yes? I'm in the middle of a count. What do you need?",
    "train":    "Tailoring requires patience and precision. I can teach it to those who have both.",
    "cloak":    "I make the finest cloaks in Dorfin. That is not arrogance; it is a documented fact. Type 'list'.",
    "help":     "Clothing and cloth goods. Type 'list'.",
},
inventory=[
    {"key": None, "name": "Fine Cloak",     "price": 80,  "desc": "A beautifully made wool cloak. Warm, weatherproof, and quietly impressive."},
    {"key": None, "name": "Linen Shirt",    "price": 18,  "desc": "A well-made linen shirt. Comfortable for travel."},
    {"key": None, "name": "Wool Trousers",  "price": 22,  "desc": "Sturdy wool trousers. Good for cold weather."},
    {"key": None, "name": "Leather Belt",   "price": 12,  "desc": "A simple but well-stitched leather belt."},
    {"key": None, "name": "Belt Pouch",     "price": 15,  "desc": "A well-made leather belt pouch."},
])

_set("npc_sable_dross", dialogue={
    "hello":    "Oh! Yes, hello, one moment — [something bubbles] — yes, there. Hello! Sable Dross, alchemist. You need something?",
    "train":    "Alchemy training! Yes! It's mostly memorisation, some trial and error, and occasionally fire. I can teach you.",
    "potion":   "I've got several in stock. Type 'list'. The ones with the orange label are fine, the blue label ones are mostly fine.",
    "help":     "Potions, reagents, alchemy training. Type 'list' for what I have today.",
},
inventory=[
    {"key": None, "name": "Healing Potion",     "price": 45,  "desc": "A properly brewed healing potion. Restores a moderate amount of health."},
    {"key": None, "name": "Antidote",            "price": 35,  "desc": "Neutralises most common poisons. Tastes dreadful."},
    {"key": None, "name": "Torch Oil",           "price": 8,   "desc": "Alchemical torch oil that burns twice as long as standard wax."},
    {"key": None, "name": "Reagent Bundle",      "price": 20,  "desc": "A bundle of common alchemical reagents for basic crafting."},
    {"key": None, "name": "Smoke Pellet",        "price": 15,  "desc": "Creates a dense cloud of smoke when thrown. Useful for escaping."},
])


# =============================================================================
# Services, Admin, Misc NPCs
# =============================================================================

caller.msg("|y[batch_dialogue] Setting service & admin NPC dialogue...|n")

_set("npc_cogsworth", dialogue={
    "hello":    "Tinker Cogsworth, at your service! Broken magical item? Strange device? Gadget that won't gadget? I can help, probably, most of the time!",
    "repair":   "I can repair most items for a fee. Magical items cost more — identification adds 30 copper. Type 'list' for services.",
    "identify": "Mysterious object? I'll tell you what it is for 30 copper. Results are accurate approximately 94% of the time.",
    "help":     "Repair, identification, tools, components. Type 'list'.",
    "marro":    "Known Marro for thirty years. Best engineer I've ever met. Second best, if I'm being honest with myself.",
},
inventory=[
    {"key": None, "name": "Item Repair",     "price": 25, "desc": "Cogsworth examines and repairs a damaged mundane item."},
    {"key": None, "name": "Item Identify",   "price": 30, "desc": "Cogsworth identifies the properties of a mysterious item."},
    {"key": None, "name": "Tinderbox",       "price": 6,  "desc": "A precision-made tinderbox. Lights reliably in wind."},
    {"key": None, "name": "Tool Kit",        "price": 40, "desc": "A basic set of mechanical tools."},
    {"key": None, "name": "Candle (x5)",     "price": 4,  "desc": "Five tallow candles. Burn for about two hours each."},
])

_set("npc_fenn", dialogue={
    "hello":    "Cogwright Fenn. You need mechanical parts, gadgets, or Tinkerer training?",
    "train":    "Tinkerer training — yes. It takes patience and a willingness to rebuild the same mechanism six times before it works.",
    "gadget":   "I have several prototype gadgets in stock. Some work better than others. The descriptions are accurate.",
    "help":     "Mechanical components, gadgets, Tinkerer training. Type 'list'.",
},
inventory=[
    {"key": None, "name": "Gear Set",        "price": 12, "desc": "A set of precision brass gears. Basic crafting component."},
    {"key": None, "name": "Spring Coil",     "price": 8,  "desc": "A coiled steel spring. Useful for traps and mechanisms."},
    {"key": None, "name": "Smoke Canister",  "price": 18, "desc": "A mechanical smoke canister. Pull the ring to deploy."},
    {"key": None, "name": "Grapple Hook",    "price": 55, "desc": "A folding grapple hook with 40 feet of wire cord."},
    {"key": None, "name": "Mechanical Lock", "price": 35, "desc": "A sturdy mechanical padlock. Requires the paired key."},
])

_set("npc_izra", dialogue={
    "hello":    "Mapper Izra. You're standing in my workspace. Don't move the maps on the table.",
    "map":      "I sell regional maps that reveal portions of the world map. Type 'list' to see what's available.",
    "explore":  "If you've been somewhere unmapped, I'll pay for accurate information. Come back with notes and I'll assess them.",
    "train":    "Cartography and Navigation. I teach both. Prerequisite: you need to be able to read.",
    "help":     "Maps for sale, exploration data purchased, cartography training. Type 'list'.",
},
inventory=[
    {"key": None, "name": "Town Map of Awtown",     "price": 5,  "desc": "A detailed map of Awtown's streets and buildings."},
    {"key": None, "name": "Regional Map: South Road","price": 40, "desc": "A map covering the southern road from Awtown. Partially filled in."},
    {"key": None, "name": "Blank Parchment",         "price": 3,  "desc": "A sheet of blank parchment for mapping or notes."},
    {"key": None, "name": "Charcoal Stick",          "price": 1,  "desc": "A stick of charcoal for marking maps and leaving trail signs."},
    {"key": None, "name": "Compass",                 "price": 30, "desc": "A reliable brass compass. Points north consistently."},
])

_set("npc_teris", dialogue={
    "hello":    "Watchman Teris. Something moves south of the wall today — I've had an eye on it. What do you need?",
    "watch":    "I keep the approaches under observation. If I post a sighting quest on the board, it's worth checking out.",
    "ranger":   "I carry basic ranger supplies. Type 'list'.",
    "sighting": "Something in the hills, two days south. Might be nothing. Probably isn't nothing.",
    "help":     "Scouting quests and ranger supplies. Type 'list'.",
},
inventory=[
    {"key": None, "name": "Arrow Bundle",   "price": 12, "desc": "Twenty standard hunting arrows."},
    {"key": None, "name": "Trail Rations",  "price": 10, "desc": "Three days of dried trail rations. Dense and unexciting."},
    {"key": None, "name": "Hempen Rope",    "price": 10, "desc": "Thirty feet of strong hemp rope."},
    {"key": None, "name": "Signal Whistle", "price": 8,  "desc": "A sharp brass whistle audible at long range."},
])

_set("npc_morvaine", dialogue={
    "hello":    "You smell like a town. That's not a complaint, exactly. What do you want?",
    "herb":     "I know every plant in Dorfin by name and by what it'll do to you. Train with me or buy from me — both available.",
    "train":    "Herbalism training. You'll need to go out and gather. I'll tell you what to look for.",
    "help":     "Herbalism training, rare reagents, foraging tools. Type 'list'.",
    "garden":   "The Willow Grove in the garden has some useful specimens. Enid lets me forage there in exchange for keeping the weeds down.",
},
inventory=[
    {"key": None, "name": "Dried Healing Herbs", "price": 15, "desc": "A bundle of dried medicinal herbs. Useful in basic healing poultices."},
    {"key": None, "name": "Antitoxin Root",       "price": 25, "desc": "A rare root that neutralises mild poisons when chewed."},
    {"key": None, "name": "Foraging Satchel",     "price": 20, "desc": "A cloth satchel with compartments for herb gathering."},
    {"key": None, "name": "Herb Pouch",           "price": 8,  "desc": "A small pouch for carrying gathered herbs without crushing them."},
])

_set("npc_orvyn", dialogue={
    "hello":    "Evening. Or morning. Depends when you've caught me. I walk the streets at night keeping the lanterns burning. Forty years of it.",
    "lantern":  "Every lantern in Awtown is my responsibility. I know each one. The one on the corner of Warden's Way has been burning crooked for a week — I'm getting to it.",
    "help":     "I sell candles, torches, and lamp oil. Type 'list'. And if you hear about anything happening on the streets at night, tell me.",
    "quest":    "I do have a job, actually. There's a storm coming and I'll need help keeping the lanterns lit. Come back when the sky darkens.",
    "storm":    "The wind's picking up. If the lanterns go out during a storm, the town goes dark. Last time that happened... well. Come find me if you want to help.",
    "rumour":   "I walk every street in this town before dawn. I see things. The thing by the south wall last week wasn't a cat.",
},
inventory=[
    {"key": None, "name": "Torch",        "price": 3,  "desc": "A standard wax-soaked torch. Burns for about an hour."},
    {"key": None, "name": "Candle",       "price": 1,  "desc": "A tallow candle. Soft light, burns two hours."},
    {"key": None, "name": "Lamp Oil",     "price": 5,  "desc": "A small flask of clean lamp oil."},
    {"key": None, "name": "Tinderbox",    "price": 5,  "desc": "Reliable fire-starting kit."},
    {"key": None, "name": "Dark Lantern", "price": 45, "desc": "A hooded lantern that can be shuttered for a directional beam of light."},
])

_set("npc_dorn", dialogue={
    "hello":    "Sergeant Dorn. You look like you want something. Make it quick.",
    "train":    "Warrior and Knight training. I run drills. It's not pleasant. It's effective. Interested?",
    "help":     "Combat training and basic weapons. Type 'list'.",
    "guard":    "The guard keeps Awtown safe. We don't run quests — check the Warden's Barracks board for bounties.",
    "bounty":   "There's a board on the wall. Current bounties posted. Come back when you've done something worth reporting.",
},
inventory=[
    {"key": None, "name": "Guard Issue Sword",  "price": 55, "desc": "Standard-issue guard sword. Reliable, if unlovely."},
    {"key": None, "name": "Guard Issue Shield", "price": 45, "desc": "A plain iron shield stamped with the Awtown crest."},
    {"key": None, "name": "Leather Gloves",     "price": 10, "desc": "Heavy leather gloves for combat. Protects the hands."},
])

_set("npc_harwick", dialogue={
    "hello":    "Harwick. I handle the bounty board. What do you need?",
    "bounty":   "Check the board on the wall. Current wanted notices are posted. Bring back proof of completion.",
    "help":     "Bounty board and basic weapons. Type 'list'.",
    "dorn":     "Sergeant Dorn is at the Warden's Barracks if you want combat training. I'm the paperwork side of things.",
},
inventory=[
    {"key": None, "name": "Short Sword",   "price": 50, "desc": "A plain but serviceable short sword."},
    {"key": None, "name": "Iron Dagger",   "price": 25, "desc": "Standard issue iron dagger. Functional."},
    {"key": None, "name": "Torch",         "price": 3,  "desc": "A standard wax torch."},
])

# Remaining NPCs — minimal but functional dialogue
_set("npc_pell", dialogue={
    "hello":    "Steward Pell. I manage Awtown's logistics. If you're looking for work, I have delivery jobs available.",
    "job":      "Supply runs and deliveries. Nothing glamorous but pays reliably. Come back when you need work.",
    "help":     "Town logistics and delivery quests. Ask me about jobs.",
    "town":     "Everything runs on schedule because I make it run on schedule. That's all.",
})

_set("npc_quellan", dialogue={
    "hello":    "Hmm? Oh — a visitor. The crystals have been quiet today. What do you need?",
    "lore":     "The crystal formation stores historical records, bestiary entries, and regional knowledge. Ask me about a specific topic.",
    "help":     "Historical records, bestiary, knowledge scrolls. Type 'list' for what I sell.",
    "crystal":  "I don't know its origin. I've been studying it for seven years. It hums in a different register on cloudy days.",
},
inventory=[
    {"key": None, "name": "Lore Scroll: Dorfin History",  "price": 30, "desc": "A scroll detailing the founding and early history of the Land of Dorfin."},
    {"key": None, "name": "Lore Scroll: Common Monsters", "price": 25, "desc": "A bestiary scroll covering the most commonly encountered creatures in the region."},
    {"key": None, "name": "Blank Scroll",                 "price": 5,  "desc": "A blank scroll of archival-quality parchment."},
])

_set("npc_hobb", dialogue={
    "hello":    "Item number? If you don't have an item number, you need a form. Form QM-3.",
    "help":     "I supply the town. If you want something from this room, you need a manifest. Type 'list' for available items.",
    "bulk":     "Bulk orders require form QM-7 and three days' notice.",
},
inventory=[
    {"key": None, "name": "Trail Rations (x5)",  "price": 20, "desc": "Five days of dried rations. Dense, reliable, unexciting."},
    {"key": None, "name": "Hemp Rope",           "price": 10, "desc": "Thirty feet of heavy hemp rope."},
    {"key": None, "name": "Iron Spikes (x10)",   "price": 8,  "desc": "Ten iron pitons. Useful for climbing, securing ropes, and improvised door-stops."},
    {"key": None, "name": "Lantern",             "price": 15, "desc": "A simple tin lantern with a glass panel."},
])

_set("npc_oswin", dialogue={
    "hello":    "Oswin. I run the paddock. You boarding a mount or just looking?",
    "stable":   "Boarding is 5 copper a day. Mount is fed, watered, and exercised. Type 'list' for tack and equipment.",
    "horse":    "I've got working horses if you need one. They're not fast but they're solid. Come back when you have coin.",
    "help":     "Mount boarding and riding equipment. Type 'list'.",
},
inventory=[
    {"key": None, "name": "Saddle",          "price": 60, "desc": "A well-made leather saddle. Fits most standard mounts."},
    {"key": None, "name": "Saddle Bags",     "price": 35, "desc": "Paired leather saddlebags. Attaches to a saddle."},
    {"key": None, "name": "Bridle",          "price": 20, "desc": "A simple bridle and bit."},
    {"key": None, "name": "Mount Boarding",  "price": 5,  "desc": "One day of feed, water, and care for a stabled mount."},
])

_set("npc_tetch", dialogue={
    "hello":    "Wayfarer Tetch. Just passing through. Have been for a while.",
    "map":      "I've got secondhand maps — cheaper than Izra's, not quite as reliable. Good enough for most roads. Type 'list'.",
    "rumour":   "I travel a lot. I hear things. There's a merchant caravan three days east that hasn't arrived yet. Four days overdue.",
    "help":     "Maps, blank parchment, trail rations. Type 'list'.",
},
inventory=[
    {"key": None, "name": "Secondhand Region Map", "price": 15, "desc": "A used regional map. Mostly accurate. Some corrections in the margins."},
    {"key": None, "name": "Blank Parchment",       "price": 2,  "desc": "A sheet of blank parchment."},
    {"key": None, "name": "Charcoal Stick",        "price": 1,  "desc": "For marking maps and leaving trail signs."},
    {"key": None, "name": "Trail Rations",         "price": 9,  "desc": "Two days of basic trail rations."},
])

_set("npc_acolyte_ren", dialogue={
    "hello":    "Oh! Welcome to the Shrine of First Light. I'm Acolyte Ren. I keep the candles lit and accept offerings.",
    "offering": "An offering to the Shrine brings a small blessing. Even a few copper means something.",
    "blessing": "I sell minor blessing scrolls — cheaper than the Temple proper, slightly weaker. Type 'list'.",
    "help":     "Minor blessings and candles. Type 'list'. And if you're heading into the Temple, this is a good place to stop first.",
},
inventory=[
    {"key": None, "name": "Minor Blessing Scroll", "price": 10, "desc": "A simple prayer scroll. Provides a very minor protective benefit for thirty minutes."},
    {"key": None, "name": "Prayer Candle",         "price": 2,  "desc": "A candle blessed at the Shrine. Burns with a steady, calming light."},
])

_set("npc_dunt", dialogue={
    "hello":    "Assayer Dunt. What needs valuing?",
    "appraise": "I appraise items at 15 copper per assessment. The valuation is accurate. I don't inflate and I don't deflate.",
    "buy":      "I purchase raw materials, gems, and ore at fair market value. Type 'list' to see what I'm currently buying.",
    "help":     "Appraisal and raw material purchase. Type 'list'.",
},
inventory=[
    {"key": None, "name": "Item Appraisal", "price": 15, "desc": "Dunt examines your item and gives you an accurate valuation."},
])

_set("npc_aldric_voss", dialogue={
    "hello":    "Ah. You found this place. That's telling.",
    "help":     "I offer perspective. Ask me about what troubles you, where you're headed, or what you've found.",
    "hint":     "Every door has a key. Every lock has a story. The trick is knowing which you need.",
    "quest":    "I give quests occasionally. When I have one for you, you'll know.",
    "hollow":   "I came here forty years ago to think for a week. I'm still thinking.",
    "advice":   "The Garden at night is worth visiting once, carefully. The Precipice at dawn is worth visiting often.",
})

_set("npc_enid", dialogue={
    "hello":    "Good day. I'm Groundskeeper Enid. Every stone in this garden is my responsibility. Is there something you needed?",
    "grave":    "I know every inscription in this garden. Ask me about any of them.",
    "history":  "The oldest grave here dates to the founding. It's not marked with a name — just a symbol. I've been trying to identify it for twenty years.",
    "night":    "I don't come here after dark any more. The groundskeeper before me did. She stopped talking about what she'd seen and never explained why.",
    "help":     "I know the garden's history and the people buried here. Ask me about anything you've noticed.",
})

_set("npc_sal", dialogue={
    "hello":    "Sal. If you've got work to post or work to take, you're in the right place.",
    "post":     "Two copper to post a notice. It stays up until the job's done or the paper falls off.",
    "job":      "Look at the board. Take what you can handle. Come back when it's done.",
    "help":     "Job postings and bounties. I don't judge what goes up here. Within reason.",
})

_set("npc_sybil", dialogue={
    "hello":    "Oh — sorry — I'm in the middle of three things. What do you need?",
    "deliver":  "I have documents that need delivering around town. Simple work, pays 10-20 copper per run.",
    "help":     "Delivery quests. I have too much paper and not enough runners.",
    "filing":   "Everything in here is filed in a system. I created the system. I understand the system. Nobody else does.",
})

_set("npc_wren", dialogue={
    "hello":    "Postmaster Wren. Quick, what do you need?",
    "deliver":  "I have urgent courier runs available. Time-sensitive, pays better than regular deliveries.",
    "mail":     "Player mail system coming soon. For now, I have courier quests.",
    "help":     "Courier quests and message delivery. Fast and well-paid.",
})

_set("npc_bevin", dialogue={
    "hello":    "Hello. I'm Scholar Bevin. This is the Study Hall. It's quieter than the Apprentice Hall if you need to learn something.",
    "train":    "I offer Lore and Languages training here. Cheaper than the Crystal Repository, slower. Effective.",
    "lore":     "Lore skill training available. Ask me about languages too — I speak six.",
    "help":     "Lore and Languages training. Quieter and cheaper than the alternatives.",
})

_set("npc_orifel", dialogue={
    "hello":    "Headmaster Orifel. New arrival? Find a seat. We'll get to you.",
    "train":    "Basic skills for all starting classes. What do you want to learn?",
    "class":    "I cover the basics. Specialised training is at the Grand Forge, the Temple, or the Barracks.",
    "quest":    "The 'First Adventure' quest chain starts here. Talk to me when you're ready to begin.",
    "help":     "Basic skill training and the First Adventure quest chain. Talk to me.",
})

caller.msg("|g[batch_dialogue] All NPC dialogue and shop inventories set. Phase 3 complete.|n")

