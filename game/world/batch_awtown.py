"""
batch_awtown.py  —  DorfinMUD Awtown world builder
Run with:  @batchcode world.batch_awtown

Creates all 103 rooms, exits (including gated orange connectors), and NPCs.
"""

# HEADER

import evennia
from evennia import create_object
from evennia.objects.objects import DefaultExit

from typeclasses.rooms import AwtownRoom, AwtownRoadRoom, AwtownCourtyardRoom, AwtownExteriorRoom
from typeclasses.exits import AwtownGate, AwtownCityGate
from typeclasses.npcs import AwtownNPC

ROOM_TAG = "awtown_dbkey"
NPC_TAG  = "awtown_npc"

TC_MAP = {
    "road":      AwtownRoadRoom,
    "courtyard": AwtownCourtyardRoom,
    "exterior":  AwtownExteriorRoom,
    "building":  AwtownRoom,
}

# ── helpers ───────────────────────────────────────────────────────────────────

def _room(db_key):
    results = evennia.search_tag(db_key, category=ROOM_TAG)
    return results[0] if results else None

def _make_room(db_key, name, tc_key, desc):
    tc = TC_MAP.get(tc_key, AwtownRoom)
    existing = evennia.search_tag(db_key, category=ROOM_TAG)
    if existing:
        room = existing[0]
    else:
        room = create_object(tc, key=name)
        room.tags.add(db_key, category=ROOM_TAG)
    room.name = name
    room.db.desc = desc
    return room

def _exit_exists(room, direction):
    return any(ex.key == direction for ex in room.exits)

def _make_exit(from_key, direction, alias, to_key, tc=None, gate_name=None):
    tc = tc or DefaultExit
    fr = _room(from_key)
    to = _room(to_key)
    if not fr or not to:
        return None
    if _exit_exists(fr, direction):
        return next((e for e in fr.exits if e.key == direction), None)
    ex = create_object(tc, key=direction, location=fr, destination=to, aliases=[alias])
    if gate_name:
        ex.db.gate_name = gate_name
    return ex

def _pair_gates(from_key, from_dir, to_key, to_dir):
    fr = _room(from_key)
    to = _room(to_key)
    if not fr or not to:
        return
    a = next((e for e in fr.exits if e.key == from_dir), None)
    b = next((e for e in to.exits if e.key == to_dir), None)
    if a and b:
        a.db.pair = b
        b.db.pair = a

def _make_npc(db_key, name, desc, loc_key, role="generic", dialogue=None):
    location = _room(loc_key)
    if not location:
        return None
    existing = evennia.search_tag(db_key, category=NPC_TAG)
    if existing:
        npc = existing[0]
        if npc.location != location:
            npc.move_to(location, quiet=True)
        return npc
    npc = create_object(AwtownNPC, key=name, location=location)
    npc.tags.add(db_key, category=NPC_TAG)
    npc.db.desc = desc
    npc.db.npc_role = role
    if dialogue:
        npc.db.dialogue = dialogue
    return npc


# =============================================================================
# ROOM DATA  (db_key, player_name, tc_key, desc)
# =============================================================================

ROOM_DATA = [
    # ── FOUNDER'S WALK (12) ──────────────────────────────────────────────────
    ("fw_1","Along Founder's Walk","road",
     "The cobblestones of Founder's Walk are swept clean each morning. Warden's Way turns south here. "
     "The Warden's Barracks stand to the north; the Lamplighter's Nook glows warmly to the west."),
    ("fw_2","Along Founder's Walk","road",
     "A well-travelled stretch of Founder's Walk. The Warden's Gate stands solid to the north. "
     "The walk continues east toward the administrative heart of Awtown."),
    ("fw_3","Along Founder's Walk","road",
     "The Notary's Office occupies a neat doorway to the north. "
     "South, Lantern Road begins its run toward the forge district."),
    ("fw_4","Along Founder's Walk","road",
     "A busy stretch — clerks and messengers pass at most hours. "
     "The Messenger's Roost is just north; the flutter of birds is faintly audible. "
     "The Archivist's Anteroom is south, perpetually smelling of ink."),
    ("fw_5","Along Founder's Walk","road",
     "A quieter stretch. The Shadow Chamber's unmarked door sits to the north, easy to overlook by design."),
    ("fw_6","Along Founder's Walk","road",
     "Templegate Lane descends south toward the Temple precinct. "
     "The Steward's Hall occupies a tidy doorway to the north."),
    ("fw_7","Along Founder's Walk","road",
     "The Artificer's Post is to the north, its door usually propped open with a half-finished device. "
     "Templegate Lane descends south toward the Temple."),
    ("fw_8","Along Founder's Walk","road",
     "The Deed Hall anchors the north side, its door bearing the town's official seal. "
     "The Vault of Gold's squat stone face looks south, barred windows glinting."),
    ("fw_9","Along Founder's Walk","road",
     "Malgrave's Parlour occupies the north side, a warm light always visible through its windows. "
     "The walk is busy at all hours here — the administrative heart of Awtown."),
    ("fw_10","Along Founder's Walk","road",
     "Hammerfall's Workshop is to the north, identified by persistent clanking. "
     "Ondrel's Study sits quietly to the south. The Grand Gate is close."),
    ("fw_11","Along Founder's Walk","road",
     "The Grand Gate rises to the north. Above its arch: 'Leave lesser than you arrived.' "
     "The Herald's Hall lies to the northeast. A covered passage leads south."),
    ("fw_12","Along Founder's Walk","road",
     "The far eastern end of Founder's Walk, where the road ends at the Assembly Hall's broad front steps."),

    # ── WARDEN'S WAY (7) ─────────────────────────────────────────────────────
    ("ww_1","Along Warden's Way","road",
     "Warden's Way turns south off Founder's Walk here. A quieter road for craftsmen and those who "
     "know the side streets. The Guardroom door is just to the west."),
    ("ww_2","Along Warden's Way","road",
     "A mid-stretch of Warden's Way. The buildings press close; cobblestones are rougher here."),
    ("ww_3","Along Warden's Way","road",
     "The Washhouse offers its services to the west. An iron-banded gate to the east opens into "
     "the Cartographer's Den courtyard."),
    ("ww_4","Along Warden's Way","road",
     "Warden's Way bends briefly east here. The Pantry's plain door is to the west."),
    ("ww_5","Along Warden's Way","road",
     "A brief eastern jog in the road. The stones are worn smooth by years of wheelbarrow traffic."),
    ("ww_6","Along Warden's Way","road",
     "The second Washhouse occupies the western wall. The forge district is very close; "
     "the smell of hot metal is constant."),
    ("ww_7","Along Warden's Way","road",
     "The southern terminus of Warden's Way. The Watchtower's narrow door is to the west. "
     "A heavy gate to the south leads into the Lantern Court."),

    # ── TEMPLEGATE LANE (2) ──────────────────────────────────────────────────
    ("tl_1","Templegate Lane","road",
     "A short lane of well-worn stones connecting Founder's Walk to the Temple precinct below. "
     "Pilgrims move quietly in either direction at most hours."),
    ("tl_2","Templegate Lane","road",
     "The lower end of Templegate Lane. The Shrine of First Light glows softly to the east. "
     "The Humming Court lies to the south."),

    # ── LANTERN ROAD (6) ─────────────────────────────────────────────────────
    ("lr_1","The Lantern Road","road",
     "Small iron lanterns hang at regular intervals, their flames steady even in wind. "
     "The Quartermaster's Cache is to the west."),
    ("lr_2","The Lantern Road","road",
     "The Round Table is to the west; the Assay Office to the east. The lanterns burn a warm amber."),
    ("lr_3","The Lantern Road","road",
     "The Cartographer's Den courtyard is to the west; the Mapmaker's Rest just east."),
    ("lr_4","The Lantern Road","road",
     "The Posting Board's corkboard walls are visible through the east doorway. "
     "Lanterns line the road north and south."),
    ("lr_5","The Lantern Road","road",
     "The road branches east toward the Hearthstone Inn, and south toward the Iron Forge. "
     "The smell of food and the ring of metal compete pleasantly."),
    ("lr_6","The Lantern Road","road",
     "A short east-west spur. The Inn Counter's door is to the east, the Common Room audible through it."),

    # ── CRAFTSMAN'S ROAD (4) ─────────────────────────────────────────────────
    ("cr_1","Along Craftsman's Road","road",
     "The western end of Craftsman's Road. A heavy gate to the west leads into the Lantern Court. "
     "The Loom Room is just north; the road stretches east."),
    ("cr_2","Along Craftsman's Road","road",
     "The Study Hall is tucked to the south. Crates of raw materials line the northern wall."),
    ("cr_3","Along Craftsman's Road","road",
     "The Alchemist's Corner is north, occasionally marked by a plume of strange-coloured smoke. "
     "The Apprentice Hall to the south is the noisiest building on the road."),
    ("cr_4","Along Craftsman's Road","road",
     "The eastern end of Craftsman's Road. The Tinker's Den clicking is audible through the north wall. "
     "The Hermit's Hollow is improbably quiet to the south."),

    # ── GATE / ENTRY ROOMS (3) ───────────────────────────────────────────────
    ("gate_side","The Warden's Gate","road",
     "A smaller but sturdy gate in Awtown's western wall. Iron-banded oak stands solid between "
     "town and the paddock outside. Less ceremony than the Grand Gate — this is where locals pass."),
    ("gate_main","The Grand Gate","road",
     "Awtown's grand eastern entrance. Two iron-banded oak doors stand open during daylight, "
     "flanked by guards in polished town livery. "
     "Above the arch, carved deep: 'Leave lesser than you arrived.'"),
    ("gate_back","The South Gate","road",
     "A quiet gate at Awtown's southern end, rarely busy. The ironwork is entwined with carved vines "
     "— a tribute to the garden beyond. A young guard reads here more often than she watches the road."),

    # ── TEAL COURTYARDS (4) ──────────────────────────────────────────────────
    ("teal_ne","The Gilded Passage","courtyard",
     "A covered passage lit by warm amber lanterns, connecting Founder's Walk to the Outfitter's Rest. "
     "The walls are clean stone; the air smells faintly of cedar."),
    ("teal_main","The Cartographer's Den","courtyard",
     "An open stone courtyard enclosed by the buildings around it. A large covered drafting table "
     "sits at the centre, its canvas awning weighted against the wind. Rolled maps are pinned under stones."),
    ("teal_server","The Humming Court","courtyard",
     "A stone-flagged courtyard centred on a crystal formation that hums just below the threshold of hearing. "
     "The vibration is felt through the soles of your boots."),
    ("teal_sw","The Lantern Court","courtyard",
     "A low courtyard in Awtown's southern quarter, ringed by the town wall on two sides. "
     "Iron lanterns on poles keep it lit at all hours. A dramatic stone shelf juts out to the southwest."),
]


ROOM_DATA += [
    # ── DUSTY PADDOCK /4 (4) ─────────────────────────────────────────────────
    ("stables_nw","The North Stables","exterior",
     "Long rows of horse stalls line both sides. Breeds from across Dorfin fill the stalls. "
     "Tack hangs on wall hooks between them."),
    ("stables_ne","The South Stables","exterior",
     "The older wing of the paddock, used for working horses and pack animals. "
     "A water trough runs the length of the south wall."),
    ("stables_sw","The Tack Room","exterior",
     "Every wall is hung with saddles, bridles, halters, and riding gear. "
     "The smell of leather and saddle oil is overwhelming but pleasant."),
    ("stables_se","The Stable Yard","exterior",
     "A cobbled yard open to the sky for walking, watering, and trading horses. "
     "Grooms move with practised efficiency. The clatter of hooves on stone is constant."),

    # ── EASTERN COMMONS /4 (4) ───────────────────────────────────────────────
    ("commons_nw","The Wayfarers' Green","exterior",
     "A broad grassy common where travellers rest, camp, and swap stories before entering Awtown. "
     "The grass is well-worn in patches from generations of campfires."),
    ("commons_ne","The Cart Market","exterior",
     "Rotating stalls of travelling merchants spread wares on folding tables and from carts. "
     "The inventory changes day to day. The smell of spiced food competes with exotic goods."),
    ("commons_sw","The Crossroads Notice Board","exterior",
     "A large wooden board covered in notices, wanted posters, and regional news pinned three deep. "
     "This is where word from the wider world first reaches the road to Awtown."),
    ("commons_se","The Toll Stone","exterior",
     "An old carved stone marker at Awtown's eastern border, engraved with the town's founding date "
     "and a worn relief of the three Founders. The city gate lies to the south."),

    # ── TEMPLE /4 (4) ────────────────────────────────────────────────────────
    ("temple_nw","The Nave","building",
     "The main chamber of the Temple of the Eternal Flame. The ceiling is vaulted. "
     "Rows of worn pews face an altar where the Eternal Flame burns in a brass bowl — "
     "it has not gone out in recorded memory."),
    ("temple_ne","The Sanctuary","building",
     "A quieter, candlelit wing for healing and restoration. The air smells of herbs and clean linen. "
     "Sister Sera tends to the wounded here with more enthusiasm than precision."),
    ("temple_sw","The Vestry","building",
     "A room of robes, ritual objects, and prayer texts in careful order. Brother Aldwin's domain. "
     "Cleric training is available here."),
    ("temple_se","The Bell Tower","building",
     "The base of the Temple's bell tower, where stairs begin climbing upward. "
     "Paladin-Warden Thane Dusk trains students here amid worn practice equipment."),

    # ── HEARTHSTONE INN /4 (4) ───────────────────────────────────────────────
    ("tavern_nw","The Common Room","building",
     "The social heart of Awtown. Every bench is occupied, the hearth blazes, "
     "and the smell of roasting meat and spilled ale saturates everything pleasantly."),
    ("tavern_ne","The Kitchen","building",
     "Cook Darra's domain, run with iron efficiency and complete intolerance for uninvited visitors. "
     "The smell is extraordinary. The cellar stair is to the south."),
    ("tavern_sw","The Inn Counter","building",
     "A worn counter of dark wood, pigeonholes for keys on the wall behind it. "
     "Innkeeper Bess Copperladle takes lodging payments here with warm efficiency."),
    ("tavern_se","The Cellar","building",
     "Stone stairs lead down to a barrel-lined room, cool and dim. Casks of ale and wine are racked "
     "floor to ceiling. The east passage leads into the Humming Court."),

    # ── GRAND FORGE /4 (4) ───────────────────────────────────────────────────
    ("forge_nw","The Iron Forge","building",
     "A thundering forge with massive bellows. The heat is extraordinary. "
     "Master Smith Brondal Ironmark works here in near-silence with economical precision."),
    ("forge_ne","The Workbench","building",
     "A broad, fragrant space — cedar from woodwork, leather from saddle frames. "
     "Bows, shields, furniture, and tack are produced here. Carpenter Wynn narrates his projects."),
    ("forge_sw","The Loom Room","building",
     "The quietest of the Forge's four workshops. Weaver Mira works in near-silence, "
     "producing cloth of improbable fineness."),
    ("forge_se","The Alchemist's Corner","building",
     "Bubbling vials, labeled jars, and the aftermath of small explosions characterise this corner. "
     "Alchemist Sable Dross works in cheerful chaos."),

    # ── GARDEN OF REMEMBRANCE /4 (4) ─────────────────────────────────────────
    ("garden_nw","The Memorial Garden","exterior",
     "Carefully tended flower beds surround small stone monuments to fallen adventurers. "
     "The groundskeeper's care is evident in every trimmed edge."),
    ("garden_ne","The Old Graves","exterior",
     "Weathered headstones from Awtown's earliest days. The inscriptions are cryptic and old. "
     "At night something moves among these stones — unsettling even within the walls."),
    ("garden_sw","The Reflecting Pool","exterior",
     "A still, dark pool surrounded by weeping willows. The water does not stir even in wind. "
     "Rumoured to show visions. The Watcher stands here always, never speaking."),
    ("garden_se","The Willow Grove","exterior",
     "Ancient willows crowd this corner of the garden, their branches forming a curtained space. "
     "Rare herbs grow in the shadows."),
]


ROOM_DATA += [
    # ── SINGLE BUILDINGS — North of Founder's Walk (10) ──────────────────────
    ("warden_barracks","The Warden's Barracks","building",
     "A long, practical room smelling of leather polish and cold iron. Bunk frames and weapons racks "
     "line opposite walls. A duty roster and wanted-notice board hang beside the door."),
    ("notary","The Notary's Office","building",
     "A cramped but tidy office. Deeds, contracts, witnessed oaths, and official stamps cover every surface. "
     "The smell of ink and wax seals never fully leaves."),
    ("messenger_roost","The Messenger's Roost","building",
     "A small, busy room smelling of feathers and leather satchels. Messenger birds perch on racks. "
     "Runners come and go constantly."),
    ("shadow_chamber","The Shadow Chamber","building",
     "A plain room with a round table and six chairs, no windows, no decoration. Used by town guard "
     "leadership and, unofficially, by the local Thieves' Guild liaison."),
    ("stewards_hall","The Steward's Hall","building",
     "A tidy administrative office where the town's logistics are managed. Bulletin boards, ledgers, "
     "and supply manifests cover every surface."),
    ("artificer_post","The Artificer's Post","building",
     "A bright, cluttered workshop where broken things are fixed. Magical items, mundane tools, "
     "and odd contraptions in various states of repair line the walls."),
    ("deed_hall","The Deed Hall","building",
     "A narrow room lined with filing cabinets and land registry scrolls. Every plot of land in Awtown "
     "has a record here. Dry as dust, but surprisingly important."),
    ("malgraves_parlour","Malgrave's Parlour","building",
     "A warm, welcoming office that always feels slightly busy. Comfortable chairs face a desk covered "
     "in notes and schedules. A 'You've Got This!' pennant hangs slightly crooked above the door."),
    ("hammerfall_workshop","Hammerfall's Workshop","building",
     "Absolute chaos. Every surface is covered in half-built devices, tools, spare parts, and diagrams. "
     "The smell of oil and hot metal is intense. Marro Hammerfall is always elbow-deep in something."),
    ("heralds_hall","The Herald's Hall","building",
     "The first room most adventurers see inside Awtown. High ceilings, bright torchlight, a roaring hearth. "
     "A large Quest Board dominates one wall; town maps are available here."),

    # ── WEST DEAD-ENDS (2) ────────────────────────────────────────────────────
    ("lamplighters_nook","The Lamplighter's Nook","building",
     "A small alcove built into the town wall, smelling of hot wax and lamp oil. "
     "Racks of candles and lanterns line every surface. Always lit, even on the darkest nights."),
    ("guardroom","The Guardroom","building",
     "A plain utilitarian room smelling of leather and cold stew. Off-duty guards play cards at a "
     "battered table. A pinboard bristles with wanted notices."),

    # ── EAST END (1) ─────────────────────────────────────────────────────────
    ("assembly_hall","The Assembly Hall","building",
     "A grand vaulted chamber for town meetings and formal ceremonies. Rows of benches face a raised dais. "
     "Portraits of the three Founders hang on the walls."),

    # ── INTERIOR DEAD-ENDS (6) ────────────────────────────────────────────────
    ("archivists_anteroom","The Archivist's Anteroom","building",
     "Shelves stacked with overflowing ledgers and correspondence waiting to be filed. "
     "The room perpetually smells of ink and mild panic."),
    ("assay_office","The Assay Office","building",
     "A clean, well-lit room with precision scales, magnifying lenses, and testing reagents. "
     "Assayer Dunt conducts all valuations with complete impartiality."),
    ("mapmakers_rest","The Mapmaker's Rest","building",
     "A narrow room with chairs and a tall map case. Travelling cartographers copy charts here. "
     "A rumour board near the door catches things the official boards won't print."),
    ("posting_board","The Posting Board","building",
     "A room dominated by an enormous cork board covered in notices and wanted postings. "
     "The work here is rougher than what the Herald's Hall will touch."),
    ("shrine_of_first_light","The Shrine of First Light","building",
     "A candlelit devotional alcove off Templegate Lane. A carved stone basin holds offerings. "
     "Acolyte Ren keeps the candles burning with teenage earnestness."),
    ("sentinel_post","The Sentinel's Post","building",
     "A narrow guard station cut into the inner face of the south wall. Arrow slits look out over "
     "the Lantern Court. Cold even in summer. Watchman Orel has stood this post for eleven years."),

    # ── WARDEN'S WAY WEST (4) ─────────────────────────────────────────────────
    ("washhouse","The Washhouse","building",
     "A surprisingly pleasant public washhouse with warm water always available. "
     "Clean towels smell faintly of lavender. Certain trail debuffs clear faster here."),
    ("pantry","The Pantry","building",
     "A small, cool room with stone walls and a heavy door. Shelves of preserved foods, dried goods, "
     "candles, and basic travel rations. Nan keeps it tidy without eye contact."),
    ("washhouse_lower","The Washhouse (Lower)","building",
     "A second public washhouse serving the southern end of Warden's Way, "
     "identical in appointments with slightly better water pressure."),
    ("watchtower","The Watchtower","building",
     "A narrow stone tower. Arrow slits look out over the southern approaches. "
     "Watchman Teris maintains a sharp eye here and turns distant sightings into quests."),

    # ── SOUTH OF FOUNDER'S WALK (3) ───────────────────────────────────────────
    ("vault_of_gold","The Vault of Gold","building",
     "A squat stone building with a heavy iron door. Polished wood counters, barred windows, "
     "and the air of serious finance. Banker Guildred Copperpot handles everything with gnomish precision."),
    ("oldmere_study","Ondrel's Study","building",
     "Floor-to-ceiling shelves of books, maps, scrolls, and documents in a system only Joleth understands. "
     "A meticulous desk sits at the centre, always bearing an open book."),
    ("outfitters_rest","The Outfitter's Rest","building",
     "A cozy shop with overstuffed chairs by the window. New adventurers can claim a basic starter kit here. "
     "Shopkeep Marta worries about everyone going out underprepared."),

    # ── AROUND TEAL COURTYARDS (4) ────────────────────────────────────────────
    ("supply_room","The Supply Room","building",
     "A general overflow storage room, less organised than the Quartermaster's Cache. "
     "Things end up here when there is nowhere better. Stock Boy Fen is doing his best."),
    ("crystal_repository","The Crystal Repository","building",
     "A space dominated by a humming crystal formation of unknown origin — an arcane storage device. "
     "Archivist Quellan tends it quietly and talks to it when alone."),
    ("round_table","The Round Table","building",
     "A small meeting room with — pointedly — a round table and chairs. "
     "Guild Registrar Brom will mention the table's roundness at least twice per visit."),
    ("quartermaster","The Quartermaster's Cache","building",
     "A tidy storeroom where everything is labeled and inventoried. "
     "Quartermaster Hobb runs it entirely by the numbers. Nothing leaves without a signed manifest."),

    # ── SOUTH WALL AREA (3) ───────────────────────────────────────────────────
    ("precipice","The Precipice","exterior",
     "A dramatic stone shelf jutting from Awtown's southern wall, high above the surrounding land. "
     "The wind is constant and strong. On a clear day the full sweep of Dorfin unfolds below."),
    ("southern_outlook","The Southern Outlook","exterior",
     "A windswept overlook on the south wall of Awtown, east of the Lantern Court. "
     "The view south is unobstructed."),
    ("lookout_point","The Lookout Point","exterior",
     "A ground-level vantage point built into Awtown's western wall, overlooking the approach "
     "to the Warden's Gate."),

    # ── SOUTH ROW (4) ─────────────────────────────────────────────────────────
    ("herbalists_nook","The Herbalist's Nook","building",
     "A cramped, fragrant room near the garden gate. Bundles of drying herbs hang from the rafters; "
     "jars of roots, seeds, bark, and petals crowd every shelf. Mud is always tracked in."),
    ("study_hall","The Study Hall","building",
     "The quieter sibling of the Apprentice Hall. Rows of desks, reference books, and chalkboards. "
     "Scholar Bevin supervises. Student Mop is asleep at a back desk."),
    ("apprentice_hall","The Apprentice Hall","building",
     "A large open room with practice dummies and training weapons. Slightly chaotic, enthusiastically loud. "
     "Headmaster Orifel manages it with experienced weariness."),
    ("hermit_hollow","The Hermit's Hollow","building",
     "This room resembles a woodland cave: moss on the walls, a fire pit, a wooden stool. "
     "Nobody knows how it got here. Sage Aldric Voss seems entirely comfortable with that."),

    # ── TINKER'S DEN (1) ─────────────────────────────────────────────────────
    ("tinker_den","The Tinker's Den","building",
     "A cluttered den of gears, springs, lenses, and gadgets. The smell of oil is overwhelming. "
     "Automaton Tick sweeps the floor and occasionally says something surprisingly profound."),

    # ── VERTICALS (3) ─────────────────────────────────────────────────────────
    ("bell_upper","The Bell Tower -- Upper","building",
     "A landing halfway up the Temple's bell tower. Arrow slits overlook Awtown's rooftops. "
     "A weapon rack holds consecrated arms."),
    ("belfry","The Belfry","building",
     "The summit of the Temple's bell tower. The great bronze bell hangs from ancient timbers. "
     "It tolls at dawn and dusk; when it rings, you feel it in your chest."),
    ("high_watch","The High Watch","exterior",
     "A narrow platform above the Precipice, reached by iron rungs. No shelter from the wind. "
     "The highest accessible point in Awtown, with unobstructed views in all directions."),
]


# =============================================================================
# EXIT DATA  (from_key, direction, alias, to_key, type, gate_name)
# type: "std" | "gate" | "city_gate"
# =============================================================================

EXIT_DATA = [
    # ── FOUNDER'S WALK internal ───────────────────────────────────────────────
    ("fw_1","east","e","fw_2","std",None),
    ("fw_2","west","w","fw_1","std",None),
    ("fw_2","east","e","fw_3","std",None),
    ("fw_3","west","w","fw_2","std",None),
    ("fw_3","east","e","fw_4","std",None),
    ("fw_4","west","w","fw_3","std",None),
    ("fw_4","east","e","fw_5","std",None),
    ("fw_5","west","w","fw_4","std",None),
    ("fw_5","east","e","fw_6","std",None),
    ("fw_6","west","w","fw_5","std",None),
    ("fw_6","east","e","fw_7","std",None),
    ("fw_7","west","w","fw_6","std",None),
    ("fw_7","east","e","fw_8","std",None),
    ("fw_8","west","w","fw_7","std",None),
    ("fw_8","east","e","fw_9","std",None),
    ("fw_9","west","w","fw_8","std",None),
    ("fw_9","east","e","fw_10","std",None),
    ("fw_10","west","w","fw_9","std",None),
    ("fw_10","east","e","fw_11","std",None),
    ("fw_11","west","w","fw_10","std",None),
    ("fw_11","east","e","fw_12","std",None),
    ("fw_12","west","w","fw_11","std",None),

    # ── FW to buildings/roads ─────────────────────────────────────────────────
    ("fw_1","north","n","warden_barracks","std",None),
    ("warden_barracks","south","s","fw_1","std",None),
    ("fw_1","south","s","ww_1","std",None),
    ("fw_1","west","w","lamplighters_nook","std",None),
    ("lamplighters_nook","east","e","fw_1","std",None),
    ("fw_2","north","n","gate_side","std",None),
    ("gate_side","south","s","fw_2","std",None),
    ("fw_3","north","n","notary","std",None),
    ("notary","south","s","fw_3","std",None),
    ("fw_3","south","s","lr_1","std",None),
    ("fw_4","north","n","messenger_roost","std",None),
    ("messenger_roost","south","s","fw_4","std",None),
    ("fw_4","south","s","archivists_anteroom","std",None),
    ("archivists_anteroom","north","n","fw_4","std",None),
    ("fw_5","north","n","shadow_chamber","std",None),
    ("shadow_chamber","south","s","fw_5","std",None),
    ("fw_6","north","n","stewards_hall","std",None),
    ("stewards_hall","south","s","fw_6","std",None),
    ("fw_6","south","s","temple_ne","std",None),
    ("temple_ne","north","n","fw_6","std",None),
    ("fw_7","north","n","artificer_post","std",None),
    ("artificer_post","south","s","fw_7","std",None),
    ("fw_7","south","s","tl_1","std",None),
    ("fw_8","north","n","deed_hall","std",None),
    ("deed_hall","south","s","fw_8","std",None),
    ("fw_8","south","s","vault_of_gold","std",None),
    ("vault_of_gold","north","n","fw_8","std",None),
    ("fw_9","north","n","malgraves_parlour","std",None),
    ("malgraves_parlour","south","s","fw_9","std",None),
    ("fw_10","north","n","hammerfall_workshop","std",None),
    ("hammerfall_workshop","south","s","fw_10","std",None),
    ("fw_10","south","s","oldmere_study","std",None),
    ("oldmere_study","north","n","fw_10","std",None),
    ("fw_11","north","n","gate_main","std",None),
    ("gate_main","south","s","fw_11","std",None),
    ("fw_11","northeast","ne","heralds_hall","std",None),
    ("heralds_hall","southwest","sw","fw_11","std",None),
    ("fw_11","south","s","teal_ne","std",None),
    ("teal_ne","north","n","fw_11","std",None),
    ("teal_ne","south","s","outfitters_rest","std",None),
    ("outfitters_rest","north","n","teal_ne","std",None),
    ("fw_12","east","e","assembly_hall","std",None),
    ("assembly_hall","west","w","fw_12","std",None),

    # ── WARDEN'S WAY ──────────────────────────────────────────────────────────
    ("ww_1","north","n","fw_1","std",None),
    ("ww_1","south","s","ww_2","std",None),
    ("ww_2","north","n","ww_1","std",None),
    ("ww_2","south","s","ww_3","std",None),
    ("ww_3","north","n","ww_2","std",None),
    ("ww_3","south","s","ww_4","std",None),
    ("ww_4","north","n","ww_3","std",None),
    ("ww_4","east","e","ww_5","std",None),
    ("ww_5","west","w","ww_4","std",None),
    ("ww_5","south","s","ww_6","std",None),
    ("ww_6","north","n","ww_5","std",None),
    ("ww_6","south","s","ww_7","std",None),
    ("ww_7","north","n","ww_6","std",None),
    ("ww_1","west","w","guardroom","std",None),
    ("guardroom","east","e","ww_1","std",None),
    ("ww_3","west","w","washhouse","std",None),
    ("washhouse","east","e","ww_3","std",None),
    ("ww_4","west","w","pantry","std",None),
    ("pantry","east","e","ww_4","std",None),
    ("ww_6","west","w","washhouse_lower","std",None),
    ("washhouse_lower","east","e","ww_6","std",None),
    ("ww_7","west","w","watchtower","std",None),
    ("watchtower","east","e","ww_7","std",None),

    # ── GATE: WW-3 <-> Cartographer's Den (orange, auto-close) ───────────────
    ("ww_3","east","e","teal_main","gate","gate"),
    ("teal_main","west","w","ww_3","gate","gate"),
    # Supply Room off teal_main
    ("teal_main","south","s","supply_room","std",None),
    ("supply_room","north","n","teal_main","std",None),
    # Cartographer's Den also connects east to LR-3
    ("teal_main","east","e","lr_3","std",None),
    ("lr_3","west","w","teal_main","std",None),

    # ── GATE: WW-7 <-> Lantern Court (orange, auto-close) ────────────────────
    ("ww_7","south","s","teal_sw","gate","gate"),
    ("teal_sw","north","n","ww_7","gate","gate"),

    # ── LANTERN COURT exits ───────────────────────────────────────────────────
    ("teal_sw","west","w","sentinel_post","std",None),
    ("sentinel_post","east","e","teal_sw","std",None),
    ("teal_sw","southwest","sw","precipice","std",None),
    ("precipice","northeast","ne","teal_sw","std",None),
    # GATE: Lantern Court <-> CR-1
    ("teal_sw","east","e","cr_1","gate","gate"),
    ("cr_1","west","w","teal_sw","gate","gate"),
    # GATE: Lantern Court <-> South Gate
    ("teal_sw","south","s","gate_back","gate","gate"),
    ("gate_back","north","n","teal_sw","gate","gate"),

    # ── SOUTH GATE <-> Memorial Garden (orange, auto-close) ──────────────────
    ("gate_back","south","s","garden_nw","gate","gate"),
    ("garden_nw","north","n","gate_back","gate","gate"),

    # ── CITY GATE: Grand Gate <-> Toll Stone ─────────────────────────────────
    ("gate_main","north","n","commons_se","city_gate","city gate"),
    ("commons_se","south","s","gate_main","city_gate","city gate"),

    # ── CITY GATE: Warden's Gate <-> Tack Room ───────────────────────────────
    ("gate_side","north","n","stables_sw","city_gate","city gate"),
    ("stables_sw","south","s","gate_side","city_gate","city gate"),

    # ── TEMPLEGATE LANE ───────────────────────────────────────────────────────
    ("tl_1","north","n","fw_7","std",None),
    ("tl_1","south","s","tl_2","std",None),
    ("tl_2","north","n","tl_1","std",None),
    ("tl_2","south","s","teal_server","std",None),
    ("teal_server","north","n","tl_2","std",None),
    ("tl_2","east","e","shrine_of_first_light","std",None),
    ("shrine_of_first_light","west","w","tl_2","std",None),

    # ── HUMMING COURT exits ───────────────────────────────────────────────────
    ("teal_server","west","w","tavern_se","std",None),
    ("tavern_se","east","e","teal_server","std",None),
    ("teal_server","east","e","crystal_repository","std",None),
    ("crystal_repository","west","w","teal_server","std",None),
    ("crystal_repository","south","s","tinker_den","std",None),
    ("tinker_den","north","n","crystal_repository","std",None),

    # ── LANTERN ROAD ──────────────────────────────────────────────────────────
    ("lr_1","north","n","fw_3","std",None),
    ("lr_1","south","s","lr_2","std",None),
    ("lr_2","north","n","lr_1","std",None),
    ("lr_2","south","s","lr_3","std",None),
    ("lr_3","north","n","lr_2","std",None),
    ("lr_3","south","s","lr_4","std",None),
    ("lr_4","north","n","lr_3","std",None),
    ("lr_4","south","s","lr_5","std",None),
    ("lr_5","north","n","lr_4","std",None),
    ("lr_5","east","e","lr_6","std",None),
    ("lr_6","west","w","lr_5","std",None),
    ("lr_1","west","w","quartermaster","std",None),
    ("quartermaster","east","e","lr_1","std",None),
    ("lr_2","west","w","round_table","std",None),
    ("round_table","east","e","lr_2","std",None),
    ("lr_2","east","e","assay_office","std",None),
    ("assay_office","west","w","lr_2","std",None),
    ("lr_4","east","e","posting_board","std",None),
    ("posting_board","west","w","lr_4","std",None),
    ("lr_5","south","s","forge_nw","std",None),
    ("forge_nw","north","n","lr_5","std",None),
    ("lr_6","east","e","tavern_sw","std",None),
    ("tavern_sw","west","w","lr_6","std",None),

    # ── CRAFTSMAN'S ROAD ──────────────────────────────────────────────────────
    ("cr_1","east","e","cr_2","std",None),
    ("cr_2","west","w","cr_1","std",None),
    ("cr_2","east","e","cr_3","std",None),
    ("cr_3","west","w","cr_2","std",None),
    ("cr_3","east","e","cr_4","std",None),
    ("cr_4","west","w","cr_3","std",None),
    ("cr_1","north","n","forge_sw","std",None),
    ("forge_sw","south","s","cr_1","std",None),
    ("cr_2","south","s","study_hall","std",None),
    ("study_hall","north","n","cr_2","std",None),
    ("cr_3","north","n","forge_se","std",None),
    ("forge_se","south","s","cr_3","std",None),
    ("cr_3","south","s","apprentice_hall","std",None),
    ("apprentice_hall","north","n","cr_3","std",None),
    ("cr_4","north","n","tinker_den","std",None),
    ("tinker_den","south","s","cr_4","std",None),
    ("cr_4","south","s","hermit_hollow","std",None),
    ("hermit_hollow","north","n","cr_4","std",None),

    # ── GRAND FORGE internal ──────────────────────────────────────────────────
    ("forge_nw","east","e","forge_ne","std",None),
    ("forge_ne","west","w","forge_nw","std",None),
    ("forge_nw","south","s","forge_sw","std",None),
    ("forge_sw","north","n","forge_nw","std",None),
    ("forge_ne","south","s","forge_se","std",None),
    ("forge_se","north","n","forge_ne","std",None),
    ("forge_sw","east","e","forge_se","std",None),
    ("forge_se","west","w","forge_sw","std",None),

    # ── HERBALIST'S NOOK ──────────────────────────────────────────────────────
    ("cr_1","south","s","herbalists_nook","std",None),
    ("herbalists_nook","north","n","cr_1","std",None),

    # ── TEMPLE internal ───────────────────────────────────────────────────────
    ("temple_nw","east","e","temple_ne","std",None),
    ("temple_ne","west","w","temple_nw","std",None),
    ("temple_nw","south","s","temple_sw","std",None),
    ("temple_sw","north","n","temple_nw","std",None),
    ("temple_ne","south","s","temple_se","std",None),
    ("temple_se","north","n","temple_ne","std",None),
    ("temple_sw","east","e","temple_se","std",None),
    ("temple_se","west","w","temple_sw","std",None),
    # Temple to Tavern
    ("temple_sw","south","s","tavern_nw","std",None),
    ("tavern_nw","north","n","temple_sw","std",None),
    # Bell tower verticals
    ("temple_se","up","u","bell_upper","std",None),
    ("bell_upper","down","d","temple_se","std",None),
    ("bell_upper","up","u","belfry","std",None),
    ("belfry","down","d","bell_upper","std",None),

    # ── HEARTHSTONE INN internal ──────────────────────────────────────────────
    ("tavern_nw","east","e","tavern_ne","std",None),
    ("tavern_ne","west","w","tavern_nw","std",None),
    ("tavern_nw","south","s","tavern_sw","std",None),
    ("tavern_sw","north","n","tavern_nw","std",None),
    ("tavern_ne","south","s","tavern_se","std",None),
    ("tavern_se","north","n","tavern_ne","std",None),
    ("tavern_sw","east","e","tavern_se","std",None),
    ("tavern_se","west","w","tavern_sw","std",None),

    # ── EASTERN COMMONS internal ──────────────────────────────────────────────
    ("commons_nw","east","e","commons_ne","std",None),
    ("commons_ne","west","w","commons_nw","std",None),
    ("commons_nw","south","s","commons_sw","std",None),
    ("commons_sw","north","n","commons_nw","std",None),
    ("commons_ne","south","s","commons_se","std",None),
    ("commons_se","north","n","commons_ne","std",None),
    ("commons_sw","east","e","commons_se","std",None),
    ("commons_se","west","w","commons_sw","std",None),

    # ── DUSTY PADDOCK internal ────────────────────────────────────────────────
    ("stables_nw","east","e","stables_ne","std",None),
    ("stables_ne","west","w","stables_nw","std",None),
    ("stables_nw","south","s","stables_sw","std",None),
    ("stables_sw","north","n","stables_nw","std",None),
    ("stables_ne","south","s","stables_se","std",None),
    ("stables_se","north","n","stables_ne","std",None),
    ("stables_sw","east","e","stables_se","std",None),
    ("stables_se","west","w","stables_sw","std",None),

    # ── GARDEN OF REMEMBRANCE internal ───────────────────────────────────────
    ("garden_nw","east","e","garden_ne","std",None),
    ("garden_ne","west","w","garden_nw","std",None),
    ("garden_nw","south","s","garden_sw","std",None),
    ("garden_sw","north","n","garden_nw","std",None),
    ("garden_ne","south","s","garden_se","std",None),
    ("garden_se","north","n","garden_ne","std",None),
    ("garden_sw","east","e","garden_se","std",None),
    ("garden_se","west","w","garden_sw","std",None),

    # ── HIGH WATCH vertical ───────────────────────────────────────────────────
    ("precipice","up","u","high_watch","std",None),
    ("high_watch","down","d","precipice","std",None),

    # ── SOUTHERN OUTLOOK / LOOKOUT POINT (orphan connections) ────────────────
    ("teal_sw","east","e","southern_outlook","std",None),  # best-fit from table
    ("southern_outlook","west","w","teal_sw","std",None),
    ("lookout_point","east","e","ww_7","std",None),
    ("ww_7","west","w","lookout_point","std",None),
]


# =============================================================================
# NPC DATA  (db_key, name, desc, loc_key, role)
# =============================================================================

NPC_DATA = [
    ("npc_vonn","Gate Captain Vonn",
     "A gruff, fair-faced veteran in polished town livery. He has seen everything that comes through this gate.",
     "gate_main","guard"),
    ("npc_tessa","Guard Tessa",
     "A younger gate guard with an easy smile and curious eyes. She notices more than she lets on.",
     "gate_main","guard"),
    ("npc_crabb","Warden Crabb",
     "An old, suspicious warden with a permanent squint and a long memory for faces.",
     "gate_side","guard"),
    ("npc_birch","Gate Hand Birch",
     "A young guard who spends more time reading than watching the gate.",
     "gate_back","guard"),
    ("npc_bramwick","Herald Bramwick",
     "An endlessly enthusiastic man in official town colours. He knows every adventurer by name.",
     "heralds_hall","quest_giver"),
    ("npc_dilly","Scribe Dilly",
     "Bramwick's efficient assistant, quietly managing paperwork and map sales.",
     "heralds_hall","merchant"),
    ("npc_marta","Shopkeep Marta",
     "A warm, grandmotherly woman who worries about every adventurer leaving underprepared.",
     "outfitters_rest","merchant"),
    ("npc_guildred","Banker Guildred Copperpot",
     "A gnome banker of absolute precision and immovable principles. He speaks in decimal points.",
     "vault_of_gold","banker"),
    ("npc_holt","Vault Guard Holt",
     "An enormous human in chainmail who communicates primarily through presence.",
     "vault_of_gold","guard"),
    ("npc_malgrave","Jorvyn Malgrave",
     "Energetic, personable, always slightly in motion. Jorvyn knows everyone by name.",
     "malgraves_parlour","founder"),
    ("npc_hammerfall","Marro Hammerfall",
     "A gruff, warm man who communicates mostly in grunts while working.",
     "hammerfall_workshop","founder"),
    ("npc_ondrel","Joleth Ondrel",
     "Quietly brilliant and slightly distracted. Warm underneath the absentmindedness.",
     "oldmere_study","founder"),
    ("npc_pell","Steward Pell",
     "An efficient, no-nonsense woman who manages the town's logistics without wasting a minute.",
     "stewards_hall","quest_giver"),
    ("npc_nimble","Clerk Nimble",
     "A young halfling assistant, quick with a quill and quicker with a filing system.",
     "stewards_hall","generic"),
    ("npc_cogsworth","Tinker Cogsworth",
     "An old gnome friend of Marro who talks very fast and knows an extraordinary amount.",
     "artificer_post","merchant"),
    ("npc_sprocket","Apprentice Sprocket",
     "A young gnome learning the trade. She fixes approximately half of what she touches.",
     "artificer_post","generic"),
    ("npc_renwick","Tollkeeper Renwick",
     "A bored but friendly gate officer who has given the same orientation speech for fifteen years.",
     "commons_se","generic"),
    ("npc_trader_moss","Trader Moss",
     "A travelling merchant with a rotating inventory of questionable provenance.",
     "commons_ne","merchant"),
    ("npc_oswin","Stableman Oswin",
     "A weathered old horseman who can assess a horse's temperament in thirty seconds.",
     "stables_sw","merchant"),
    ("npc_groom_pip","Groom Pip",
     "A cheerful young stable hand who is always in a hurry and always has a carrot ready.",
     "stables_se","generic"),
    ("npc_enid","Groundskeeper Enid",
     "An elderly woman who tends the Memorial Garden with quiet devotion. She knows every grave.",
     "garden_nw","quest_giver"),
    ("npc_watcher","The Watcher",
     "A silent, hooded figure who stands by the Reflecting Pool at all hours. No one knows who they are.",
     "garden_sw","generic"),
    ("npc_edwyn_lux","High Priest Edwyn Lux",
     "A solemn, kind man who oversees all temple functions with gentle authority.",
     "temple_nw","merchant"),
    ("npc_sister_sera","Sister Sera",
     "An enthusiastic young priestess still mastering some of her healing spells.",
     "temple_ne","merchant"),
    ("npc_aldwin","Brother Aldwin",
     "A formal, serious cleric trainer who expects dedication.",
     "temple_sw","trainer"),
    ("npc_thane_dusk","Paladin-Warden Thane Dusk",
     "A battle-scarred retired paladin who trains others. Gruff, absolutely honourable.",
     "temple_se","trainer"),
    ("npc_bess","Innkeeper Bess Copperladle",
     "Warm, formidable, with a memory for faces that borders on unsettling.",
     "tavern_sw","innkeeper"),
    ("npc_finn","Barkeep Finn",
     "Quick wit and quicker hands. Serves drinks without spilling and information without effort.",
     "tavern_nw","merchant"),
    ("npc_cobble","Lute-player Cobble",
     "A wandering bard of considerable skill and terrible grace under requests.",
     "tavern_nw","generic"),
    ("npc_darra","Cook Darra",
     "The undisputed ruler of the kitchen. She does not welcome visitors.",
     "tavern_ne","generic"),
    ("npc_quellan","Archivist Quellan",
     "A quiet half-elf who tends the crystal formation and talks to it when alone.",
     "crystal_repository","quest_giver"),
    ("npc_hobb","Quartermaster Hobb",
     "Short, efficient, entirely governed by inventory numbers. Nothing leaves without a manifest.",
     "quartermaster","merchant"),
    ("npc_brom","Guild Registrar Brom",
     "Handles guild formation with meticulous attention. Very fond of the round table.",
     "round_table","generic"),
    ("npc_brondal","Master Smith Brondal Ironmark",
     "A veteran dwarf smith of legendary skill and very few words.",
     "forge_nw","trainer"),
    ("npc_wynn","Carpenter Wynn",
     "A cheerful human craftsman who narrates his work at length to anyone within earshot.",
     "forge_ne","trainer"),
    ("npc_mira","Weaver Mira",
     "A quiet, precise elf who produces fabric of impossible fineness.",
     "forge_sw","trainer"),
    ("npc_sable_dross","Alchemist Sable Dross",
     "Eccentric, distracted, faintly singed. Works in cheerful chaos.",
     "forge_se","trainer"),
    ("npc_fenn","Cogwright Fenn",
     "Marro's oldest friend. Sells mechanical components and trains tinkerers hands-on.",
     "tinker_den","trainer"),
    ("npc_tick","Automaton Tick",
     "A small mechanical construct that sweeps the floor and occasionally says something profound.",
     "tinker_den","generic"),
    ("npc_orifel","Headmaster Thane Orifel",
     "A tired but dedicated trainer who has seen a hundred students come and go.",
     "apprentice_hall","trainer"),
    ("npc_rudd","Apprentice Rudd",
     "An overconfident student who challenges new arrivals to sparring matches.",
     "apprentice_hall","generic"),
    ("npc_yeva","Apprentice Yeva",
     "A studious young mage who takes her homework very seriously.",
     "apprentice_hall","quest_giver"),
    ("npc_aldric_voss","Sage Aldric Voss",
     "Ancient, cryptic, inexplicably comfortable in a room that looks like a forest cave.",
     "hermit_hollow","quest_giver"),
    ("npc_fen","Stock Boy Fen",
     "A teenage helper who is not very organised but is enthusiastic.",
     "supply_room","quest_giver"),
    ("npc_teris","Watchman Teris",
     "A sharp-eyed half-elf ranger who notices what moves on the horizon.",
     "watchtower","quest_giver"),
    ("npc_dorn","Sergeant Dorn",
     "A scarred veteran with a permanent scowl and a dry sense of humour.",
     "warden_barracks","trainer"),
    ("npc_recruit_pip","Guard Recruit Pip",
     "First week on the job, nervously polishing a helmet that is too large for him.",
     "warden_barracks","generic"),
    ("npc_morvaine","Hedge-Witch Morvaine",
     "An ancient, half-feral woman who knows every plant in Dorfin by name.",
     "herbalists_nook","trainer"),
    ("npc_izra","Mapper Izra",
     "A meticulous gnome cartographer who has personally charted more of Dorfin than anyone alive.",
     "teal_main","trainer"),
    ("npc_nan","Nan",
     "A quiet, stout woman who keeps the Pantry stocked without ever making eye contact.",
     "pantry","merchant"),
    ("npc_orvyn","Lamplighter Orvyn",
     "An elderly man who has walked Awtown's streets every night for forty years.",
     "lamplighters_nook","quest_giver"),
    ("npc_harwick","Sergeant's Aid Harwick",
     "Stocky, no-nonsense. Handles the paperwork Sergeant Dorn will not touch.",
     "guardroom","quest_giver"),
    ("npc_sybil","Clerk-Errant Sybil",
     "Young, harried, permanently ink-stained. She was a courier once. She never left.",
     "archivists_anteroom","quest_giver"),
    ("npc_tetch","Wayfarer Tetch",
     "A lean, road-worn human who has been 'passing through' for three years.",
     "mapmakers_rest","merchant"),
    ("npc_acolyte_ren","Acolyte Ren",
     "An earnest seventeen-year-old managing the Shrine with more enthusiasm than authority.",
     "shrine_of_first_light","merchant"),
    ("npc_orel","Watchman Orel",
     "A watchman who has stood the same post for eleven years without complaint.",
     "sentinel_post","quest_giver"),
    ("npc_notary_prim","Notary Prim",
     "Small, precise, permanently ink-stained. Notarises contracts without judging them.",
     "notary","generic"),
    ("npc_wren","Postmaster Wren",
     "Wiry, fast-moving, never stands still. Manages the town's messenger network.",
     "messenger_roost","quest_giver"),
    ("npc_registrar","Registrar Voss",
     "A methodical older man who knows where every land scroll is filed.",
     "deed_hall","generic"),
    ("npc_sal","Board-Keeper Sal",
     "A gruff woman who manages the Posting Board with absolute neutrality.",
     "posting_board","quest_giver"),
    ("npc_dunt","Assayer Dunt",
     "A square-built, square-jawed dwarf who conducts all valuations incorruptibly.",
     "assay_office","merchant"),
    ("npc_bevin","Scholar Bevin",
     "A calm, patient young woman who ended up as the Study Hall's unofficial supervisor.",
     "study_hall","trainer"),
    ("npc_student_mop","Student Mop",
     "Always asleep at a desk. Has never failed a lesson. Nobody knows how.",
     "study_hall","generic"),
    ("npc_aldous","Town Crier Aldous",
     "A dramatic man who announces town news with maximum gravitas.",
     "assembly_hall","generic"),
]


# =============================================================================
# GATE PAIRS  (from_key, from_dir, to_key, to_dir)
# Must be run after all exits are created.
# =============================================================================

GATE_PAIRS = [
    ("ww_3",      "east",  "teal_main",  "west"),   # Cartographer's Den
    ("teal_main", "west",  "ww_3",       "east"),   # (symmetric — pair both directions)
    ("ww_7",      "south", "teal_sw",    "north"),  # Lantern Court
    ("teal_sw",   "east",  "cr_1",       "west"),   # CR-1
    ("teal_sw",   "south", "gate_back",  "north"),  # South Gate (outer)
    ("gate_back", "south", "garden_nw",  "north"),  # Memorial Garden
    ("gate_main", "north", "commons_se", "south"),  # Grand Gate city gate
    ("gate_side", "north", "stables_sw", "south"),  # Warden's Gate city gate
]

# =============================================================================
# CODE — Step 1: Rooms
# =============================================================================

caller.msg("|y[batch_awtown] Step 1/4 — Creating rooms...|n")
count = 0
for entry in ROOM_DATA:
    db_key, name, tc_key, desc = entry[0], entry[1], entry[2], entry[3]
    _make_room(db_key, name, tc_key, desc)
    count += 1
caller.msg(f"|g  Created/updated {count} rooms.|n")

# =============================================================================
# CODE — Step 2: Exits
# =============================================================================

caller.msg("|y[batch_awtown] Step 2/4 — Creating exits...|n")
count = 0
skipped = 0
for row in EXIT_DATA:
    from_key, direction, alias, to_key, etype, gate_name = row
    if etype == "city_gate":
        tc = AwtownCityGate
    elif etype == "gate":
        tc = AwtownGate
    else:
        tc = DefaultExit
    ex = _make_exit(from_key, direction, alias, to_key, tc=tc, gate_name=gate_name)
    if ex:
        count += 1
    else:
        skipped += 1
caller.msg(f"|g  Created {count} exits. Skipped {skipped} (already existed or missing room).|n")

# =============================================================================
# CODE — Step 3: Pair gates
# =============================================================================

caller.msg("|y[batch_awtown] Step 3/4 — Pairing gate exits...|n")
for from_key, from_dir, to_key, to_dir in GATE_PAIRS:
    _pair_gates(from_key, from_dir, to_key, to_dir)
caller.msg("|g  Gate pairs set.|n")

# =============================================================================
# CODE — Step 4: NPCs
# =============================================================================

caller.msg("|y[batch_awtown] Step 4/4 — Placing NPCs...|n")
count = 0
missing = []
for row in NPC_DATA:
    db_key, name, desc, loc_key, role = row
    npc = _make_npc(db_key, name, desc, loc_key, role=role)
    if npc:
        count += 1
    else:
        missing.append(loc_key)
if missing:
    caller.msg(f"|r  Warning: could not place NPCs — missing rooms: {missing}|n")
caller.msg(f"|g  Placed/updated {count} NPCs.|n")

caller.msg("|g[batch_awtown] Complete. Awtown is ready.|n")

