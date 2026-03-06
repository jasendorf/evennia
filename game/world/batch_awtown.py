"""
DorfinMUD — Awtown World Builder
=================================
Run with:  @batchcode world.batch_awtown

All /4 room sets are strict 2x2 grids:
    NW <-e/w-> NE
     |          |
    n/s        n/s
     |          |
    SW <-e/w-> SE

Each room connects only to its two cardinal neighbors.
No hub rooms. No diagonal exits.
"""

# ---------------------------------------------------------------------------
#HEADER
# ---------------------------------------------------------------------------

from evennia import create_object
from typeclasses.rooms import (
    Room, RoadRoom, GateRoom, ExteriorRoom, CourtyardRoom,
    InnRoom, TempleRoom, CraftingRoom, TrainingRoom, FounderRoom, LookoutRoom,
)
from typeclasses.exits import Exit

DIR_ALIASES = {
    "north":     ["n"],
    "south":     ["s"],
    "east":      ["e"],
    "west":      ["w"],
    "northwest": ["nw"],
    "northeast": ["ne"],
    "southwest": ["sw"],
    "southeast": ["se"],
    "up":        ["u"],
    "down":      ["d"],
}

def room(typeclass, key, desc, zone="awtown", **kwargs):
    r = create_object(typeclass, key=key)
    r.db.desc = desc
    r.db.zone = zone
    for attr, val in kwargs.items():
        setattr(r.db, attr, val)
    caller.msg(f"|g  Created:|n {key} [{typeclass.__name__}] {r.dbref}")
    return r

def exit(name, from_room, to_room):
    aliases = DIR_ALIASES.get(name, [])
    create_object(Exit, key=name, aliases=aliases,
                  location=from_room, destination=to_room)

def link(room_a, dir_ab, room_b, dir_ba):
    exit(dir_ab, room_a, room_b)
    exit(dir_ba, room_b, room_a)

W = {}

caller.msg("|y" + "="*60 + "|n")
caller.msg("|wDorfinMUD — Building Awtown|n")
caller.msg("|y" + "="*60 + "|n")


# ===========================================================================
#CODE

# ---------------------------------------------------------------------------
# SECTION 1 — Eastern Commons (/4)
#
#   Wayfarers' Green (NW) <-e/w-> Cart Market (NE)
#          n/s                          n/s
#   Notice Board (SW)    <-e/w-> Toll Stone (SE)
#
#   Entry: Grand Gate --east--> Wayfarers' Green (NW, west side of grid)
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Exterior: Eastern Commons (/4) ---|n")

W["wayfarers_green"] = room(
    ExteriorRoom, "The Wayfarers' Green",
    """|gA patch of worn but welcoming grass spreads beneath a broad oak tree.|n

The first thing most travelers see arriving from Awtown's Grand Gate to the west.
Bedrolls, campfires, and quiet conversations fill the space. A weathered sign
reads: |w"Rest your feet. The road will wait."|n

The cart market lies to the east; the notice board is to the south.
""",
    ambient=["A group of travelers huddles around a small fire.",
             "Someone sharpens a blade with slow, rhythmic strokes."])

W["cart_market"] = room(
    ExteriorRoom, "The Cart Market",
    """|yA row of wooden carts and canvas stalls lines the eastern edge of the commons.|n

Traveling merchants hawk goods of dubious provenance. Trader Moss watches you
with a merchant's appraising eye. The green lies to the west; the Toll Stone
is to the south.
""",
    ambient=["A merchant shouts something about a 'once in a lifetime' price.",
             "The smell of spiced sausage drifts from somewhere."])

W["notice_board"] = room(
    ExteriorRoom, "The Crossroads Notice Board",
    """|wA massive oak board, weathered but sturdy, stands at the crossroads.|n

Layers of parchment, nailed notices, and hand-scrawled rumors cover every inch.
The Wayfarers' Green is to the north; the Toll Stone lies to the east.
""",
    ambient=["Someone reads a notice, tears it down, and pockets it."])

W["toll_stone"] = room(
    ExteriorRoom, "The Toll Stone",
    """|wA crumbling stone pillar marks the old boundary of Awtown.|n

The founding date of Dorfin is carved into its face. Tollkeeper Renwick leans
against it with the patience of a man surprised by nothing. The notice board
is to the west; the cart market lies to the north.
""")

#  2x2 grid connections
link(W["wayfarers_green"], "east",  W["cart_market"],  "west")   # NW <-> NE
link(W["notice_board"],    "east",  W["toll_stone"],   "west")   # SW <-> SE
link(W["wayfarers_green"], "south", W["notice_board"], "north")  # NW <-> SW
link(W["cart_market"],     "south", W["toll_stone"],   "north")  # NE <-> SE


# ---------------------------------------------------------------------------
# SECTION 2 — Gates
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Gates ---|n")

W["grand_gate"] = room(
    GateRoom, "The Grand Gate",
    """|wTwo iron-banded oak doors stand open in the great arched gateway.|n

Guards in polished town livery flank the arch. Carved above:
|w"Leave lesser than you arrived."|n

To the east lies the open commons. To the west, Founder's Walk and Awtown.
""",
    ambient=["A cart rumbles through with a cheerful wave.",
             "A guard stamps their feet and straightens up."])

W["wardens_gate"] = room(
    GateRoom, "The Warden's Gate",
    """|wA sturdy western gate, less grand than the main entrance but no less solid.|n

Warden Crabb eyes every arrival with deep suspicion. Locals pass through with
a nod; strangers get the full once-over. The stables lie to the west; Founder's
Walk stretches to the east.
""")

W["south_gate"] = room(
    GateRoom, "The South Gate",
    """|wA quiet gate at the southern end of Awtown, rarely busy.|n

The ironwork is entwined with carved vines. Gate Hand Birch leans against the
post with a book open, looking up with mild curiosity. Craftsman's Road is to
the north; the Garden of Remembrance lies to the south.
""")

link(W["wayfarers_green"], "west", W["grand_gate"], "east")


# ---------------------------------------------------------------------------
# SECTION 3 — Dusty Paddock (/4)
#
#   North Stables (NW) <-e/w-> South Stables (NE)
#          n/s                        n/s
#   Tack Room (SW)    <-e/w-> Stable Yard (SE)
#
#   Entry: Warden's Gate --west--> North Stables (NW, east side of grid)
#   Note: "North" and "South" in the stable names refer to their position
#         within the paddock, not their map direction.
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Exterior: Dusty Paddock (/4) ---|n")

W["north_stables"] = room(
    ExteriorRoom, "The North Stables",
    """|yLong rows of well-kept stalls stretch the length of this wing.|n

Horses from across Dorfin stand groomed and quiet. Stableman Oswin moves
methodically from stall to stall. The Warden's Gate lies to the east; the
south stables are further west; the tack room is to the south.
""",
    ambient=["A horse nuzzles your sleeve.",
             "Oswin mutters reassuringly to a nervous roan."])

W["south_stables"] = room(
    ExteriorRoom, "The South Stables",
    """|yThe working wing of the paddock — pack animals and common mounts.|n

Less polished than the north stables, but clean and functional. The north
stables are to the east; the stable yard lies to the south.
""")

W["tack_room"] = room(
    ExteriorRoom, "The Tack Room",
    """|wEvery wall is hung with saddles, bridles, and riding gear.|n

The smell of leather oil is thick enough to taste. The north stables are
to the north; the stable yard lies to the east.
""")

W["stable_yard"] = room(
    ExteriorRoom, "The Stable Yard",
    """|yAn open cobbled yard where horses are walked, watered, and traded.|n

Groom Pip darts between animals with infinite pockets full of carrots. The
tack room is to the west; the south stables lie to the north.
""",
    ambient=["Groom Pip produces a carrot and holds it out.",
             "A merchant haggles over a spotted mare."])

#  2x2 grid connections
link(W["north_stables"], "west",  W["south_stables"], "east")   # NW <-> NE
link(W["tack_room"],     "east",  W["stable_yard"],   "west")   # SW <-> SE
link(W["north_stables"], "south", W["tack_room"],     "north")  # NW <-> SW
link(W["south_stables"], "south", W["stable_yard"],   "north")  # NE <-> SE

link(W["wardens_gate"], "west", W["north_stables"], "east")


# ---------------------------------------------------------------------------
# SECTION 4 — Garden of Remembrance (/4)
#
#   Memorial Garden (NW) <-e/w-> Old Graves (NE)
#          n/s                        n/s
#   Reflecting Pool (SW) <-e/w-> Willow Grove (SE)
#
#   Entry: South Gate --south--> Memorial Garden (NW, north side of grid)
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Exterior: Garden of Remembrance (/4) ---|n")

W["memorial_garden"] = room(
    ExteriorRoom, "The Memorial Garden",
    """|gCarefully tended flower beds surround small monuments to fallen heroes.|n

Groundskeeper Enid knows the name on every stone. The South Gate lies to the
north; the Old Graves are to the east; the Reflecting Pool is to the south.
""",
    ambient=["Enid pauses at one stone longer than the others."])

W["old_graves"] = room(
    ExteriorRoom, "The Old Graves",
    """|wWeathered headstones lean at varied angles. The inscriptions are cryptic.|n

The oldest stones predate the founding records. At night, something stirs here.
The Memorial Garden lies to the west; the Willow Grove is to the south.
""",
    is_safe=False,
    desc_night="|wThe shadows between the stones are wrong at night. Don't look directly at them.|n",
    ambient=["Fresh flowers sit on one old grave. No one saw who left them."])

W["reflecting_pool"] = room(
    ExteriorRoom, "The Reflecting Pool",
    """|cA still, dark pool surrounded by weeping willows.|n

Those who stare long enough claim to see things. A hooded figure sits motionless
at the water's edge and has never been seen to move. The Memorial Garden is to
the north; the Willow Grove lies to the east.
""",
    ambient=["The surface ripples once. There is no wind.",
             "The hooded figure is exactly where it was when you arrived."])

W["willow_grove"] = room(
    ExteriorRoom, "The Willow Grove",
    """|gAncient willows cluster here, branches trailing the ground.|n

The air smells of damp earth and something faintly sweet. Rare plants grow here
that grow nowhere else in Awtown. The Old Graves lie to the north; the Reflecting
Pool is to the west.
""",
    ambient=["A rare herb grows at the base of one willow, overlooked by most."])

#  2x2 grid connections
link(W["memorial_garden"], "east",  W["old_graves"],      "west")   # NW <-> NE
link(W["reflecting_pool"], "east",  W["willow_grove"],    "west")   # SW <-> SE
link(W["memorial_garden"], "south", W["reflecting_pool"], "north")  # NW <-> SW
link(W["old_graves"],      "south", W["willow_grove"],    "north")  # NE <-> SE

link(W["south_gate"], "south", W["memorial_garden"], "north")


# ---------------------------------------------------------------------------
# SECTION 5 — Founder's Walk (E-W spine road)
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Roads: Founder's Walk ---|n")

W["founders_walk_west"] = room(
    RoadRoom, "Along Founder's Walk (West)",
    """|cThe western stretch of Awtown's grandest road.|n

The cobblestones are swept clean each morning. The Warden's Gate is to the west.
Administrative buildings line both sides of the road.
""",
    ambient=["A town guard nods as they pass on their rounds.",
             "Two officials argue quietly, stopping when they notice you."])

W["founders_walk_central"] = room(
    RoadRoom, "Along Founder's Walk (Central)",
    """|cThe heart of Founder's Walk, where the road widens slightly.|n

Roads branch south toward the Temple. The sound of hammers drifts from the east.
""",
    ambient=["A pilgrim hurries south toward the Temple.",
             "One cobblestone was replaced slightly wrong. Someone knows who did it."])

W["founders_walk_east"] = room(
    RoadRoom, "Along Founder's Walk (East)",
    """|cThe eastern stretch of Founder's Walk, near the Founders' own offices.|n

The Workshop and Parlour are to the north. The Herald's Hall lies further east.
""",
    ambient=["Machine oil drifts faintly from Hammerfall's Workshop.",
             "Someone exits Malgrave's Parlour looking noticeably more motivated."])

link(W["wardens_gate"],          "east", W["founders_walk_west"],    "west")
link(W["founders_walk_west"],    "east", W["founders_walk_central"], "west")
link(W["founders_walk_central"], "east", W["founders_walk_east"],    "west")


# ---------------------------------------------------------------------------
# SECTION 6 — North Row: Administrative District
#  Runs east-west above Founder's Walk.
#  FW West --north--> Notary (west end of row)
#  FW Central --north--> Artificer's Post (east end of row, creates a loop)
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Buildings: Administrative District ---|n")

W["notary_office"] = room(
    Room, "The Notary's Office",
    """|wA cramped but tidy office. The smell of ink and wax seals never leaves.|n

Notary Prim sits behind a desk stacked with documents, ink-stained to the elbows.
Founder's Walk is to the south; the Messenger's Roost lies to the east.
""",
    ambient=["The scratch of Prim's quill is the only sound.",
             "A fresh wax seal cools on the desk."])

W["messengers_roost"] = room(
    Room, "The Messenger's Roost",
    """|wA small, busy room that smells of feathers and leather satchels.|n

Postmaster Wren never stands still for more than two seconds. The Notary's
Office is to the west; the Shadow Chamber lies to the east.
""",
    ambient=["A runner bursts in, hands off a packet, and is gone.",
             "A bird fixes you with one bright eye."])

W["shadow_chamber"] = room(
    Room, "The Shadow Chamber",
    """|wA plain, unremarkable room most people walk past without noticing.|n

A round table. Six chairs. No windows. The silence here is occupied, not empty.
The door locks from the inside. The Messenger's Roost is to the west; the
Steward's Hall lies to the east.
""",
    no_teleport=True, light_level=2,
    ambient=["The silence in here is complete."])

W["stewards_hall"] = room(
    Room, "The Steward's Hall",
    """|wA tidy administrative office of bulletin boards and supply manifests.|n

Steward Pell moves with the efficiency of someone who has turned organization
into an art form. The Shadow Chamber is to the west; the Artificer's Post
lies to the east.
""",
    ambient=["Pell crosses something off a list and adds two more things."])

W["artificers_post"] = room(
    Room, "The Artificer's Post",
    """|wA bright, cluttered workshop where broken things come to be fixed.|n

Tinker Cogsworth talks constantly. Apprentice Sprocket watches something bubble
in the corner with growing concern. Founder's Walk is to the south; the
Steward's Hall lies to the west.
""",
    ambient=["Cogsworth finishes a sentence and immediately starts another.",
             "Something in the corner makes a sound it shouldn't."])

link(W["founders_walk_west"],    "north", W["notary_office"],    "south")
link(W["notary_office"],         "east",  W["messengers_roost"], "west")
link(W["messengers_roost"],      "east",  W["shadow_chamber"],   "west")
link(W["shadow_chamber"],        "east",  W["stewards_hall"],    "west")
link(W["stewards_hall"],         "east",  W["artificers_post"],  "west")
link(W["founders_walk_central"], "north", W["artificers_post"],  "south")


# ---------------------------------------------------------------------------
# SECTION 7 — Founders' Offices
#  Hammerfall is north of FW East.
#  Malgrave is east of Hammerfall (same north row).
#  Oldmere's Study connects south to Market Row East.
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Buildings: Founders' Offices ---|n")

W["hammerfall_workshop"] = room(
    FounderRoom, "Hammerfall's Workshop",
    """|rAbsolute chaos. Every surface covered in half-built devices and diagrams.|n

Marro Hammerfall doesn't look up. He's elbow-deep in something important. The
smell of oil and hot metal is immediate. Founder's Walk is to the south;
Malgrave's Parlour lies to the east.
""",
    ambient=["Hammerfall grunts. Greeting or approval — hard to say.",
             "Something hisses, spins, and stops. He doesn't react."])

W["malgraves_parlour"] = room(
    FounderRoom, "Malgrave's Parlour",
    """|yA warm, welcoming office that always feels slightly busy.|n

A |w"You've Got This!"|n pennant hangs slightly crooked above the door. Jorvyn
Malgrave is already looking at you like he was expecting you. Hammerfall's
Workshop lies to the west.
""",
    ambient=["Malgrave straightens papers, unsatisfied, and straightens them again.",
             "The pennant sways. There is no draft."])

W["oldmeres_study"] = room(
    FounderRoom, "Oldmere's Study",
    """|bFloor-to-ceiling shelves of books, maps, scrolls, and documents.|n

A single clear desk sits at the center, always with an open book. Joleth Oldmere
looks up with the expression of someone who just remembered something they needed
to tell you forty-five minutes ago. Market Row is to the south.
""",
    ambient=["Oldmere finds the exact book she wants without looking.",
             "A stack of scrolls shifts. Nothing falls. The system holds."])

link(W["founders_walk_east"], "north", W["hammerfall_workshop"], "south")
link(W["hammerfall_workshop"],"east",  W["malgraves_parlour"],   "west")


# ---------------------------------------------------------------------------
# SECTION 8 — Herald's Hall, Assembly Hall, Outfitter's Rest
#  Chain: FW East --east--> Herald's Hall --east--> Grand Gate --east--> Wayfarers' Green
#  Herald's Hall --south--> Assembly Hall
#  Assembly Hall --west--> Outfitter's Rest --west--> Oldmere's Study
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Buildings: Entry District ---|n")

W["heralds_hall"] = room(
    Room, "The Herald's Hall",
    """|yHigh ceilings, bright torchlight, and a roaring fireplace welcome you.|n

This is the first room most adventurers see inside Awtown. A large |wQuest Board|n
dominates one wall. Herald Bramwick is already halfway across the room toward you.
Founder's Walk is to the west; the Grand Gate lies to the east.

|c[Quest Board here. Town maps from Scribe Dilly.]|n
""",
    ambient=["Bramwick greets a new arrival by name before they've said a word.",
             "A fresh notice has been pinned to the Quest Board.",
             "The fire crackles. Someone has just stoked it."])

W["assembly_hall"] = room(
    Room, "The Assembly Hall",
    """|wA grand vaulted chamber of stone and dark wood.|n

Rows of benches face a raised speaking dais. Portraits of the three Founders
regard the room with varying degrees of approval. The Herald's Hall is to
the north; the Outfitter's Rest lies to the west.
""",
    ambient=["Your footsteps echo strangely under the vaulted ceiling.",
             "Malgrave's portrait has been slightly reframed. Nobody admits it."])

W["outfitters_rest"] = room(
    Room, "The Outfitter's Rest",
    """|yA cozy shop with overstuffed chairs and warm golden light.|n

Shopkeep Marta fusses over every customer. New adventurers may claim a free
starter kit here — clothing, torch, rations. The Assembly Hall is to the east;
Oldmere's Study lies to the west.

|c[New characters may claim a free starter kit here, once.]|n
""",
    rest_bonus=1,
    ambient=["Marta presses travel biscuits into someone's hand before they can refuse.",
             "The chairs here are extremely comfortable. This is not an accident."])

link(W["founders_walk_east"], "east",  W["heralds_hall"],    "west")
link(W["heralds_hall"],       "east",  W["grand_gate"],      "west")
link(W["heralds_hall"],       "south", W["assembly_hall"],   "north")
link(W["assembly_hall"],      "west",  W["outfitters_rest"], "east")
link(W["outfitters_rest"],    "west",  W["oldmeres_study"],  "east")


# ---------------------------------------------------------------------------
# SECTION 9 — Templegate Lane & Temple of the Eternal Flame (/4)
#
#   Nave (NW)       <-e/w-> Sanctuary (NE)
#      n/s                       n/s
#   Vestry (SW)     <-e/w-> Bell Tower (SE)
#
#   Entry: Templegate Lane South --south--> Nave (NW, north-west corner)
#   Oldmere's Study connects south to Market Row East.
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Roads & Temple: Templegate Lane ---|n")

W["templegate_lane_north"] = room(
    RoadRoom, "Templegate Lane (North)",
    """|yA short, well-worn stretch running south off Founder's Walk.|n

Small lanterns flicker at the junction. The faint smell of incense drifts up
from the south. Founder's Walk is to the north.
""",
    ambient=["A pilgrim moves past in silence, eyes forward.",
             "A lantern overhead gutters and steadies."])

W["templegate_lane_south"] = room(
    RoadRoom, "Templegate Lane (South)",
    """|yThe lane widens slightly as it approaches the Temple doors.|n

Carved pillars mark the entrance to the south. A donation bowl sits unattended
by the door, reliably and mysteriously full. Market Row branches to the east.
""")

link(W["founders_walk_central"],  "south", W["templegate_lane_north"], "north")
link(W["templegate_lane_north"],  "south", W["templegate_lane_south"], "north")

W["temple_nave"] = room(
    TempleRoom, "The Temple — The Nave",
    """|wA soaring vaulted ceiling rises above rows of worn pews.|n

At the altar, an eternal flame burns in a brass bowl that has never been empty.
High Priest Edwyn Lux moves between the pews with unhurried purpose. The lane
is to the north; the Sanctuary lies to the east; the Vestry is to the south.
""",
    rest_bonus=1,
    ambient=["The eternal flame flickers once, then burns steady.",
             "A quiet prayer is murmured somewhere in the pews."])

W["temple_sanctuary"] = room(
    TempleRoom, "The Temple — The Sanctuary",
    """|cQuiet and candlelit, this wing smells of herbs and clean linen.|n

Sister Sera hums softly as she works. Whatever the injury, things will improve
here. They usually do. The Nave is to the west; the Bell Tower is to the south.
""",
    rest_bonus=2,
    ambient=["Sister Sera changes a dressing with practiced, gentle hands.",
             "The candles here never seem to burn down."])

W["temple_vestry"] = room(
    TempleRoom, "The Temple — The Vestry",
    """|wRobes hang in precise rows. Prayer texts stacked by faith and use.|n

Brother Aldwin sits at his desk and will not look up until you speak. Cleric
training happens here, on Aldwin's terms. The Nave is to the north; the Bell
Tower lies to the east.
""",
    trainer_npc=None,
    ambient=["Aldwin's quill stops. He reads what he wrote. He continues."])

W["temple_bell_tower"] = room(
    TempleRoom, "The Temple — The Bell Tower",
    """|wA narrow staircase leads to this small, wind-swept chamber.|n

The bell hasn't rung in years — by choice. Paladin-Warden Thane Dusk trains
here. He will teach others. He expects dedication. The Sanctuary is to the
north; the Vestry lies to the west.
""",
    is_outdoor=True, light_level=5, trainer_npc=None,
    ambient=["The wind up here is constant and cold.",
             "Dusk's sword returns to guard so smoothly the motion seems continuous."])

#  2x2 grid connections
link(W["temple_nave"],      "east",  W["temple_sanctuary"],  "west")   # NW <-> NE
link(W["temple_vestry"],    "east",  W["temple_bell_tower"], "west")   # SW <-> SE
link(W["temple_nave"],      "south", W["temple_vestry"],     "north")  # NW <-> SW
link(W["temple_sanctuary"], "south", W["temple_bell_tower"], "north")  # NE <-> SE

link(W["templegate_lane_south"], "south", W["temple_nave"], "north")


# ---------------------------------------------------------------------------
# SECTION 10 — Market Row (E-W middle road)
#  West end off Templegate Lane South.
#  Market Row East connects north to Oldmere's Study.
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Roads: Market Row ---|n")

W["market_row_west"] = room(
    RoadRoom, "Market Row (West)",
    """|yThe western stretch of Awtown's busiest commercial road.|n

The smell of fresh bread drifts from the Hearthstone to the north. Templegate
Lane branches to the west. The Vault of Gold lies to the south.
""",
    ambient=["A merchant haggles. Both parties seem to be enjoying it.",
             "The smell of fresh bread is genuinely distracting."])

W["market_row_east"] = room(
    RoadRoom, "Market Row (East)",
    """|yThe eastern stretch of Market Row, near the bank district.|n

The clink of gold from the Vault carries clearly. Oldmere's Study is to the
north; the Crystal Repository lies to the south.
""",
    ambient=["Someone exits the Vault looking satisfied. Briefly."])

link(W["templegate_lane_south"], "east",  W["market_row_west"], "west")
link(W["market_row_west"],       "east",  W["market_row_east"], "west")
link(W["market_row_east"],       "north", W["oldmeres_study"],  "south")


# ---------------------------------------------------------------------------
# SECTION 11 — Financial District: Vault, Assay Office, Crystal Repository
#  South of Market Row, chained east.
#  Vault south of MR West; Crystal south of MR East (creates a loop).
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Buildings: Financial District ---|n")

W["vault_of_gold"] = room(
    Room, "The Vault of Gold",
    """|wA squat stone building with a heavy iron door and barred windows.|n

Banker Guildred Copperpot stands at the counter, precise as a decimal point.
Vault Guard Holt stands by the door, silent as an axiom. Market Row is to
the north; the Assay Office lies to the east.
""",
    ambient=["Copperpot recounts a stack of coins. Same total. He recounts again.",
             "Holt has not moved in some time."])

W["assay_office"] = room(
    Room, "The Assay Office",
    """|wA clean, well-lit room of scales, magnifying lenses, and testing trays.|n

Assayer Dunt has never given an incorrect valuation. He will not start today.
The Vault of Gold is to the west; the Crystal Repository lies to the east.
""",
    ambient=["Dunt holds a gem to the light and makes a sound of appreciation."])

W["crystal_repository"] = room(
    CourtyardRoom, "The Crystal Repository",
    """|cAn open stone courtyard enclosed by tall walls.|n

At its center, a humming crystal formation pulses with soft light. Archivist
Quellan whispers to the crystals when he thinks no one is watching. Market Row
is to the north; the Assay Office lies to the west.
""",
    ambient=["The crystals hum at a frequency you feel more than hear.",
             "Quellan whispers to the central crystal. It pulses in response."])

link(W["market_row_west"],  "south", W["vault_of_gold"],      "north")
link(W["vault_of_gold"],    "east",  W["assay_office"],       "west")
link(W["assay_office"],     "east",  W["crystal_repository"], "west")
link(W["market_row_east"],  "south", W["crystal_repository"], "north")


# ---------------------------------------------------------------------------
# SECTION 12 — Hearthstone Inn (/4)
#
#   Common Room (NW) <-e/w-> Kitchen (NE)
#          n/s                    n/s
#   Private Snug (SW)<-e/w-> Cellar (SE)
#
#   Entry: Market Row West --north--> Common Room (NW, street-facing)
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Buildings: Hearthstone Inn (/4) ---|n")

W["common_room"] = room(
    InnRoom, "The Hearthstone — The Common Room",
    """|yThe main tavern floor: crowded benches, a roaring hearth, the bar.|n

Barkeep Finn serves without spilling a drop while holding three conversations.
Lute-player Cobble is in the corner doing something technically musical. Market
Row is to the south; the Kitchen lies to the east; the Private Snug is south.
""",
    rest_bonus=2,
    ambient=["Finn slides a drink down the bar. It stops exactly right.",
             "Cobble hits a wrong note, recovers, pretends it was intentional.",
             "Two locals argue about something that happened fifteen years ago."])

W["the_kitchen"] = room(
    InnRoom, "The Hearthstone — The Kitchen",
    """|rCook Darra runs this kitchen with iron efficiency and zero tolerance.|n

The food is exceptional. The atmosphere for uninvited visitors is not. Darra
will share her opinions about this, at volume. The Common Room is to the west;
the Cellar lies to the south.
""",
    ambient=["Something sizzles. The smell is outstanding.",
             "Darra notices you looking. Her expression says: wrong room."])

W["private_snug"] = room(
    InnRoom, "The Hearthstone — The Private Snug",
    """|wCurtained booths line this quieter back room.|n

For private meetings, shady deals, and eavesdropping. A Suspicious Figure
occupies one booth — different figure than last week, same booth. The Common
Room is to the north; the Cellar lies to the east.
""",
    light_level=2,
    ambient=["Someone speaks very quietly. You catch one word: 'tonight.'"])

W["the_cellar"] = room(
    InnRoom, "The Hearthstone — The Cellar",
    """|wStone stairs lead down to a barrel-lined cellar, dark and cold.|n

There is, behind the oldest barrels in the back corner, a door that shouldn't
be here. No one who works here will discuss it. The Kitchen is to the north;
the Private Snug lies to the west.
""",
    light_level=1, is_safe=False,
    ambient=["Something drips in the dark.",
             "The door in the corner is still there."])

#  2x2 grid connections
link(W["common_room"],   "east",  W["the_kitchen"],  "west")   # NW <-> NE
link(W["private_snug"],  "east",  W["the_cellar"],   "west")   # SW <-> SE
link(W["common_room"],   "south", W["private_snug"], "north")  # NW <-> SW
link(W["the_kitchen"],   "south", W["the_cellar"],   "north")  # NE <-> SE

link(W["market_row_west"], "north", W["common_room"], "south")


# ---------------------------------------------------------------------------
# SECTION 13 — Warden's Way (N-S road) & West District Buildings
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Roads: Warden's Way ---|n")

W["wardens_way_north"] = room(
    RoadRoom, "Along Warden's Way (North)",
    """|5A quieter road, favored by craftsmen avoiding Founder's Walk.|n

The paving stones are uneven but solid. Founder's Walk is to the north; the
central stretch lies to the south. The Warden's Barracks are to the west.
""",
    ambient=["A craftsman passes with a bundle of timber."])

W["wardens_way_central"] = room(
    RoadRoom, "Along Warden's Way (Central)",
    """|5The middle stretch of Warden's Way — lighter foot traffic.|n

The Round Table meeting room is to the west. The distant ring of the forge
drifts from the south. Craftsman's Road lies to the south.
""")

link(W["founders_walk_west"],   "south", W["wardens_way_north"],   "north")
link(W["wardens_way_north"],    "south", W["wardens_way_central"], "north")

caller.msg("\n|c--- Buildings: West District ---|n")

W["deed_hall"] = room(
    Room, "The Deed Hall",
    """|wA narrow room lined with filing cabinets and land registry scrolls.|n

Registrar Voss can produce any document within thirty seconds. Warden's Way
is to the east; the Quartermaster's Cache lies to the north.
""",
    ambient=["The filing system is either genius or deeply personal."])

W["quartermaster_cache"] = room(
    Room, "The Quartermaster's Cache",
    """|wA tidy storeroom of boxes, crates, and meticulously labeled barrels.|n

Quartermaster Hobb requires a signed manifest in triplicate. The Deed Hall
is to the south; the Pantry lies to the east.
""",
    ambient=["Hobb checks a list, makes a mark, checks it again."])

W["pantry"] = room(
    Room, "The Pantry",
    """|wA small, cool room with stone walls and a heavy door.|n

Nan keeps everything orderly and sells rations without eye contact. This is
not unfriendliness. It is efficiency. The Quartermaster's Cache is to the west;
the Supply Room lies to the east.
""",
    ambient=["Nan straightens a row of ration packs that were already straight."])

W["supply_room"] = room(
    Room, "The Supply Room",
    """|wA general overflow storage room. Things end up here when there's nowhere else.|n

Stock Boy Fen has a system. He will explain it. The explanation will not help.
The Pantry is to the west; Warden's Way is to the south.
""",
    ambient=["A crate is labelled 'MISC — DO NOT OPEN'. Fen doesn't remember why."])

W["round_table"] = room(
    Room, "The Round Table",
    """|yA small comfortable room centered on an actual round table.|n

Guild Registrar Brom will mention the table more than once. It is genuinely
round. He made a point of it. Warden's Way is to the east; the Posting Board
lies to the south.
""",
    ambient=["Brom glances at the table with quiet satisfaction."])

W["posting_board"] = room(
    Room, "The Posting Board",
    """|yA public room dominated by an enormous cork board.|n

Board-Keeper Sal will post anything for a coin, tear it down for two — no
opinions expressed. The Round Table is to the north; Warden's Way is to the east.
""",
    ambient=["Someone pins a new notice. Sal doesn't look up.",
             "A wanted poster at the edge catches your eye."])

W["washhouse_north"] = room(
    Room, "The Washhouse (North)",
    """|cWarm water, clean towels, and soap that smells of lavender.|n

A surprising luxury. The dirt of the road comes off here. Warden's Way is
to the west; the Washhouse South lies below on the southern stretch.
""",
    rest_bonus=1,
    ambient=["Someone leaves looking measurably better than when they arrived."])

W["washhouse_south"] = room(
    Room, "The Washhouse (South)",
    """|cThe southern washhouse — same warm water, same lavender soap.|n

For the convenience of crafting district workers who carry more industrial grime.
Warden's Way is to the west.
""",
    rest_bonus=1)

link(W["wardens_way_north"],   "west",  W["deed_hall"],           "east")
link(W["deed_hall"],           "north", W["quartermaster_cache"], "south")
link(W["quartermaster_cache"], "east",  W["pantry"],              "west")
link(W["pantry"],              "east",  W["supply_room"],         "west")
link(W["supply_room"],         "south", W["wardens_way_north"],   "north")   # loop back
link(W["wardens_way_central"], "west",  W["round_table"],         "east")
link(W["round_table"],         "south", W["posting_board"],       "north")
link(W["wardens_way_north"],   "east",  W["washhouse_north"],     "west")
link(W["wardens_way_central"], "east",  W["washhouse_south"],     "west")


# ---------------------------------------------------------------------------
# SECTION 14 — Warden's Barracks
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Buildings: Warden's Barracks ---|n")

W["wardens_barracks"] = room(
    Room, "The Warden's Barracks",
    """|wA long practical room of leather polish and cold iron.|n

Bunk frames line one wall; weapons racks line the other. Sergeant Dorn runs
drills here affectionately. The Warden's Gate is to the north; Warden's Way
lies to the east.
""",
    trainer_npc=None,
    ambient=["Guard Recruit Pip polishes a helmet clearly too large for him.",
             "Sergeant Dorn corrects someone's stance with one word and a look."])

link(W["wardens_gate"],     "south", W["wardens_barracks"],  "north")
link(W["wardens_barracks"], "east",  W["wardens_way_north"], "west")


# ---------------------------------------------------------------------------
# SECTION 15 — Craftsman's Road (E-W bottom road)
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Roads: Craftsman's Road ---|n")

W["craftsmans_road_west"] = room(
    RoadRoom, "Craftsman's Road (West)",
    """|rThe western stretch of the southern road — dusty and purposeful.|n

The ring of hammers is never far. Warden's Way is to the north; the eastern
stretch lies ahead. The Watchtower is to the west; the Herbalist's Nook is
to the south.
""",
    ambient=["A cart loaded with raw timber rumbles past.",
             "The smell of hot metal is stronger here."])

W["craftsmans_road_east"] = room(
    RoadRoom, "Craftsman's Road (East)",
    """|rThe eastern stretch, near the forge complex and the South Gate.|n

The Grand Forge's heat can be felt from here on warm days. The South Gate
lies to the east; the Iron Forge is to the south.
""",
    ambient=["Sparks drift briefly from somewhere in the forge complex."])

link(W["wardens_way_central"],  "south", W["craftsmans_road_west"], "north")
link(W["craftsmans_road_west"], "east",  W["craftsmans_road_east"], "west")
link(W["craftsmans_road_east"], "east",  W["south_gate"],           "west")


# ---------------------------------------------------------------------------
# SECTION 16 — Grand Forge (/4)
#
#   Iron Forge (NW)  <-e/w-> Workbench (NE)
#          n/s                    n/s
#   Loom Room (SW)   <-e/w-> Alchemist's Corner (SE)
#
#   Entry: Craftsman's Road East --south--> Iron Forge (NW, road-facing corner)
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Buildings: Grand Forge (/4) ---|n")

W["iron_forge"] = room(
    CraftingRoom, "The Grand Forge — The Iron Forge",
    """|rA thundering forge with massive bellows and an ever-burning flame.|n

Master Smith Brondal Ironmark works at the central anvil with total certainty.
Craftsman's Road is to the north; the Workbench lies to the east; the Loom
Room is to the south.
""",
    trainer_npc=None,
    ambient=["The hammer falls. The metal rings. This happens again.",
             "Brondal examines a blade edge and makes a sound of approval."])

W["workbench"] = room(
    CraftingRoom, "The Grand Forge — The Workbench",
    """|yFragrant cedar and leather fill this bright workshop.|n

Bows, shields, and saddles in progress cover every surface. Carpenter Wynn
hums cheerfully. The Iron Forge is to the west; the Alchemist's Corner lies
to the south.
""",
    trainer_npc=None,
    ambient=["Wynn whistles something tuneless and cheerful.",
             "The smell of fresh-cut cedar is exceptional."])

W["loom_room"] = room(
    CraftingRoom, "The Grand Forge — The Loom Room",
    """|mThe quietest workshop — a relative term here.|n

Weaver Mira works with a focus that treats a single misaligned thread as a
personal failing. She has never had one. The Iron Forge is to the north; the
Alchemist's Corner lies to the east.
""",
    trainer_npc=None,
    ambient=["The loom moves with hypnotic rhythm.",
             "Mira holds cloth to the light, satisfied, then finds one flaw."])

W["alchemists_corner"] = room(
    CraftingRoom, "The Grand Forge — The Alchemist's Corner",
    """|gBubbling vials, impossible smells, and the scent of scorched eyebrow.|n

Alchemist Sable Dross works happily distracted, thinking about three other things
at once. The Workbench is to the north; the Loom Room lies to the west.
""",
    trainer_npc=None,
    ambient=["Something pops. Sable Dross doesn't look up.",
             "A vial changes color. Sable makes a note."])

#  2x2 grid connections
link(W["iron_forge"],    "east",  W["workbench"],          "west")   # NW <-> NE
link(W["loom_room"],     "east",  W["alchemists_corner"],  "west")   # SW <-> SE
link(W["iron_forge"],    "south", W["loom_room"],          "north")  # NW <-> SW
link(W["workbench"],     "south", W["alchemists_corner"],  "north")  # NE <-> SE

link(W["craftsmans_road_east"], "south", W["iron_forge"], "north")


# ---------------------------------------------------------------------------
# SECTION 17 — Tinker's Den
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Buildings: Tinker's Den ---|n")

W["tinkers_den"] = room(
    CraftingRoom, "The Tinker's Den",
    """|wGears, springs, lenses, and gadgets hang from every surface.|n

Cogwright Fenn could find any component by feel in the dark. Automaton Tick
sweeps the floor and occasionally says something surprisingly profound. The
Workbench is to the west; Cartographer's Den is to the south.
""",
    trainer_npc=None,
    ambient=["Tick sweeps past and makes a small sound that might be a greeting.",
             "Fenn produces exactly the part he needs without looking."])

link(W["workbench"],    "east",  W["tinkers_den"], "west")


# ---------------------------------------------------------------------------
# SECTION 18 — South Row
#  Herbalist's Nook is at the west end, accessed from Craftsman's Road West.
#  Row runs east: Herbalist → Apprentice → Study → Hermit → Cartographer
#  Cartographer connects north to Tinker's Den.
#  Alchemist's Corner connects south into Study Hall (forge above, hall below).
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Buildings: South Row ---|n")

W["herbalists_nook"] = room(
    Room, "The Herbalist's Nook",
    """|gBundles of drying herbs hang from the rafters. Jars crowd every shelf.|n

Hedge-Witch Morvaine is deciding whether you deserve her time. Craftsman's Road
is to the north; the Apprentice Hall lies to the east.
""",
    trainer_npc=None,
    ambient=["Something in a jar moves. Probably herbs.",
             "Morvaine makes a sound between a grunt and a diagnosis."])

W["apprentice_hall"] = room(
    TrainingRoom, "The Apprentice Hall",
    """|yA large room of practice dummies, training weapons, and battered desks.|n

Apprentice Rudd is already looking at you like he wants to spar. The
Herbalist's Nook is to the west; the Study Hall lies to the east; the
Alchemist's Corner is to the north.
""",
    trainer_npc=None,
    ambient=["Rudd squares up to a dummy and misses.",
             "Apprentice Yeva annotates a textbook, oblivious to the noise.",
             "Headmaster Orifel pinches the bridge of his nose and says nothing."])

W["study_hall"] = room(
    TrainingRoom, "The Study Hall",
    """|wRows of desks and chalkboards. The quieter sibling of the Apprentice Hall.|n

Scholar Bevin supervises with patient calm. Student Mop is asleep at a desk
and has somehow passed every assessment. The Apprentice Hall is to the west;
the Hermit's Hollow lies to the east.
""",
    ambient=["Student Mop is asleep. His notes are inexplicably excellent.",
             "Bevin corrects a diagram, pauses, and draws it better."])

W["hermits_hollow"] = room(
    Room, "The Hermit's Hollow",
    """|gThis room is inexplicably made to look like a woodland cave.|n

Moss on the walls. A small fire pit. A wooden stool. Nobody knows how this
ended up inside a town building. Nobody has asked. Sage Aldric Voss already
knows what you came to ask. The Study Hall is to the west; the Cartographer's
Den lies to the east.
""",
    light_level=2,
    ambient=["The fire burns without apparent fuel.",
             "Voss is looking at you. He was looking at you when you arrived."])

W["cartographers_den"] = room(
    Room, "The Cartographer's Den",
    """|wEvery surface covered in maps — rolled, pinned, framed, half-finished.|n

Mapper Izra works with a focus that borders on aggressive. She will sell the
best maps in Dorfin and pay for uncharted territory data. The Hermit's Hollow
is to the west; Tinker's Den lies to the north.
""",
    trainer_npc=None,
    ambient=["Izra marks a new detail on a map with a tiny, precise stroke."])

link(W["craftsmans_road_west"], "south", W["herbalists_nook"],   "north")
link(W["herbalists_nook"],      "east",  W["apprentice_hall"],   "west")
link(W["apprentice_hall"],      "east",  W["study_hall"],        "west")
link(W["study_hall"],           "east",  W["hermits_hollow"],    "west")
link(W["hermits_hollow"],       "east",  W["cartographers_den"], "west")
link(W["alchemists_corner"],    "south", W["study_hall"],        "north")
link(W["tinkers_den"],          "south", W["cartographers_den"], "north")


# ---------------------------------------------------------------------------
# SECTION 19 — Watchtower & The Precipice
#  Watchtower is west of Craftsman's Road West.
# ---------------------------------------------------------------------------
caller.msg("\n|c--- Buildings: Watchtower & Precipice ---|n")

W["watchtower"] = room(
    Room, "The Watchtower",
    """|wA narrow stone tower with a single winding staircase.|n

Watchman Teris notices things at distances that don't seem reasonable. He has
never explained how. Craftsman's Road is to the east; the Precipice is above.
""",
    trainer_npc=None,
    ambient=["Teris points at something distant. When you look, it's gone."])

W["the_precipice"] = room(
    LookoutRoom, "The Precipice",
    """|wA dramatic stone shelf juts out high above the surrounding land.|n

The wind is constant and clean. The full sweep of Dorfin unfolds below —
distant forests, dark hills, unknown waters. Adventurers come here before
setting out, and sometimes after, to remember why they left.
""",
    desc_night="""|wThe Precipice at night is something else entirely.|n

Awtown glows behind you. Dorfin stretches dark to the horizon, marked only by
distant fires and cold silver rivers. The wind is the same. You are not.
""",
    ambient=["The wind here is constant, cold, and clarifying.",
             "The view makes problems seem the correct size."])

link(W["craftsmans_road_west"], "west", W["watchtower"],    "east")
link(W["watchtower"],           "up",   W["the_precipice"], "down")


# ---------------------------------------------------------------------------
# FINAL REPORT
# ---------------------------------------------------------------------------

caller.msg("\n|y" + "="*60 + "|n")
caller.msg("|wAwtown world build complete!|n")
caller.msg("|y" + "="*60 + "|n")
caller.msg(f"\n|cTotal rooms built:|n {len(W)}")
caller.msg(f"\n|cNew player start:|n  {W['wayfarers_green'].key} {W['wayfarers_green'].dbref}")
caller.msg(f"|cDefault home:    |n  {W['heralds_hall'].key} {W['heralds_hall'].dbref}")
caller.msg("""
|yAdd to settings.py ConfigMap:|n

  START_LOCATION = "{start}"
  DEFAULT_HOME   = "{home}"

|yThen:|n
  1. Restart pod to pick up settings
  2. @tel {start}  — verify landing in Wayfarers' Green
  3. Walk the full map, check exits with 'look' in each room
  4. Build NPCs in world/npcs.py

|gDorfin awaits.|n
""".format(
    start=W["wayfarers_green"].dbref,
    home=W["heralds_hall"].dbref,
))
