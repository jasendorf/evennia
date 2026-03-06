"""
DorfinMUD — Awtown World Builder
=================================
Run with:  @batchcode world.batch_awtown

Builds the entire Awtown hub town from scratch. Uses the custom room
typeclasses from typeclasses/rooms.py so every room is born with the
correct attribute defaults for its type.

After running, copy the printed START_LOCATION and DEFAULT_HOME dbrefs
into your settings.py ConfigMap:
    START_LOCATION = "#<dbref>"
    DEFAULT_HOME   = "#<dbref>"
"""

# ---------------------------------------------------------------------------
#HEADER
# ---------------------------------------------------------------------------

from evennia import create_object
from evennia.utils import logger
from typeclasses.rooms import (
    Room,
    RoadRoom,
    GateRoom,
    ExteriorRoom,
    CourtyardRoom,
    InnRoom,
    TempleRoom,
    CraftingRoom,
    TrainingRoom,
    FounderRoom,
    LookoutRoom,
)
from typeclasses.exits import Exit

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def room(typeclass, key, desc, zone="awtown", **kwargs):
    """
    Create a room of the given typeclass with a description and zone.
    Any extra kwargs are set as db attributes after creation.
    Returns the room object.
    """
    r = create_object(typeclass, key=key)
    r.db.desc = desc
    r.db.zone = zone
    for attr, val in kwargs.items():
        setattr(r.db, attr, val)
    caller.msg(f"|g  Created:|n {key} [{typeclass.__name__}] {r.dbref}")
    return r


def link(room_a, exit_ab, room_b, exit_ba):
    """Two-way exit between room_a and room_b."""
    create_object(Exit, key=exit_ab, location=room_a, destination=room_b)
    create_object(Exit, key=exit_ba, location=room_b, destination=room_a)


def one_way(from_room, exit_name, to_room):
    """One-way exit."""
    create_object(Exit, key=exit_name, location=from_room, destination=to_room)


W = {}   # world dict — W["key"] = room object

caller.msg("|y" + "="*60 + "|n")
caller.msg("|wDorfinMUD — Building Awtown|n")
caller.msg("|y" + "="*60 + "|n")


# ===========================================================================
#CODE
# --- BLOCK 1 — Eastern Commons (New Player Landing Zone) ---
# ===========================================================================
caller.msg("\n|c--- Exterior: Eastern Commons ---|n")

W["eastern_commons"] = room(
    ExteriorRoom,
    "The Eastern Commons",
    """|yA broad open commons stretches before the mighty gates of Awtown.|n

Travelers of every stripe mill about — weary adventurers, hopeful merchants,
and wide-eyed newcomers clutching their packs. Lanterns on tall poles mark
the edge of the road. To the |wwest|n, the |wGrand Gate|n of Awtown stands
open, its carved archway reading: |w"Leave lesser than you arrived."|n

|c[New arrivals: head west through the Grand Gate to enter the town.]|n
""",
)

W["wayfarers_green"] = room(
    ExteriorRoom,
    "The Wayfarers' Green",
    """|gA patch of worn but welcoming grass spreads beneath a broad oak tree.|n

Travelers rest here before or after the long road. Bedrolls, campfires, and
quietly murmured conversations fill the space. A weathered sign reads:
|w"Rest your feet. The road will wait."|n
""",
    ambient=[
        "A group of travelers huddles around a small fire, speaking quietly.",
        "Someone nearby is sharpening a blade with slow, rhythmic strokes.",
        "A child darts between the resting travelers, chasing something small.",
    ]
)

W["cart_market"] = room(
    ExteriorRoom,
    "The Cart Market",
    """|yA row of wooden carts and canvas stalls lines the eastern edge of the commons.|n

Traveling merchants hawk goods of dubious provenance — everything from
tarnished blades to suspiciously fragrant spices. The inventory changes with
the wind and the seller's mood. Trader Moss watches you with a merchant's
appraising eye.
""",
    ambient=[
        "A merchant shouts something about a 'once in a lifetime' price.",
        "The smell of spiced sausage drifts from somewhere nearby.",
    ]
)

W["notice_board"] = room(
    ExteriorRoom,
    "The Crossroads Notice Board",
    """|wA massive oak board, weathered but sturdy, stands at the crossroads.|n

Layers of parchment, nailed notices, and hand-scrawled rumors cover every
inch. Wanted posters flutter at the edges. Recent additions are pinned over
older ones, telling the layered history of the road in paper and ink.
""",
    ambient=[
        "Someone reads a notice, mouths moving, then tears it down and pockets it.",
    ]
)

W["toll_stone"] = room(
    ExteriorRoom,
    "The Toll Stone",
    """|wA crumbling stone pillar marks the old boundary of Awtown.|n

The founding date of Dorfin is carved deep into its face, worn smooth by
years of passing hands. Tollkeeper Renwick leans against it with the
patience of a man who has seen absolutely everything and is surprised by
none of it.
""",
)

link(W["eastern_commons"], "northwest", W["wayfarers_green"],  "southeast")
link(W["eastern_commons"], "northeast", W["cart_market"],      "southwest")
link(W["eastern_commons"], "southwest", W["notice_board"],     "northeast")
link(W["eastern_commons"], "southeast", W["toll_stone"],       "northwest")


# ===========================================================================
# --- BLOCK 2 — Gates ---
# ===========================================================================
caller.msg("\n|c--- Gates ---|n")

W["grand_gate"] = room(
    GateRoom,
    "The Grand Gate",
    """|wTwo iron-banded oak doors stand open in the great arched gateway.|n

Guards in polished town livery flank the arch, watching arrivals with
practiced calm. Carved in the stone above: |w"Leave lesser than you
arrived."|n The bustle of |wFounder's Walk|n begins to the west. The
open commons lie to the east.
""",
    ambient=[
        "A guard stamps their feet against the chill and straightens up.",
        "A cart rumbles through the gate with a cheerful wave from the driver.",
    ]
)

W["wardens_gate"] = room(
    GateRoom,
    "The Warden's Gate",
    """|wA sturdy western gate, less grand than the main entrance but no less solid.|n

Warden Crabb eyes every arrival with deep suspicion and a slowness to
warm up that borders on geological. Locals pass through with a nod;
strangers get the full once-over. The |wDusty Paddock|n lies to the west.
|wFounder's Walk|n stretches to the east.
""",
)

W["south_gate"] = room(
    GateRoom,
    "The South Gate",
    """|wA quiet gate at the southern end of Awtown, rarely busy.|n

The ironwork is entwined with carved vines — a tribute to the garden
beyond. Gate Hand Birch leans against the post with a book open in one
hand, looking up with the mild curiosity of someone with time to spare.
|wCraftsman's Road|n is to the north; the |wGarden of Remembrance|n to
the south.
""",
)

link(W["eastern_commons"], "west", W["grand_gate"], "east")


# ===========================================================================
# --- BLOCK 3 — Dusty Paddock (West Stables /4) ---
# ===========================================================================
caller.msg("\n|c--- Exterior: Dusty Paddock (Stables) ---|n")

W["dusty_paddock"] = room(
    ExteriorRoom,
    "The Dusty Paddock",
    """|yA sprawling stable complex west of the Warden's Gate.|n

The smell of hay, horse, and well-oiled leather is immediate and total.
Grooms move between stalls with practiced efficiency. Four areas branch
off from this central yard.
""",
    ambient=[
        "A horse stamps and blows softly in a nearby stall.",
        "The creak of a cart wheel echoes across the yard.",
    ]
)

W["north_stables"] = room(
    ExteriorRoom,
    "The North Stables",
    """|yLong rows of well-kept stalls stretch the length of this wing.|n

Horses from across Dorfin stand groomed and quiet. The smell of fresh
straw and good feed makes this a comfortable place, if you like horses.
Stableman Oswin moves methodically from stall to stall.
""",
    ambient=[
        "A horse nuzzles your sleeve with unexpected warmth.",
        "Oswin mutters something reassuring to a nervous-looking roan.",
    ]
)

W["south_stables"] = room(
    ExteriorRoom,
    "The South Stables",
    """|yThe working wing of the paddock — pack animals and common mounts.|n

Less polished than the north stables, but clean and functional. The
horses here have seen more road miles and carry their experience in their
posture.
""",
)

W["tack_room"] = room(
    ExteriorRoom,
    "The Tack Room",
    """|wEvery wall is hung with saddles, bridles, and riding gear.|n

The smell of leather oil is thick enough to taste. Equipment for every
kind of rider hangs in organized rows. Repairs happen here; sales happen
here too, at prices Stableman Oswin considers entirely reasonable.
""",
)

W["stable_yard"] = room(
    ExteriorRoom,
    "The Stable Yard",
    """|yAn open cobbled yard where horses are walked, watered, and traded.|n

Groom Pip darts between animals with a cheerful word and seemingly
infinite pockets full of carrots. The gate to the east leads back toward
Awtown proper.
""",
    ambient=[
        "Groom Pip produces a carrot from somewhere and holds it out.",
        "A merchant haggles loudly over the price of a spotted mare.",
    ]
)

link(W["wardens_gate"],  "west",      W["dusty_paddock"],  "east")
link(W["dusty_paddock"], "northwest", W["north_stables"],  "southeast")
link(W["dusty_paddock"], "northeast", W["south_stables"],  "southwest")
link(W["dusty_paddock"], "southwest", W["tack_room"],      "northeast")
link(W["dusty_paddock"], "southeast", W["stable_yard"],    "northwest")


# ===========================================================================
# --- BLOCK 4 — Garden of Remembrance (South /4) ---
# ===========================================================================
caller.msg("\n|c--- Exterior: Garden of Remembrance ---|n")

W["garden_remembrance"] = room(
    ExteriorRoom,
    "The Garden of Remembrance",
    """|gA walled garden of quiet beauty and gentle melancholy.|n

Used for peaceful reflection and the burial of Awtown's honored dead.
Flowers are tended with devotion; the paths are swept clean. Four areas
branch off from this central garden path.
""",
    ambient=[
        "Wind moves softly through the flowers. Nothing else does.",
        "Somewhere nearby, a bird calls once and falls silent.",
    ]
)

W["memorial_garden"] = room(
    ExteriorRoom,
    "The Memorial Garden",
    """|gCarefully tended flower beds surround small monuments to fallen heroes.|n

Each monument is inscribed with a name and a short epitaph. Groundskeeper
Enid moves slowly between them, pulling weeds and leaving small offerings.
She knows the name on every stone.
""",
    ambient=[
        "Enid pauses at one stone longer than the others. She doesn't say why.",
    ]
)

W["old_graves"] = room(
    ExteriorRoom,
    "The Old Graves",
    """|wWeathered headstones from Awtown's earliest days lean at varied angles.|n

The inscriptions are cryptic — names half-worn, dates that don't quite
add up. The oldest stones predate the founding records. At night,
something stirs here. During the day, it merely watches.
""",
    is_safe=False,
    desc_night="""|wThe old graves look different at night. The shadows are wrong.|n

The worn inscriptions seem deeper in the moonlight. Between the stones,
something moves that isn't wind. Don't look directly at it.
""",
    ambient=[
        "One of the older headstones has fresh flowers on it. No one saw who left them.",
    ]
)

W["reflecting_pool"] = room(
    ExteriorRoom,
    "The Reflecting Pool",
    """|cA still, dark pool lies surrounded by weeping willows.|n

The surface is perfectly calm regardless of the weather. Those who stare
long enough claim to see things — other places, other times, faces they
know and faces they don't. A hooded figure sits motionless at the water's
edge. They have never been seen to move.
""",
    ambient=[
        "The pool's surface ripples once. There is no wind.",
        "The hooded figure is in the same position it was when you arrived.",
    ]
)

W["willow_grove"] = room(
    ExteriorRoom,
    "The Willow Grove",
    """|gAncient willows cluster here, branches trailing the ground.|n

The light is green and filtered. The air smells of damp earth and
something faintly sweet. Herbalists make quiet pilgrimages here for
plants found nowhere else in Awtown. What grows here and why is not
entirely clear.
""",
    ambient=[
        "A rare herb grows at the base of one willow, overlooked by most.",
    ]
)

link(W["south_gate"],         "south",     W["garden_remembrance"], "north")
link(W["garden_remembrance"], "northwest", W["memorial_garden"],    "southeast")
link(W["garden_remembrance"], "northeast", W["old_graves"],         "southwest")
link(W["garden_remembrance"], "southwest", W["reflecting_pool"],    "northeast")
link(W["garden_remembrance"], "southeast", W["willow_grove"],       "northwest")


# ===========================================================================
# --- BLOCK 5 — Founder's Walk (Main North Road, E-W) ---
# ===========================================================================
caller.msg("\n|c--- Roads: Founder's Walk ---|n")

W["founders_walk_west"] = room(
    RoadRoom,
    "Along Founder's Walk (West)",
    """|cThe western stretch of Awtown's grandest road.|n

The cobblestones here are swept clean each morning. You walk where the
Founders walk. The |wWarden's Gate|n is to the west. Administrative
buildings line both sides — civic halls, offices, the occasional smell
of something official.
""",
    ambient=[
        "A town guard nods at you as they pass on their rounds.",
        "Two officials argue in low voices outside a building, stopping when they notice you.",
    ]
)

W["founders_walk_central"] = room(
    RoadRoom,
    "Along Founder's Walk (Central)",
    """|cThe heart of Founder's Walk, where the great road widens slightly.|n

The cobblestones here are worn smooth by generations of feet. Roads
branch north and south. The faint smell of incense drifts up from the
Temple to the south. The sound of hammers comes from the east.
""",
    ambient=[
        "A pilgrim hurries south toward the Temple, clutching a small wrapped parcel.",
        "The cobblestones are uneven here in one spot — someone pried one up and replaced it slightly wrong.",
    ]
)

W["founders_walk_east"] = room(
    RoadRoom,
    "Along Founder's Walk (East)",
    """|cThe eastern stretch of Founder's Walk, near the Founders' own offices.|n

The grandest buildings in Awtown line this stretch. The Workshop and the
Parlour are to the north. Ahead to the east, the |wHerald's Hall|n and
the |wGrand Gate|n.
""",
    ambient=[
        "The smell of machine oil drifts faintly from Hammerfall's Workshop.",
        "Someone exits Malgrave's Parlour looking noticeably more motivated than when they went in.",
    ]
)

link(W["wardens_gate"],          "east", W["founders_walk_west"],    "west")
link(W["founders_walk_west"],    "east", W["founders_walk_central"], "west")
link(W["founders_walk_central"], "east", W["founders_walk_east"],    "west")
link(W["founders_walk_east"],    "east", W["grand_gate"],            "west")


# ===========================================================================
# --- BLOCK 6 — North Row: Administrative District ---
# ===========================================================================
caller.msg("\n|c--- Buildings: Administrative District ---|n")

W["notary_office"] = room(
    Room,
    "The Notary's Office",
    """|wA cramped but tidy office squeezed between the gate and the road.|n

The smell of ink and wax seals never leaves this room. Deeds, contracts,
and witnessed oaths are the currency here. Notary Prim sits behind a
desk stacked with documents, ink-stained to the elbows and entirely at
peace with it.
""",
    ambient=[
        "The scratch of Prim's quill is the only sound.",
        "A fresh wax seal cools on the desk, pressed with a worn official stamp.",
    ]
)

W["messengers_roost"] = room(
    Room,
    "The Messenger's Roost",
    """|wA small, busy room that smells of feathers and leather satchels.|n

Messenger birds perch on racks along one wall. Runners come and go
constantly. Postmaster Wren never stands still for more than two seconds.
Word travels fast here — sometimes faster than is entirely comfortable.
""",
    ambient=[
        "A bird ruffles its feathers and fixes you with one bright eye.",
        "A runner bursts in, hands off a sealed packet, and is gone before anyone reacts.",
    ]
)

W["shadow_chamber"] = room(
    Room,
    "The Shadow Chamber",
    """|wA plain, unremarkable room that most people walk past without noticing.|n

A round table. Six chairs. No windows. The silence here is particular —
not empty, but occupied. The kind of room where things are decided that
are later described as having happened naturally. The door locks from
the inside.
""",
    no_teleport=True,
    light_level=2,
    ambient=[
        "The silence in here is complete.",
    ]
)

W["stewards_hall"] = room(
    Room,
    "The Steward's Hall",
    """|wA tidy administrative office where town logistics are managed.|n

Bulletin boards, ledgers, and supply manifests line every wall. Steward
Pell moves between them with the efficiency of someone who has turned
organization into an art form. Clerk Nimble's quill scratches without
pause.
""",
    ambient=[
        "Pell crosses something off a list and adds two more things.",
        "Nimble files a document with terrifying speed.",
    ]
)

W["artificers_post"] = room(
    Room,
    "The Artificer's Post",
    """|wA bright, cluttered workshop where broken things come to be fixed.|n

Magical items and mundane tools in various states of repair crowd every
surface. Tinker Cogsworth talks while he works, and while he thinks, and
while he listens, and at all other times. Apprentice Sprocket watches
something bubble in the corner with growing concern.
""",
    ambient=[
        "Cogsworth finishes a sentence, pauses, and immediately starts another.",
        "Something in the corner makes a sound it shouldn't.",
    ]
)

link(W["founders_walk_west"],    "north", W["notary_office"],    "south")
link(W["notary_office"],         "east",  W["messengers_roost"], "west")
link(W["messengers_roost"],      "east",  W["shadow_chamber"],   "west")
link(W["shadow_chamber"],        "east",  W["stewards_hall"],    "west")
link(W["stewards_hall"],         "east",  W["artificers_post"],  "west")
link(W["founders_walk_central"], "north", W["artificers_post"],  "south")


# ===========================================================================
# --- BLOCK 7 — Founders' Offices ---
# ===========================================================================
caller.msg("\n|c--- Buildings: Founders' Offices ---|n")

W["hammerfall_workshop"] = room(
    FounderRoom,
    "Hammerfall's Workshop",
    """|rAbsolute chaos. Every surface is covered in half-built devices and diagrams.|n

The smell of oil and hot metal is immediate. Half a suit of armor stands
in one corner, apparently mid-repair. Marro Hammerfall doesn't look up
when you enter. He's elbow-deep in something that looks important and
probably is.
""",
    ambient=[
        "Hammerfall grunts. It might be a greeting. It might be approval. Hard to say.",
        "Something on the far bench hisses, spins, and stops. Hammerfall doesn't react.",
    ]
)

W["malgraves_parlour"] = room(
    FounderRoom,
    "Malgrave's Parlour",
    """|yA warm, welcoming office that somehow always feels slightly busy.|n

Comfortable chairs face a large desk covered in notes and schedules.
A |w"You've Got This!"|n pennant hangs slightly crooked above the door.
Jorvyn Malgrave is already looking at you like he was expecting you
specifically.
""",
    ambient=[
        "Malgrave straightens a stack of papers, unsatisfied, and straightens them again.",
        "The pennant sways slightly even though there is no draft.",
    ]
)

W["oldmeres_study"] = room(
    FounderRoom,
    "Oldmere's Study",
    """|bFloor-to-ceiling shelves of books, maps, scrolls, and documents.|n

A meticulous system that only Joleth understands. A single clear desk
sits at the center, always with an open book on it. Joleth Oldmere looks
up from the pages with the particular expression of someone who just
remembered something they needed to tell you forty-five minutes ago.
""",
    ambient=[
        "Oldmere finds the exact book she wants without looking at the shelf.",
        "A stack of scrolls shifts on the shelf. Nothing falls. The system holds.",
    ]
)

link(W["founders_walk_east"], "north",     W["hammerfall_workshop"], "south")
link(W["hammerfall_workshop"],"east",      W["malgraves_parlour"],   "west")
link(W["founders_walk_east"], "northwest", W["oldmeres_study"],      "southeast")


# ===========================================================================
# --- BLOCK 8 — Herald's Hall & Assembly Hall ---
# ===========================================================================
caller.msg("\n|c--- Buildings: Entry District ---|n")

W["heralds_hall"] = room(
    Room,
    "The Herald's Hall",
    """|yHigh ceilings, bright torchlight, and a roaring fireplace welcome you.|n

This is the first room most adventurers see inside Awtown. A large
|wQuest Board|n dominates one wall; town maps are stacked on a side
table. Herald Bramwick is already halfway across the room toward you,
arms spread wide in welcome.

|c[The Quest Board is here. Town maps are available from Scribe Dilly.]|n
""",
    ambient=[
        "Bramwick greets a new arrival by name before they've said a word.",
        "A fresh notice has been pinned to the Quest Board. Dilly makes a note of it.",
        "The fire crackles warmly. Someone has just stoked it.",
    ]
)

W["assembly_hall"] = room(
    Room,
    "The Assembly Hall",
    """|wA grand vaulted chamber of stone and dark wood.|n

Rows of benches face a raised speaking dais. Portraits of the three
Founders hang on the walls, regarding the empty room with varying
degrees of approval. When Town Crier Aldous speaks here, the acoustics
make it the business of the entire building.
""",
    ambient=[
        "Your footsteps echo strangely under the vaulted ceiling.",
        "One of the Founder portraits has been slightly reframed. Malgrave's. Nobody admits to it.",
    ]
)

link(W["grand_gate"],   "west",  W["heralds_hall"],       "east")
link(W["heralds_hall"], "south", W["assembly_hall"],      "north")
link(W["heralds_hall"], "west",  W["founders_walk_east"], "east")


# ===========================================================================
# --- BLOCK 9 — Templegate Lane & Temple of the Eternal Flame (/4) ---
# ===========================================================================
caller.msg("\n|c--- Roads & Temple: Templegate Lane ---|n")

W["templegate_lane_north"] = room(
    RoadRoom,
    "Templegate Lane (North)",
    """|yA short, well-worn stretch running south off Founder's Walk.|n

Pilgrims, healers, and the merely curious all pass through here.
Small lanterns flicker at the junction overhead. The faint smell of
incense drifts up from the south.
""",
    ambient=[
        "A pilgrim moves past in silence, eyes forward.",
        "One of the lanterns overhead gutters and steadies again.",
    ]
)

W["templegate_lane_south"] = room(
    RoadRoom,
    "Templegate Lane (South)",
    """|yThe lane widens slightly as it approaches the Temple doors.|n

The stone here is smoother, worn by more feet and more reverence.
Carved pillars mark the entrance to the south. A small donation bowl
sits unattended by the door, reliably and mysteriously full.
""",
)

W["temple_nave"] = room(
    TempleRoom,
    "The Temple — The Nave",
    """|wA soaring vaulted ceiling rises above rows of worn pews.|n

At the altar, an eternal flame burns in a brass bowl that has not
been empty in living memory. The light it casts is warm and steady.
High Priest Edwyn Lux moves between the pews with unhurried purpose.
Four wings branch off from here.
""",
    rest_bonus=1,
    ambient=[
        "The eternal flame flickers once, then burns steady.",
        "A quiet prayer is being murmured somewhere in the pews.",
        "Edwyn Lux lights a candle and places it at the altar without ceremony.",
    ]
)

W["temple_sanctuary"] = room(
    TempleRoom,
    "The Temple — The Sanctuary",
    """|cQuiet and candlelit, this wing smells of herbs and clean linen.|n

Clerics tend to the wounded on low cots. Sister Sera hums softly to
herself as she works. Whatever the injury, the attitude here is one of
calm certainty that things will improve. They usually do.
""",
    rest_bonus=2,
    ambient=[
        "Sister Sera changes a dressing with practiced, gentle hands.",
        "The candles here never seem to burn down.",
    ]
)

W["temple_vestry"] = room(
    TempleRoom,
    "The Temple — The Vestry",
    """|wRobes hang in precise rows. Ritual items are stored in labeled cases.|n

Prayer texts are stacked by faith and frequency of use. Brother Aldwin
sits at a writing desk, neither looking up nor acknowledging you until
you speak first. Cleric training happens here, on Aldwin's schedule and
Aldwin's terms.
""",
    trainer_npc=None,
    ambient=[
        "The scratch of Aldwin's quill stops. He reads what he wrote. He continues.",
    ]
)

W["temple_bell_tower"] = room(
    TempleRoom,
    "The Temple — The Bell Tower",
    """|wA narrow staircase leads to this small, wind-swept chamber.|n

The bell overhead hasn't been rung in years — by choice. Paladin-Warden
Thane Dusk trains here in the high light and open air, his sword moving
in patterns that look simple until you try to follow them. He will train
others. He expects dedication.
""",
    is_outdoor=True,
    light_level=5,
    trainer_npc=None,
    ambient=[
        "The wind up here is constant and cold.",
        "Thane Dusk's sword returns to guard so smoothly the motion seems continuous.",
    ]
)

link(W["founders_walk_central"],  "south",     W["templegate_lane_north"], "north")
link(W["templegate_lane_north"],  "south",     W["templegate_lane_south"], "north")
link(W["templegate_lane_south"],  "south",     W["temple_nave"],           "north")
link(W["temple_nave"],            "northwest", W["temple_sanctuary"],      "southeast")
link(W["temple_nave"],            "northeast", W["temple_vestry"],         "southwest")
link(W["temple_nave"],            "southwest", W["temple_bell_tower"],     "northeast")


# ===========================================================================
# --- BLOCK 10 — Market Row (Middle E-W Road) ---
# ===========================================================================
caller.msg("\n|c--- Roads: Market Row ---|n")

W["market_row_west"] = room(
    RoadRoom,
    "Market Row (West)",
    """|yThe western stretch of Awtown's busiest commercial road.|n

The smell of fresh bread drifts from the Hearthstone to the north. The
clink of commerce is constant. Lanterns hang at the crossings. The road
runs east toward the Vault of Gold and the Crystal Repository.
""",
    ambient=[
        "A merchant haggles loudly over something. Both parties seem to be enjoying it.",
        "The smell of fresh bread is distracting.",
    ]
)

W["market_row_east"] = room(
    RoadRoom,
    "Market Row (East)",
    """|yThe eastern stretch of Market Row, near the bank and the study.|n

The clink of gold from the Vault carries clearly. The road connects the
Temple district to the west with the Outfitter's and the Herald's Hall
to the east.
""",
    ambient=[
        "Someone exits the Vault of Gold looking satisfied. Briefly.",
    ]
)

link(W["templegate_lane_south"], "east", W["market_row_west"],  "west")
link(W["market_row_west"],       "east", W["market_row_east"],  "west")
link(W["market_row_east"],       "east", W["heralds_hall"],     "west")


# ===========================================================================
# --- BLOCK 11 — Vault of Gold, Assay Office, Crystal Repository ---
# ===========================================================================
caller.msg("\n|c--- Buildings: Financial District ---|n")

W["vault_of_gold"] = room(
    Room,
    "The Vault of Gold",
    """|wA squat stone building with a heavy iron door and barred windows.|n

Polished wood counters give the interior the air of a place where money
is treated with appropriate respect. Banker Guildred Copperpot stands at
the central counter, precise as a decimal point. Vault Guard Holt stands
by the door, silent as an axiom.
""",
    ambient=[
        "Copperpot recounts a stack of coins. The total is the same. He recounts them again.",
        "Holt has not moved in some time.",
    ]
)

W["assay_office"] = room(
    Room,
    "The Assay Office",
    """|wA clean, well-lit room of scales, magnifying lenses, and testing trays.|n

Gems, ore samples, and mysterious objects are brought here to be
appraised. Assayer Dunt examines everything with the same expression:
absolute incorruptible focus. He has never given an incorrect valuation.
He will not start today.
""",
    ambient=[
        "Dunt holds a gem up to the light and makes a sound that could be appreciation.",
    ]
)

W["crystal_repository"] = room(
    CourtyardRoom,
    "The Crystal Repository",
    """|cAn open stone courtyard enclosed by tall walls.|n

At its center, a humming crystal formation pulses with soft, steady
light. Scholars come here to read stored knowledge. Others find it
unsettling. Archivist Quellan tends the crystals with quiet devotion and
occasionally whispers to them when he thinks no one is watching.
""",
    ambient=[
        "The crystals hum at a frequency you feel more than hear.",
        "Quellan whispers something to the central crystal. It pulses once in response.",
    ]
)

link(W["market_row_west"],  "south", W["vault_of_gold"],      "north")
link(W["vault_of_gold"],    "east",  W["assay_office"],       "west")
link(W["assay_office"],     "east",  W["crystal_repository"], "west")
link(W["market_row_east"],  "south", W["crystal_repository"], "north")


# ===========================================================================
# --- BLOCK 12 — Outfitter's Rest ---
# ===========================================================================
caller.msg("\n|c--- Buildings: Outfitter's Rest ---|n")

W["outfitters_rest"] = room(
    Room,
    "The Outfitter's Rest",
    """|yA cozy shop with overstuffed chairs and warm golden light.|n

New adventurers can claim a basic starter kit here — simple clothing,
a belt pouch, a torch. Shopkeep Marta fusses over every customer with
grandmotherly concern. Nothing here is fancy. Everything here is enough.

|c[New characters may claim a free starter kit here, once.]|n
""",
    rest_bonus=1,
    ambient=[
        "Marta presses a packet of travel biscuits into someone's hand before they can refuse.",
        "The chairs here are extremely comfortable. This is not an accident.",
    ]
)

link(W["market_row_east"], "north", W["outfitters_rest"], "south")
link(W["outfitters_rest"], "west",  W["oldmeres_study"],  "east")


# ===========================================================================
# --- BLOCK 13 — Hearthstone Inn (/4) ---
# ===========================================================================
caller.msg("\n|c--- Buildings: Hearthstone Inn ---|n")

W["hearthstone_inn"] = room(
    InnRoom,
    "The Hearthstone Inn",
    """|yThe social heart of Awtown — warm, loud, and permanently fragrant.|n

The smell of roasting meat and spilled ale hits you before you're fully
through the door. Innkeeper Bess Copperladle runs the floor with the
authority of someone who owns the room in every sense. Four wings
connect from this central common space.
""",
    rest_bonus=2,
    ambient=[
        "The hearth roars. Someone is singing badly and nobody is telling them to stop.",
        "Bess moves through the crowd with a tray, remembering everyone's order.",
    ]
)

W["common_room"] = room(
    InnRoom,
    "The Hearthstone — The Common Room",
    """|yThe main tavern floor: crowded benches, a roaring hearth, the bar.|n

Music most evenings. Rumors always. Barkeep Finn serves drinks without
spilling a drop while carrying on three separate conversations. Lute-
player Cobble is in the corner doing something technically musical.
""",
    rest_bonus=2,
    ambient=[
        "Finn slides a drink down the bar without looking. It stops exactly where it should.",
        "Cobble hits a wrong note, recovers, and pretends it was intentional.",
        "Two locals argue passionately about something that happened fifteen years ago.",
    ]
)

W["the_kitchen"] = room(
    InnRoom,
    "The Hearthstone — The Kitchen",
    """|rCook Darra runs this kitchen with iron efficiency and zero tolerance.|n

The food that emerges from here is exceptional. The atmosphere for
uninvited visitors is not. Darra has opinions about people being in
her kitchen. Those opinions are negative and she will share them at
volume.
""",
    ambient=[
        "Something sizzles. The smell is outstanding.",
        "Darra notices you looking. Her expression suggests you are in the wrong room.",
    ]
)

W["private_snug"] = room(
    InnRoom,
    "The Hearthstone — The Private Snug",
    """|wCurtained booths line this quieter back room.|n

For private meetings, shady deals, and the patient art of eavesdropping.
A Suspicious Figure occupies one of the booths. Different figure than
last week. Same booth. They will not explain this.
""",
    light_level=2,
    ambient=[
        "Someone in a curtained booth speaks very quietly. You catch one word: 'tonight.'",
    ]
)

W["the_cellar"] = room(
    InnRoom,
    "The Hearthstone — The Cellar",
    """|wStone stairs lead down to a barrel-lined cellar, dark and cold.|n

The inn's reserves of wine, ale, and preserved foods fill the racks.
There is, in the back corner, behind the oldest barrels, a door that
shouldn't be here. No one who works at the inn will discuss it.
""",
    light_level=1,
    is_safe=False,
    ambient=[
        "Something drips in the dark.",
        "The door in the corner is definitely still there.",
    ]
)

link(W["market_row_west"],  "north",     W["hearthstone_inn"], "south")
link(W["hearthstone_inn"],  "northwest", W["common_room"],     "southeast")
link(W["hearthstone_inn"],  "northeast", W["the_kitchen"],     "southwest")
link(W["hearthstone_inn"],  "southwest", W["private_snug"],    "northeast")
link(W["hearthstone_inn"],  "southeast", W["the_cellar"],      "northwest")


# ===========================================================================
# --- BLOCK 14 — Warden's Way (N-S Road) & West District Buildings ---
# ===========================================================================
caller.msg("\n|c--- Roads: Warden's Way ---|n")

W["wardens_way_north"] = room(
    RoadRoom,
    "Along Warden's Way (North)",
    """|5A quieter road, favored by craftsmen and those avoiding Founder's Walk.|n

The paving stones are uneven but solid. Administrative offices to one
side, storage to the other. The road runs north to Founder's Walk and
south toward the crafting district.
""",
    ambient=[
        "A craftsman passes with a bundle of timber under one arm.",
    ]
)

W["wardens_way_central"] = room(
    RoadRoom,
    "Along Warden's Way (Central)",
    """|5The middle stretch of Warden's Way — foot traffic lighter here.|n

A useful connector between the administrative north and the crafting
south. The Round Table meeting room is nearby. The distant ring of the
forge drifts from below.
""",
)

link(W["founders_walk_west"],   "south", W["wardens_way_north"],   "north")
link(W["wardens_way_north"],    "south", W["wardens_way_central"], "north")

caller.msg("\n|c--- Buildings: West District ---|n")

W["deed_hall"] = room(
    Room,
    "The Deed Hall",
    """|wA narrow room lined with filing cabinets and land registry scrolls.|n

Every plot of land in Awtown and surrounding territory has a record here.
Registrar Voss can produce any document within thirty seconds. He
considers this his primary achievement and is correct to do so.
""",
    ambient=[
        "The filing system in here is either genius or deeply personal.",
    ]
)

W["round_table"] = room(
    Room,
    "The Round Table",
    """|yA small, comfortable room centered on — yes — an actual round table.|n

Guild Registrar Brom will mention the table. He will mention it more
than once. The room is used for guild registrations, private negotiations,
and occasionally heated disputes about the table. The table is genuinely
round.
""",
    ambient=[
        "Brom glances at the table with quiet satisfaction.",
    ]
)

W["quartermaster_cache"] = room(
    Room,
    "The Quartermaster's Cache",
    """|wA tidy storeroom of boxes, crates, and meticulously labeled barrels.|n

Quartermaster Hobb will not release any supply without a signed manifest
in triplicate. He considers this a reasonable system. Everyone who has
ever needed something urgently considers it a personal vendetta.
""",
    ambient=[
        "Hobb checks an inventory list, makes a mark, and checks it again.",
    ]
)

W["posting_board"] = room(
    Room,
    "The Posting Board",
    """|yA public room dominated by an enormous cork board.|n

Notices, contracts, job offers, and wanted postings cover every inch.
Board-Keeper Sal manages what goes up and what comes down. She will post
anything for a coin and tear down anything for two, with no opinions
expressed either way.
""",
    ambient=[
        "Someone pins a new notice. Sal doesn't look up.",
        "A wanted poster at the edge of the board catches your eye.",
    ]
)

link(W["wardens_way_north"],   "west",  W["deed_hall"],           "east")
link(W["wardens_way_central"], "west",  W["round_table"],         "east")
link(W["wardens_way_central"], "north", W["quartermaster_cache"], "south")
link(W["wardens_way_central"], "south", W["posting_board"],       "north")


# ===========================================================================
# --- BLOCK 15 — Warden's Barracks ---
# ===========================================================================
caller.msg("\n|c--- Buildings: Warden's Barracks ---|n")

W["wardens_barracks"] = room(
    Room,
    "The Warden's Barracks",
    """|wA long, practical room that smells of leather polish and cold iron.|n

Bunk frames line one wall; weapons racks line the other. A duty roster
and a wanted-notice board hang by the door. Sergeant Dorn runs drills
here with the focus of someone who has trained a hundred soldiers and
found fault with every one of them — affectionately.
""",
    trainer_npc=None,
    ambient=[
        "Guard Recruit Pip polishes a helmet that is clearly too big for him.",
        "Sergeant Dorn corrects someone's stance with a single word and a look.",
    ]
)

link(W["wardens_gate"],     "south", W["wardens_barracks"],  "north")
link(W["wardens_barracks"], "east",  W["wardens_way_north"], "west")


# ===========================================================================
# --- BLOCK 16 — Craftsman's Road (Bottom E-W) ---
# ===========================================================================
caller.msg("\n|c--- Roads: Craftsman's Road ---|n")

W["craftsmans_road_west"] = room(
    RoadRoom,
    "Craftsman's Road (West)",
    """|rThe western stretch of the southern road — dusty and purposeful.|n

The ring of hammers is never far away. Crates line the road edges. The
smell of metal shavings and sawdust is permanent. Workers move with the
efficiency of people who have places to be and things to make.
""",
    ambient=[
        "A cart loaded with raw timber rumbles past.",
        "The smell of hot metal from the forge is noticeably stronger here.",
    ]
)

W["craftsmans_road_east"] = room(
    RoadRoom,
    "Craftsman's Road (East)",
    """|rThe eastern stretch of Craftsman's Road, near the forge complex.|n

The Grand Forge's heat can be felt from here on warm days. The Tinker's
Den announces itself with the smell of oil and an occasional distant
metallic clank. The South Gate lies further south.
""",
    ambient=[
        "Sparks drift briefly into the road from somewhere in the forge complex.",
    ]
)

link(W["wardens_way_central"],  "south", W["craftsmans_road_west"], "north")
link(W["craftsmans_road_west"], "east",  W["craftsmans_road_east"], "west")
link(W["craftsmans_road_east"], "south", W["south_gate"],           "north")


# ===========================================================================
# --- BLOCK 17 — Grand Forge (/4) ---
# ===========================================================================
caller.msg("\n|c--- Buildings: Grand Forge ---|n")

W["grand_forge"] = room(
    CraftingRoom,
    "The Grand Forge",
    """|rAwtown's premier crafting complex — four workshops under one sprawling roof.|n

The noise is constant: hammering, sawing, the hiss of hot metal in
water, and the occasional sharp pop from the Alchemist's Corner that
makes everyone flinch. The smell is iron, cedar, and something that
might be herbs or might be something considerably more alarming.
""",
    ambient=[
        "A distant hammer rings a steady rhythm deep in the complex.",
        "Someone shouts a question. An answer comes back in Dwarvish.",
    ]
)

W["iron_forge"] = room(
    CraftingRoom,
    "The Grand Forge — The Iron Forge",
    """|rA thundering forge with massive bellows and an ever-burning flame.|n

The heat here is a physical presence. Master Smith Brondal Ironmark
works at the central anvil with the unhurried certainty of a craftsman
who has never once doubted what he was doing. Weapons and armor are made
here, and made properly.
""",
    trainer_npc=None,
    ambient=[
        "The hammer falls. The metal rings. This happens again.",
        "Brondal examines the edge of a blade and makes a sound that might be approval.",
    ]
)

W["workbench"] = room(
    CraftingRoom,
    "The Grand Forge — The Workbench",
    """|yFragrant cedar and leather fill this bright workshop.|n

Bows, shields, furniture, and saddles in various stages of completion
cover every surface. Carpenter Wynn hums to himself as he works,
cheerful in the way of someone who genuinely loves what they do and
cannot understand why everyone doesn't.
""",
    trainer_npc=None,
    ambient=[
        "Wynn whistles something tuneless and cheerful.",
        "The smell of fresh-cut cedar is exceptional.",
    ]
)

W["loom_room"] = room(
    CraftingRoom,
    "The Grand Forge — The Loom Room",
    """|mThe quietest of the four workshops — a relative term in the Forge.|n

Cloth, clothing, robes, and banners in progress hang from frames. Weaver
Mira works at the central loom with the precise, focused energy of
someone who considers a single misaligned thread a personal failing.
She has never had a personal failing. The cloaks prove it.
""",
    trainer_npc=None,
    ambient=[
        "The loom moves with hypnotic rhythm.",
        "Mira holds a length of cloth to the light, satisfied, then finds one flaw.",
    ]
)

W["alchemists_corner"] = room(
    CraftingRoom,
    "The Grand Forge — The Alchemist's Corner",
    """|gBubbling vials, impossible smells, and the faint scent of scorched eyebrow.|n

Potions and reagents line the shelves in a system Alchemist Sable Dross
insists is ordered, though no one else has navigated it successfully.
She works with the happy distraction of someone thinking about three
other things simultaneously.
""",
    trainer_npc=None,
    ambient=[
        "Something pops. Sable Dross doesn't look up.",
        "A vial turns a color it wasn't a moment ago. Sable makes a note.",
    ]
)

link(W["craftsmans_road_west"], "south",     W["grand_forge"],       "north")
link(W["grand_forge"],          "northwest", W["iron_forge"],        "southeast")
link(W["grand_forge"],          "northeast", W["workbench"],         "southwest")
link(W["grand_forge"],          "southwest", W["loom_room"],         "northeast")
link(W["grand_forge"],          "southeast", W["alchemists_corner"], "northwest")


# ===========================================================================
# --- BLOCK 18 — Tinker's Den ---
# ===========================================================================
caller.msg("\n|c--- Buildings: Tinker's Den ---|n")

W["tinkers_den"] = room(
    CraftingRoom,
    "The Tinker's Den",
    """|wGears, springs, lenses, and gadgets hang from every surface.|n

The smell of machine oil is overwhelming in the best possible way.
Cogwright Fenn presides over the organized chaos with the ease of a man
who could find any specific component by feel in the dark. Automaton
Tick sweeps the floor and occasionally says something surprisingly
profound about existence.
""",
    trainer_npc=None,
    ambient=[
        "Tick sweeps past your feet and makes a small sound that might be a greeting.",
        "Fenn produces the exact part he needs from a drawer without looking.",
    ]
)

link(W["craftsmans_road_east"], "south", W["tinkers_den"], "north")
link(W["grand_forge"],          "east",  W["tinkers_den"], "west")


# ===========================================================================
# --- BLOCK 19 — South Row: Training & Specialist Buildings ---
# ===========================================================================
caller.msg("\n|c--- Buildings: South Row ---|n")

W["apprentice_hall"] = room(
    TrainingRoom,
    "The Apprentice Hall",
    """|yA large open room of practice dummies, training weapons, and battered desks.|n

Young would-be adventurers study here with an enthusiasm that regularly
crosses into chaos. Headmaster Thane Orifel watches it all with the
expression of a man who has seen a hundred classes and is fairly certain
this one won't kill him. Apprentice Rudd is already looking at you like
he wants to spar.
""",
    trainer_npc=None,
    ambient=[
        "Apprentice Rudd squares up to a practice dummy and misses.",
        "Apprentice Yeva is annotating a textbook in the corner, oblivious to the noise.",
        "Orifel pinches the bridge of his nose and says nothing for a long moment.",
    ]
)

W["study_hall"] = room(
    TrainingRoom,
    "The Study Hall",
    """|wRows of desks and chalkboards covered in diagrams fill this quieter room.|n

The studious refuge from the Apprentice Hall next door. Scholar Bevin
supervises with patient calm. Student Mop is asleep at a desk again and
has somehow, once again, passed every assessment. No one investigates
this.
""",
    ambient=[
        "Student Mop is asleep. His notes, inexplicably, are excellent.",
        "Bevin corrects a diagram on the board, pauses, and draws it better.",
    ]
)

W["hermits_hollow"] = room(
    Room,
    "The Hermit's Hollow",
    """|gThis room is inexplicably made to look like a woodland cave.|n

Moss on the walls. A small fire pit. A wooden stool. Nobody knows how
this ended up inside a town building and nobody has ever asked. Sage
Aldric Voss sits beside the fire, looking up at you with the expression
of a man who already knows what you came to ask and has prepared his
answer in the form of a question.
""",
    light_level=2,
    ambient=[
        "The fire burns without any apparent fuel.",
        "Aldric Voss is already looking at you. He was looking at you when you arrived.",
    ]
)

W["cartographers_den"] = room(
    Room,
    "The Cartographer's Den",
    """|wEvery surface is covered in maps — rolled, pinned, framed, half-finished.|n

A large drafting table dominates the center. Mapper Izra works over it
with a focus that borders on aggressive. She will sell you the best maps
in Dorfin, train you in Navigation, and pay well for uncharted territory
data. She does not make small talk. The maps speak for her.
""",
    trainer_npc=None,
    ambient=[
        "Izra marks a new detail on a map with a tiny, precise stroke.",
    ]
)

W["herbalists_nook"] = room(
    Room,
    "The Herbalist's Nook",
    """|gBundles of drying herbs hang from the rafters. Jars crowd every shelf.|n

The smell is complex, green, and somehow ancient. Hedge-Witch Morvaine
doesn't look up when you enter. She knows you're there. She knows what
you want. She is deciding whether you deserve it. Mud is tracked in
regularly and no one apologizes for it.
""",
    trainer_npc=None,
    ambient=[
        "Something in a jar moves. Probably herbs.",
        "Morvaine makes a sound somewhere between a grunt and a diagnosis.",
    ]
)

link(W["craftsmans_road_west"], "east",  W["apprentice_hall"],   "west")
link(W["apprentice_hall"],      "east",  W["study_hall"],        "west")
link(W["study_hall"],           "east",  W["hermits_hollow"],    "west")
link(W["hermits_hollow"],       "east",  W["cartographers_den"], "west")
link(W["craftsmans_road_west"], "south", W["herbalists_nook"],   "north")
link(W["herbalists_nook"],      "east",  W["apprentice_hall"],   "west")


# ===========================================================================
# --- BLOCK 20 — Washhouses, Pantry, Supply Room ---
# ===========================================================================
caller.msg("\n|c--- Buildings: Washhouses & Storage ---|n")

W["washhouse_north"] = room(
    Room,
    "The Washhouse (North)",
    """|cWarm water, clean towels, and soap that smells faintly of lavender.|n

A surprising luxury for a town of this size. The staff work quietly and
efficiently. The dirt of the road comes off here. So does the kind of
weariness that is more than physical.
""",
    rest_bonus=1,
    ambient=[
        "Someone leaves looking measurably better than when they arrived.",
        "The lavender smell is stronger today.",
    ]
)

W["washhouse_south"] = room(
    Room,
    "The Washhouse (South)",
    """|cThe southern washhouse — identical to its northern sibling.|n

Same warm water, same lavender soap, same quiet efficiency. Positioned
here for the convenience of crafting district workers who carry more
industrial grime and require correspondingly more industrial washing.
""",
    rest_bonus=1,
)

W["pantry"] = room(
    Room,
    "The Pantry",
    """|wA small, cool room with stone walls and a heavy door.|n

Shelves of preserved foods, dried goods, candles, and travel rations
line the walls. A stout, quiet woman named Nan keeps everything orderly
and sells rations without ever making eye contact. This is not
unfriendliness. It is efficiency.
""",
    ambient=[
        "Nan straightens a row of ration packs that were already straight.",
    ]
)

W["supply_room"] = room(
    Room,
    "The Supply Room",
    """|wA general overflow storage room of organized chaos.|n

Things end up here when there's no better place for them. Stock Boy Fen
has a system, theoretically. He will explain it if asked. The explanation
will not clarify anything, but his enthusiasm will be genuine.
""",
    ambient=[
        "A crate in the corner is labelled 'MISC — DO NOT OPEN'. Fen doesn't remember why.",
    ]
)

link(W["wardens_way_north"],   "east",      W["washhouse_north"], "west")
link(W["wardens_way_central"], "east",      W["washhouse_south"], "west")
link(W["wardens_way_central"], "northwest", W["pantry"],          "southeast")
link(W["wardens_way_central"], "northeast", W["supply_room"],     "southwest")


# ===========================================================================
# --- BLOCK 21 — Watchtower & The Precipice ---
# ===========================================================================
caller.msg("\n|c--- Buildings: Watchtower & Precipice ---|n")

W["watchtower"] = room(
    Room,
    "The Watchtower",
    """|wA narrow stone tower with a single winding staircase.|n

From the top, on a clear day, you can see the edges of Dorfin. Watchman
Teris stands at the parapet, scanning the southern approaches with sharp
eyes. He notices things at distances that don't seem reasonable. He has
never once explained how.
""",
    trainer_npc=None,
    ambient=[
        "Teris points at something in the distance. When you look, it's gone.",
    ]
)

W["the_precipice"] = room(
    LookoutRoom,
    "The Precipice",
    """|wA dramatic stone shelf juts out from the southern wall, high above the land.|n

The wind here is constant and clean. On a clear day, the full sweep of
Dorfin unfolds below — distant forests, dark hills, and the glimmer of
unknown waters far to the east. Adventurers come here before setting
out, and sometimes after returning, just to remember why they left.
""",
    desc_night="""|wThe Precipice at night is something else entirely.|n

The lights of Awtown glow behind you. Ahead, the dark land of Dorfin
stretches to every horizon, marked only by the occasional distant fire
or the cold silver of a river catching moonlight. The wind is the same.
You are not quite the same person who stood here in daylight.
""",
    ambient=[
        "The wind up here is constant and cold and somehow clarifying.",
        "The view from here makes problems seem the correct size.",
    ]
)

link(W["craftsmans_road_west"], "west", W["watchtower"],    "east")
link(W["watchtower"],           "up",   W["the_precipice"], "down")


# ===========================================================================
# --- BLOCK 22 — Final Report ---
# ===========================================================================

caller.msg("\n|y" + "="*60 + "|n")
caller.msg("|wAwtown world build complete!|n")
caller.msg("|y" + "="*60 + "|n")
caller.msg(f"\n|cTotal rooms built:|n {len(W)}")
caller.msg(f"\n|cNew player start room:|n")
caller.msg(f"  {W['eastern_commons'].key} — {W['eastern_commons'].dbref}")
caller.msg(f"\n|cRecommended DEFAULT_HOME:|n")
caller.msg(f"  {W['heralds_hall'].key} — {W['heralds_hall'].dbref}")
caller.msg("""
|yNext steps — add to your settings.py ConfigMap:|n

  START_LOCATION = "{start}"
  DEFAULT_HOME   = "{home}"

|yThen:|n
  1. @reload  (or pod restart to pick up settings)
  2. @tel {start}  (verify you land in Eastern Commons)
  3. Build NPCs in world/npcs.py

|gDorfin awaits.|n
""".format(
    start=W["eastern_commons"].dbref,
    home=W["heralds_hall"].dbref,
))
