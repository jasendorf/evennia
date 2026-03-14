# DorfinMUD — Live World Export

**108 rooms** | **64 NPCs**

---

## apprentice

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `apprentice_hall` | **The Apprentice Hall** | AwtownRoom | north→cr_3 |

### The Apprentice Hall (`apprentice_hall`)

> A large open room with practice dummies and training weapons. Slightly chaotic, enthusiastically loud. Headmaster Orifel manages it with experienced weariness.

**NPCs:**
- **Headmaster Thane Orifel** (`npc_orifel`, trainer) — A tired but dedicated trainer who has seen a hundred students come and go.
- **Apprentice Rudd** (`npc_rudd`, generic) — An overconfident student who challenges new arrivals to sparring matches.
- **Apprentice Yeva** (`npc_yeva`, quest_giver) — A studious young mage who takes her homework very seriously.

---

## archivists

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `archivists_anteroom` | **The Archivist's Anteroom** | AwtownRoom | north→fw_4 |

### The Archivist's Anteroom (`archivists_anteroom`)

> Shelves stacked with overflowing ledgers and correspondence waiting to be filed. The room perpetually smells of ink and mild panic.

**NPCs:**
- **Clerk-Errant Sybil** (`npc_sybil`, quest_giver) — Young, harried, permanently ink-stained. She was a courier once. She never left.

---

## artificer

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `artificer_post` | **The Artificer's Post** | AwtownRoom | south→fw_7 |

### The Artificer's Post (`artificer_post`)

> A bright, cluttered workshop where broken things are fixed. Magical items, mundane tools, and odd contraptions in various states of repair line the walls.

**NPCs:**
- **Tinker Cogsworth** (`npc_cogsworth`, merchant) — An old gnome friend of Marro who talks very fast and knows an extraordinary amount.
- **Apprentice Sprocket** (`npc_sprocket`, generic) — A young gnome learning the trade. She fixes approximately half of what she touches.

---

## assay

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `assay_office` | **The Assay Office** | AwtownRoom | west→lr_2 |

### The Assay Office (`assay_office`)

> A clean, well-lit room with precision scales, magnifying lenses, and testing reagents. Assayer Dunt conducts all valuations with complete impartiality.

**NPCs:**
- **Assayer Dunt** (`npc_dunt`, merchant) — A square-built, square-jawed dwarf who conducts all valuations incorruptibly.

---

## assembly

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `assembly_hall` | **The Assembly Hall** | AwtownRoom | west→fw_12 |

### The Assembly Hall (`assembly_hall`)

> A grand vaulted chamber for town meetings and formal ceremonies. Rows of benches face a raised dais. Portraits of the three Founders hang on the walls.

**NPCs:**
- **Town Crier Aldous** (`npc_aldous`, generic) — A dramatic man who announces town news with maximum gravitas.

---

## belfry

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `belfry` | **The Belfry** | AwtownRoom | down→bell_upper |

### The Belfry (`belfry`)

> The summit of the Temple's bell tower. The great bronze bell hangs from ancient timbers. It tolls at dawn and dusk; when it rings, you feel it in your chest.

---

## bell

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `bell_upper` | **The Bell Tower -- Upper** | AwtownRoom | down→temple_se, up→belfry |

### The Bell Tower -- Upper (`bell_upper`)

> A landing halfway up the Temple's bell tower. Arrow slits overlook Awtown's rooftops. A weapon rack holds consecrated arms.

---

## commons

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `commons_ne` | **The Cart Market** | AwtownExteriorRoom | south→commons_se, west→commons_nw |
| `commons_nw` | **The Wayfarers' Green** | AwtownExteriorRoom | east→commons_ne, south→commons_sw |
| `commons_se` | **The Toll Stone** | AwtownExteriorRoom | north→commons_ne, south→gate_main [city_gate], west→commons_sw |
| `commons_sw` | **The Crossroads Notice Board** | AwtownExteriorRoom | east→commons_se, north→commons_nw |

### The Cart Market (`commons_ne`)

> Rotating stalls of travelling merchants spread wares on folding tables and from carts. The inventory changes day to day. The smell of spiced food competes with exotic goods.

**NPCs:**
- **Trader Moss** (`npc_trader_moss`, merchant) — A travelling merchant with a rotating inventory of questionable provenance.

### The Wayfarers' Green (`commons_nw`)

> A broad grassy common where travellers rest, camp, and swap stories before entering Awtown. The grass is well-worn in patches from generations of campfires.

### The Toll Stone (`commons_se`)

> An old carved stone marker at Awtown's eastern border, engraved with the town's founding date and a worn relief of the three Founders. The city gate lies to the south.

**NPCs:**
- **Tollkeeper Renwick** (`npc_renwick`, generic) — A bored but friendly gate officer who has given the same orientation speech for fifteen years.

### The Crossroads Notice Board (`commons_sw`)

> A large wooden board covered in notices, wanted posters, and regional news pinned three deep. This is where word from the wider world first reaches the road to Awtown.

---

## cr

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `cr_1` | **Along Craftsman's Road** | AwtownRoadRoom | east→cr_2, north→forge_sw, south→herbalists_nook, west→teal_sw [gate] |
| `cr_2` | **Along Craftsman's Road** | AwtownRoadRoom | east→cr_3, south→study_hall, west→cr_1 |
| `cr_3` | **Along Craftsman's Road** | AwtownRoadRoom | east→cr_4, north→forge_se, south→apprentice_hall, west→cr_2 |
| `cr_4` | **Along Craftsman's Road** | AwtownRoadRoom | north→tinker_den, south→hermit_hollow, west→cr_3 |

### Along Craftsman's Road (`cr_1`)

> The western end of Craftsman's Road. A heavy gate to the west leads into the Lantern Court. The Loom Room is just north; the road stretches east.

### Along Craftsman's Road (`cr_2`)

> The Study Hall is tucked to the south. Crates of raw materials line the northern wall.

### Along Craftsman's Road (`cr_3`)

> The Alchemist's Corner is north, occasionally marked by a plume of strange-coloured smoke. The Apprentice Hall to the south is the noisiest building on the road.

### Along Craftsman's Road (`cr_4`)

> The eastern end of Craftsman's Road. The Tinker's Den clicking is audible through the north wall. The Hermit's Hollow is improbably quiet to the south.

---

## crystal

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `crystal_repository` | **The Crystal Repository** | AwtownRoom | south→tinker_den, west→teal_server |

### The Crystal Repository (`crystal_repository`)

> A space dominated by a humming crystal formation of unknown origin — an arcane storage device. Archivist Quellan tends it quietly and talks to it when alone.

**NPCs:**
- **Archivist Quellan** (`npc_quellan`, quest_giver) — A quiet half-elf who tends the crystal formation and talks to it when alone.

---

## deed

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `deed_hall` | **The Deed Hall** | AwtownRoom | south→fw_8 |

### The Deed Hall (`deed_hall`)

> A narrow room lined with filing cabinets and land registry scrolls. Every plot of land in Awtown has a record here. Dry as dust, but surprisingly important.

**NPCs:**
- **Registrar Voss** (`npc_registrar`, generic) — A methodical older man who knows where every land scroll is filed.

---

## forge

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `forge_ne` | **The Workbench** | AwtownRoom | south→forge_se, west→forge_nw |
| `forge_nw` | **The Iron Forge** | AwtownRoom | east→forge_ne, north→lr_5, south→forge_sw |
| `forge_se` | **The Alchemist's Corner** | AwtownRoom | north→forge_ne, south→cr_3, west→forge_sw |
| `forge_sw` | **The Loom Room** | AwtownRoom | east→forge_se, north→forge_nw, south→cr_1 |

### The Workbench (`forge_ne`)

> A broad, fragrant space — cedar from woodwork, leather from saddle frames. Bows, shields, furniture, and tack are produced here. Carpenter Wynn narrates his projects.

**NPCs:**
- **Carpenter Wynn** (`npc_wynn`, trainer) — A cheerful human craftsman who narrates his work at length to anyone within earshot.

### The Iron Forge (`forge_nw`)

> A thundering forge with massive bellows. The heat is extraordinary. Master Smith Brondal Ironmark works here in near-silence with economical precision.

**NPCs:**
- **Master Smith Brondal Ironmark** (`npc_brondal`, trainer) — A veteran dwarf smith of legendary skill and very few words.

### The Alchemist's Corner (`forge_se`)

> Bubbling vials, labeled jars, and the aftermath of small explosions characterise this corner. Alchemist Sable Dross works in cheerful chaos.

**NPCs:**
- **Alchemist Sable Dross** (`npc_sable_dross`, trainer) — Eccentric, distracted, faintly singed. Works in cheerful chaos.

### The Loom Room (`forge_sw`)

> The quietest of the Forge's four workshops. Weaver Mira works in near-silence, producing cloth of improbable fineness.

**NPCs:**
- **Weaver Mira** (`npc_mira`, trainer) — A quiet, precise elf who produces fabric of impossible fineness.

---

## fw

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `fw_1` | **Along Founder's Walk** | AwtownRoadRoom | east→fw_2, north→warden_barracks, south→ww_1, west→lamplighters_nook |
| `fw_10` | **Along Founder's Walk** | AwtownRoadRoom | east→fw_11, north→hammerfall_workshop, south→oldmere_study, west→fw_9 |
| `fw_11` | **Along Founder's Walk** | AwtownRoadRoom | east→fw_12, north→gate_main, northeast→heralds_hall, south→teal_ne, west→fw_10 |
| `fw_12` | **Along Founder's Walk** | AwtownRoadRoom | east→assembly_hall, west→fw_11 |
| `fw_2` | **Along Founder's Walk** | AwtownRoadRoom | east→fw_3, north→gate_side, west→fw_1 |
| `fw_3` | **Along Founder's Walk** | AwtownRoadRoom | east→fw_4, north→notary, south→lr_1, west→fw_2 |
| `fw_4` | **Along Founder's Walk** | AwtownRoadRoom | east→fw_5, north→messenger_roost, south→archivists_anteroom, west→fw_3 |
| `fw_5` | **Along Founder's Walk** | AwtownRoadRoom | east→fw_6, north→shadow_chamber, west→fw_4 |
| `fw_6` | **Along Founder's Walk** | AwtownRoadRoom | east→fw_7, north→stewards_hall, south→temple_ne, west→fw_5 |
| `fw_7` | **Along Founder's Walk** | AwtownRoadRoom | east→fw_8, north→artificer_post, south→tl_1, west→fw_6 |
| `fw_8` | **Along Founder's Walk** | AwtownRoadRoom | east→fw_9, north→deed_hall, south→vault_of_gold, west→fw_7 |
| `fw_9` | **Along Founder's Walk** | AwtownRoadRoom | east→fw_10, north→malgraves_parlour, west→fw_8 |

### Along Founder's Walk (`fw_1`)

> The cobblestones of Founder's Walk are swept clean each morning. Warden's Way turns south here. The Warden's Barracks stand to the north; the Lamplighter's Nook glows warmly to the west.

### Along Founder's Walk (`fw_10`)

> Hammerfall's Workshop is to the north, identified by persistent clanking. Ondrel's Study sits quietly to the south. The Grand Gate is close.

### Along Founder's Walk (`fw_11`)

> The Grand Gate rises to the north. Above its arch: 'Leave lesser than you arrived.' The Herald's Hall lies to the northeast. A covered passage leads south.

### Along Founder's Walk (`fw_12`)

> The far eastern end of Founder's Walk, where the road ends at the Assembly Hall's broad front steps.

### Along Founder's Walk (`fw_2`)

> A well-travelled stretch of Founder's Walk. The Warden's Gate stands solid to the north. The walk continues east toward the administrative heart of Awtown.

### Along Founder's Walk (`fw_3`)

> The Notary's Office occupies a neat doorway to the north. South, Lantern Road begins its run toward the forge district.

### Along Founder's Walk (`fw_4`)

> A busy stretch — clerks and messengers pass at most hours. The Messenger's Roost is just north; the flutter of birds is faintly audible. The Archivist's Anteroom is south, perpetually smelling of ink.

### Along Founder's Walk (`fw_5`)

> A quieter stretch. The Shadow Chamber's unmarked door sits to the north, easy to overlook by design.

### Along Founder's Walk (`fw_6`)

> Templegate Lane descends south toward the Temple precinct. The Steward's Hall occupies a tidy doorway to the north.

### Along Founder's Walk (`fw_7`)

> The Artificer's Post is to the north, its door usually propped open with a half-finished device. Templegate Lane descends south toward the Temple.

### Along Founder's Walk (`fw_8`)

> The Deed Hall anchors the north side, its door bearing the town's official seal. The Vault of Gold's squat stone face looks south, barred windows glinting.

### Along Founder's Walk (`fw_9`)

> Malgrave's Parlour occupies the north side, a warm light always visible through its windows. The walk is busy at all hours here — the administrative heart of Awtown.

---

## garden

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `garden_ne` | **The Old Graves** | AwtownExteriorRoom | south→garden_se, west→garden_nw |
| `garden_nw` | **The Memorial Garden** | AwtownExteriorRoom | east→garden_ne, north→gate_back [gate], south→garden_sw |
| `garden_se` | **The Willow Grove** | AwtownExteriorRoom | north→garden_ne, west→garden_sw |
| `garden_sw` | **The Reflecting Pool** | AwtownExteriorRoom | east→garden_se, north→garden_nw |

### The Old Graves (`garden_ne`)

> Weathered headstones from Awtown's earliest days. The inscriptions are cryptic and old. At night something moves among these stones — unsettling even within the walls.

### The Memorial Garden (`garden_nw`)

> Carefully tended flower beds surround small stone monuments to fallen adventurers. The groundskeeper's care is evident in every trimmed edge.

**NPCs:**
- **Groundskeeper Enid** (`npc_enid`, quest_giver) — An elderly woman who tends the Memorial Garden with quiet devotion. She knows every grave.

### The Willow Grove (`garden_se`)

> Ancient willows crowd this corner of the garden, their branches forming a curtained space. Rare herbs grow in the shadows.

### The Reflecting Pool (`garden_sw`)

> A still, dark pool surrounded by weeping willows. The water does not stir even in wind. Rumoured to show visions. The Watcher stands here always, never speaking.

**NPCs:**
- **The Watcher** (`npc_watcher`, generic) — A silent, hooded figure who stands by the Reflecting Pool at all hours. No one knows who they are.

---

## gate

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `gate_back` | **The South Gate** | AwtownRoadRoom | north→teal_sw [gate], south→garden_nw [gate] |
| `gate_main` | **The Grand Gate** | AwtownRoadRoom | north→commons_se [city_gate], south→fw_11 |
| `gate_side` | **The Warden's Gate** | AwtownRoadRoom | north→stables_sw [city_gate], south→fw_2 |

### The South Gate (`gate_back`)

> A quiet gate at Awtown's southern end, rarely busy. The ironwork is entwined with carved vines — a tribute to the garden beyond. A young guard reads here more often than she watches the road.

**NPCs:**
- **Gate Hand Birch** (`npc_birch`, guard) — A young guard who spends more time reading than watching the gate.

### The Grand Gate (`gate_main`)

> Awtown's grand eastern entrance. Two iron-banded oak doors stand open during daylight, flanked by guards in polished town livery. Above the arch, carved deep: 'Leave lesser than you arrived.'

**NPCs:**
- **Gate Captain Vonn** (`npc_vonn`, guard) — A gruff, fair-faced veteran in polished town livery. He has seen everything that comes through this gate.
- **Guard Tessa** (`npc_tessa`, guard) — A younger gate guard with an easy smile and curious eyes. She notices more than she lets on.

### The Warden's Gate (`gate_side`)

> A smaller but sturdy gate in Awtown's western wall. Iron-banded oak stands solid between town and the paddock outside. Less ceremony than the Grand Gate — this is where locals pass.

**NPCs:**
- **Warden Crabb** (`npc_crabb`, guard) — An old, suspicious warden with a permanent squint and a long memory for faces.

---

## guardroom

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `guardroom` | **The Guardroom** | AwtownRoom | east→ww_1 |

### The Guardroom (`guardroom`)

> A plain utilitarian room smelling of leather and cold stew. Off-duty guards play cards at a battered table. A pinboard bristles with wanted notices.

**NPCs:**
- **Sergeant's Aid Harwick** (`npc_harwick`, quest_giver) — Stocky, no-nonsense. Handles the paperwork Sergeant Dorn will not touch.

---

## hammerfall

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `hammerfall_workshop` | **Hammerfall's Workshop** | AwtownRoom | south→fw_10 |

### Hammerfall's Workshop (`hammerfall_workshop`)

> Absolute chaos. Every surface is covered in half-built devices, tools, spare parts, and diagrams. The smell of oil and hot metal is intense. Marro Hammerfall is always elbow-deep in something.

**NPCs:**
- **Marro Hammerfall** (`npc_hammerfall`, founder) — A gruff, warm man who communicates mostly in grunts while working.

---

## heralds

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `heralds_hall` | **The Herald's Hall** | AwtownRoom | southwest→fw_11 |

### The Herald's Hall (`heralds_hall`)

> The first room most adventurers see inside Awtown. High ceilings, bright torchlight, a roaring hearth. A large Quest Board dominates one wall; town maps are available here.

**NPCs:**
- **Herald Bramwick** (`npc_bramwick`, quest_giver) — An endlessly enthusiastic man in official town colours. He knows every adventurer by name.
- **Scribe Dilly** (`npc_dilly`, merchant) — Bramwick's efficient assistant, quietly managing paperwork and map sales.

---

## herbalists

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `herbalists_nook` | **The Herbalist's Nook** | AwtownRoom | north→cr_1 |

### The Herbalist's Nook (`herbalists_nook`)

> A cramped, fragrant room near the garden gate. Bundles of drying herbs hang from the rafters; jars of roots, seeds, bark, and petals crowd every shelf. Mud is always tracked in.

**NPCs:**
- **Hedge-Witch Morvaine** (`npc_morvaine`, trainer) — An ancient, half-feral woman who knows every plant in Dorfin by name.

---

## hermit

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `hermit_hollow` | **The Hermit's Hollow** | AwtownRoom | north→cr_4 |

### The Hermit's Hollow (`hermit_hollow`)

> This room resembles a woodland cave: moss on the walls, a fire pit, a wooden stool. Nobody knows how it got here. Sage Aldric Voss seems entirely comfortable with that.

**NPCs:**
- **Sage Aldric Voss** (`npc_aldric_voss`, quest_giver) — Ancient, cryptic, inexplicably comfortable in a room that looks like a forest cave.

---

## high

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `high_watch` | **The High Watch** | AwtownExteriorRoom | down→precipice |

### The High Watch (`high_watch`)

> A narrow platform above the Precipice, reached by iron rungs. No shelter from the wind. The highest accessible point in Awtown, with unobstructed views in all directions.

---

## lamplighters

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `lamplighters_nook` | **The Lamplighter's Nook** | AwtownRoom | east→fw_1 |

### The Lamplighter's Nook (`lamplighters_nook`)

> A small alcove built into the town wall, smelling of hot wax and lamp oil. Racks of candles and lanterns line every surface. Always lit, even on the darkest nights.

**NPCs:**
- **Lamplighter Orvyn** (`npc_orvyn`, quest_giver) — An elderly man who has walked Awtown's streets every night for forty years.

---

## lookout

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `lookout_point` | **The Lookout Point** | AwtownExteriorRoom | east→ww_7 |

### The Lookout Point (`lookout_point`)

> A ground-level vantage point built into Awtown's western wall, overlooking the approach to the Warden's Gate.

---

## lr

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `lr_1` | **The Lantern Road** | AwtownRoadRoom | north→fw_3, south→lr_2, west→quartermaster |
| `lr_2` | **The Lantern Road** | AwtownRoadRoom | east→assay_office, north→lr_1, south→lr_3, west→round_table |
| `lr_3` | **The Lantern Road** | AwtownRoadRoom | north→lr_2, south→lr_4, west→teal_main |
| `lr_4` | **The Lantern Road** | AwtownRoadRoom | east→posting_board, north→lr_3, south→lr_5 |
| `lr_5` | **The Lantern Road** | AwtownRoadRoom | east→lr_6, north→lr_4, south→forge_nw |
| `lr_6` | **The Lantern Road** | AwtownRoadRoom | east→tavern_sw, west→lr_5 |

### The Lantern Road (`lr_1`)

> Small iron lanterns hang at regular intervals, their flames steady even in wind. The Quartermaster's Cache is to the west.

### The Lantern Road (`lr_2`)

> The Round Table is to the west; the Assay Office to the east. The lanterns burn a warm amber.

### The Lantern Road (`lr_3`)

> The Cartographer's Den courtyard is to the west; the Mapmaker's Rest just east.

### The Lantern Road (`lr_4`)

> The Posting Board's corkboard walls are visible through the east doorway. Lanterns line the road north and south.

### The Lantern Road (`lr_5`)

> The road branches east toward the Hearthstone Inn, and south toward the Iron Forge. The smell of food and the ring of metal compete pleasantly.

### The Lantern Road (`lr_6`)

> A short east-west spur. The Inn Counter's door is to the east, the Common Room audible through it.

---

## malgraves

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `malgraves_parlour` | **Malgrave's Parlour** | AwtownRoom | south→fw_9 |

### Malgrave's Parlour (`malgraves_parlour`)

> A warm, welcoming office that always feels slightly busy. Comfortable chairs face a desk covered in notes and schedules. A 'You've Got This!' pennant hangs slightly crooked above the door.

**NPCs:**
- **Jorvyn Malgrave** (`npc_malgrave`, founder) — Energetic, personable, always slightly in motion. Jorvyn knows everyone by name.

---

## mapmakers

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `mapmakers_rest` | **The Mapmaker's Rest** | AwtownRoom | none |

### The Mapmaker's Rest (`mapmakers_rest`)

> A narrow room with chairs and a tall map case. Travelling cartographers copy charts here. A rumour board near the door catches things the official boards won't print.

**NPCs:**
- **Wayfarer Tetch** (`npc_tetch`, merchant) — A lean, road-worn human who has been 'passing through' for three years.

---

## messenger

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `messenger_roost` | **The Messenger's Roost** | AwtownRoom | south→fw_4 |

### The Messenger's Roost (`messenger_roost`)

> A small, busy room smelling of feathers and leather satchels. Messenger birds perch on racks. Runners come and go constantly.

**NPCs:**
- **Postmaster Wren** (`npc_wren`, quest_giver) — Wiry, fast-moving, never stands still. Manages the town's messenger network.

---

## notary

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `notary` | **The Notary's Office** | AwtownRoom | south→fw_3 |

### The Notary's Office (`notary`)

> A cramped but tidy office. Deeds, contracts, witnessed oaths, and official stamps cover every surface. The smell of ink and wax seals never fully leaves.

**NPCs:**
- **Notary Prim** (`npc_notary_prim`, generic) — Small, precise, permanently ink-stained. Notarises contracts without judging them.

---

## oldmere

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `oldmere_study` | **Ondrel's Study** | AwtownRoom | north→fw_10 |

### Ondrel's Study (`oldmere_study`)

> Floor-to-ceiling shelves of books, maps, scrolls, and documents in a system only Joleth understands. A meticulous desk sits at the centre, always bearing an open book.

**NPCs:**
- **Joleth Ondrel** (`npc_ondrel`, founder) — Quietly brilliant and slightly distracted. Warm underneath the absentmindedness.

---

## outfitters

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `outfitters_rest` | **The Outfitter's Rest** | AwtownRoom | north→teal_ne |

### The Outfitter's Rest (`outfitters_rest`)

> A cozy shop with overstuffed chairs by the window. New adventurers can claim a basic starter kit here. Shopkeep Marta worries about everyone going out underprepared.

**NPCs:**
- **Shopkeep Marta** (`npc_marta`, merchant) — A warm, grandmotherly woman who worries about every adventurer leaving underprepared.

---

## pantry

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `pantry` | **The Pantry** | AwtownRoom | east→ww_4 |

### The Pantry (`pantry`)

> A small, cool room with stone walls and a heavy door. Shelves of preserved foods, dried goods, candles, and basic travel rations. Nan keeps it tidy without eye contact.

**NPCs:**
- **Nan** (`npc_nan`, merchant) — A quiet, stout woman who keeps the Pantry stocked without ever making eye contact.

---

## posting

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `posting_board` | **The Posting Board** | AwtownRoom | west→lr_4 |

### The Posting Board (`posting_board`)

> A room dominated by an enormous cork board covered in notices and wanted postings. The work here is rougher than what the Herald's Hall will touch.

**NPCs:**
- **Board-Keeper Sal** (`npc_sal`, quest_giver) — A gruff woman who manages the Posting Board with absolute neutrality.

---

## precipice

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `precipice` | **The Precipice** | AwtownExteriorRoom | northeast→teal_sw, up→high_watch |

### The Precipice (`precipice`)

> A dramatic stone shelf jutting from Awtown's southern wall, high above the surrounding land. The wind is constant and strong. On a clear day the full sweep of Dorfin unfolds below.

---

## quartermaster

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `quartermaster` | **The Quartermaster's Cache** | AwtownRoom | east→lr_1 |

### The Quartermaster's Cache (`quartermaster`)

> A tidy storeroom where everything is labeled and inventoried. Quartermaster Hobb runs it entirely by the numbers. Nothing leaves without a signed manifest.

**NPCs:**
- **Quartermaster Hobb** (`npc_hobb`, merchant) — Short, efficient, entirely governed by inventory numbers. Nothing leaves without a manifest.

---

## round

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `round_table` | **The Round Table** | AwtownRoom | east→lr_2 |

### The Round Table (`round_table`)

> A small meeting room with — pointedly — a round table and chairs. Guild Registrar Brom will mention the table's roundness at least twice per visit.

**NPCs:**
- **Guild Registrar Brom** (`npc_brom`, generic) — Handles guild formation with meticulous attention. Very fond of the round table.

---

## sentinel

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `sentinel_post` | **The Sentinel's Post** | AwtownRoom | east→teal_sw |

### The Sentinel's Post (`sentinel_post`)

> A narrow guard station cut into the inner face of the south wall. Arrow slits look out over the Lantern Court. Cold even in summer. Watchman Orel has stood this post for eleven years.

**NPCs:**
- **Watchman Orel** (`npc_orel`, quest_giver) — A watchman who has stood the same post for eleven years without complaint.

---

## shadow

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `shadow_chamber` | **The Shadow Chamber** | AwtownRoom | south→fw_5 |

### The Shadow Chamber (`shadow_chamber`)

> A plain room with a round table and six chairs, no windows, no decoration. Used by town guard leadership and, unofficially, by the local Thieves' Guild liaison.

---

## shrine_of_first

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `shrine_of_first_light` | **The Shrine of First Light** | AwtownRoom | west→tl_2 |

### The Shrine of First Light (`shrine_of_first_light`)

> A candlelit devotional alcove off Templegate Lane. A carved stone basin holds offerings. Acolyte Ren keeps the candles burning with teenage earnestness.

**NPCs:**
- **Acolyte Ren** (`npc_acolyte_ren`, merchant) — An earnest seventeen-year-old managing the Shrine with more enthusiasm than authority.

---

## southern

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `southern_outlook` | **The Southern Outlook** | AwtownExteriorRoom | west→teal_sw |

### The Southern Outlook (`southern_outlook`)

> A windswept overlook on the south wall of Awtown, east of the Lantern Court. The view south is unobstructed.

---

## stables

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `stables_ne` | **The South Stables** | AwtownExteriorRoom | south→stables_se, west→stables_nw |
| `stables_nw` | **The North Stables** | AwtownExteriorRoom | east→stables_ne, south→stables_sw |
| `stables_se` | **The Stable Yard** | AwtownExteriorRoom | north→stables_ne, west→stables_sw |
| `stables_sw` | **The Tack Room** | AwtownExteriorRoom | east→stables_se, north→stables_nw, south→gate_side [city_gate] |

### The South Stables (`stables_ne`)

> The older wing of the paddock, used for working horses and pack animals. A water trough runs the length of the south wall.

### The North Stables (`stables_nw`)

> Long rows of horse stalls line both sides. Breeds from across Dorfin fill the stalls. Tack hangs on wall hooks between them.

### The Stable Yard (`stables_se`)

> A cobbled yard open to the sky for walking, watering, and trading horses. Grooms move with practised efficiency. The clatter of hooves on stone is constant.

**NPCs:**
- **Groom Pip** (`npc_groom_pip`, generic) — A cheerful young stable hand who is always in a hurry and always has a carrot ready.

### The Tack Room (`stables_sw`)

> Every wall is hung with saddles, bridles, halters, and riding gear. The smell of leather and saddle oil is overwhelming but pleasant.

**NPCs:**
- **Stableman Oswin** (`npc_oswin`, merchant) — A weathered old horseman who can assess a horse's temperament in thirty seconds.

---

## stewards

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `stewards_hall` | **The Steward's Hall** | AwtownRoom | south→fw_6 |

### The Steward's Hall (`stewards_hall`)

> A tidy administrative office where the town's logistics are managed. Bulletin boards, ledgers, and supply manifests cover every surface.

**NPCs:**
- **Steward Pell** (`npc_pell`, quest_giver) — An efficient, no-nonsense woman who manages the town's logistics without wasting a minute.
- **Clerk Nimble** (`npc_nimble`, generic) — A young halfling assistant, quick with a quill and quicker with a filing system.

---

## study

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `study_hall` | **The Study Hall** | AwtownRoom | north→cr_2 |

### The Study Hall (`study_hall`)

> The quieter sibling of the Apprentice Hall. Rows of desks, reference books, and chalkboards. Scholar Bevin supervises. Student Mop is asleep at a back desk.

**NPCs:**
- **Scholar Bevin** (`npc_bevin`, trainer) — A calm, patient young woman who ended up as the Study Hall's unofficial supervisor.
- **Student Mop** (`npc_student_mop`, generic) — Always asleep at a desk. Has never failed a lesson. Nobody knows how.

---

## supply

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `supply_room` | **The Supply Room** | AwtownRoom | north→teal_main |

### The Supply Room (`supply_room`)

> A general overflow storage room, less organised than the Quartermaster's Cache. Things end up here when there is nowhere better. Stock Boy Fen is doing his best.

**NPCs:**
- **Stock Boy Fen** (`npc_fen`, quest_giver) — A teenage helper who is not very organised but is enthusiastic.

---

## tavern

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `tavern_ne` | **The Kitchen** | AwtownRoom | south→tavern_se [kitchen door], west→tavern_nw |
| `tavern_nw` | **The Common Room** | AwtownRoom | east→tavern_ne, north→temple_sw, south→tavern_sw |
| `tavern_se` | **The Stage** | AwtownRoom | east→teal_server, north→tavern_ne [kitchen door], west→tavern_sw |
| `tavern_sw` | **The Inn Counter** | AwtownRoom | east→tavern_se, north→tavern_nw, west→lr_6 |

### The Kitchen (`tavern_ne`)

> Cook Darra's domain, run with iron efficiency and complete intolerance for uninvited visitors. The smell is extraordinary. A latched door to the south bears a 'Kitchen Staff Only' sign.

**NPCs:**
- **Cook Darra** (`npc_darra`, generic) — The undisputed ruler of the kitchen. She does not welcome visitors.

### The Common Room (`tavern_nw`)

> The social heart of Awtown. Every bench is occupied, the hearth blazes, and the smell of roasting meat and spilled ale saturates everything pleasantly.

**NPCs:**
- **Barkeep Finn** (`npc_finn`, merchant) — Quick wit and quicker hands. Serves drinks without spilling and information without effort.

### The Stage (`tavern_se`)

> A small raised wooden platform occupies the southeast corner of the inn, ringed by mismatched benches worn smooth from years of enthusiastic audiences. Scuff marks and candle-wax drippings cover the stage. The east passage leads into the Humming Court.

**NPCs:**
- **Lute-player Cobble** (`npc_cobble`, generic) — A wandering bard of considerable skill and terrible grace under requests.

### The Inn Counter (`tavern_sw`)

> A worn counter of dark wood, pigeonholes for keys on the wall behind it. Innkeeper Bess Copperladle takes lodging payments here with warm efficiency.

**NPCs:**
- **Innkeeper Bess Copperladle** (`npc_bess`, innkeeper) — Warm, formidable, with a memory for faces that borders on unsettling.

---

## teal

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `teal_main` | **The Cartographer's Den** | AwtownCourtyardRoom | east→lr_3, south→supply_room, west→ww_3 [gate] |
| `teal_ne` | **The Gilded Passage** | AwtownCourtyardRoom | north→fw_11, south→outfitters_rest |
| `teal_server` | **The Humming Court** | AwtownCourtyardRoom | east→crystal_repository, north→tl_2, west→tavern_se |
| `teal_sw` | **The Lantern Court** | AwtownCourtyardRoom | east→cr_1 [gate], north→ww_7 [gate], south→gate_back [gate], southwest→precipice, west→sentinel_post |

### The Cartographer's Den (`teal_main`)

> An open stone courtyard enclosed by the buildings around it. A large covered drafting table sits at the centre, its canvas awning weighted against the wind. Rolled maps are pinned under stones.

**NPCs:**
- **Mapper Izra** (`npc_izra`, trainer) — A meticulous gnome cartographer who has personally charted more of Dorfin than anyone alive.

### The Gilded Passage (`teal_ne`)

> A covered passage lit by warm amber lanterns, connecting Founder's Walk to the Outfitter's Rest. The walls are clean stone; the air smells faintly of cedar.

### The Humming Court (`teal_server`)

> A stone-flagged courtyard centred on a crystal formation that hums just below the threshold of hearing. The vibration is felt through the soles of your boots.

### The Lantern Court (`teal_sw`)

> A low courtyard in Awtown's southern quarter, ringed by the town wall on two sides. Iron lanterns on poles keep it lit at all hours. A dramatic stone shelf juts out to the southwest.

---

## temple

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `temple_ne` | **The Sanctuary** | AwtownRoom | north→fw_6, south→temple_se, west→temple_nw |
| `temple_nw` | **The Nave** | AwtownRoom | east→temple_ne, south→temple_sw |
| `temple_se` | **The Bell Tower** | AwtownRoom | north→temple_ne, up→bell_upper, west→temple_sw |
| `temple_sw` | **The Vestry** | AwtownRoom | east→temple_se, north→temple_nw, south→tavern_nw |

### The Sanctuary (`temple_ne`)

> A quieter, candlelit wing for healing and restoration. The air smells of herbs and clean linen. Sister Sera tends to the wounded here with more enthusiasm than precision.

**NPCs:**
- **Sister Sera** (`npc_sister_sera`, merchant) — An enthusiastic young priestess still mastering some of her healing spells.

### The Nave (`temple_nw`)

> The main chamber of the Temple of the Eternal Flame. The ceiling is vaulted. Rows of worn pews face an altar where the Eternal Flame burns in a brass bowl — it has not gone out in recorded memory.

**NPCs:**
- **High Priest Edwyn Lux** (`npc_edwyn_lux`, merchant) — A solemn, kind man who oversees all temple functions with gentle authority.

### The Bell Tower (`temple_se`)

> The base of the Temple's bell tower, where stairs begin climbing upward. Paladin-Warden Thane Dusk trains students here amid worn practice equipment.

**NPCs:**
- **Paladin-Warden Thane Dusk** (`npc_thane_dusk`, trainer) — A battle-scarred retired paladin who trains others. Gruff, absolutely honourable.

### The Vestry (`temple_sw`)

> A room of robes, ritual objects, and prayer texts in careful order. Brother Aldwin's domain. Cleric training is available here.

**NPCs:**
- **Brother Aldwin** (`npc_aldwin`, trainer) — A formal, serious cleric trainer who expects dedication.

---

## test_arena

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `test_arena_east` | **Arena East** | AwtownRoom | south→test_arena_south, west→test_arena_north |
| `test_arena_north` | **Arena North** | AwtownRoom | east→test_arena_east, south→test_arena_west, training→training_yard |
| `test_arena_south` | **Arena South** | AwtownRoom | north→test_arena_east, west→test_arena_west |
| `test_arena_west` | **Arena West** | AwtownRoom | east→test_arena_south, north→test_arena_north |

### Arena East (`test_arena_east`)

> A cobblestone yard with torch sconces bolted to iron posts. A sign reads: '|wPatrol Route|n'. Exits lead north and south.

### Arena North (`test_arena_north`)

> A sandy clearing ringed by wooden fences. Scuff marks cover the ground. A weathered sign reads: '|wWander Zone|n'. Exits lead east and west.

### Arena South (`test_arena_south`)

> A muddy pit surrounded by sharpened stakes. A sign reads: '|wChase Zone — watch your back|n'. Exits lead east and west.

### Arena West (`test_arena_west`)

> An empty stretch of hard-packed dirt. Good for observing mob arrivals. A sign reads: '|wObservation Point|n'. Exits lead north and south.

---

## tinker

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `tinker_den` | **The Tinker's Den** | AwtownRoom | north→crystal_repository, south→cr_4 |

### The Tinker's Den (`tinker_den`)

> A cluttered den of gears, springs, lenses, and gadgets. The smell of oil is overwhelming. Automaton Tick sweeps the floor and occasionally says something surprisingly profound.

**NPCs:**
- **Cogwright Fenn** (`npc_fenn`, trainer) — Marro's oldest friend. Sells mechanical components and trains tinkerers hands-on.
- **Automaton Tick** (`npc_tick`, generic) — A small mechanical construct that sweeps the floor and occasionally says something profound.

---

## tl

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `tl_1` | **Templegate Lane** | AwtownRoadRoom | north→fw_7, south→tl_2 |
| `tl_2` | **Templegate Lane** | AwtownRoadRoom | east→shrine_of_first_light, north→tl_1, south→teal_server |

### Templegate Lane (`tl_1`)

> A short lane of well-worn stones connecting Founder's Walk to the Temple precinct below. Pilgrims move quietly in either direction at most hours.

### Templegate Lane (`tl_2`)

> The lower end of Templegate Lane. The Shrine of First Light glows softly to the east. The Humming Court lies to the south.

---

## training

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `training_yard` | **The Training Yard** | AwtownRoom | arena→test_arena_north, barracks→warden_barracks |

### The Training Yard (`training_yard`)

> A walled yard of packed dirt behind the Warden's Barracks. Straw dummies and weapon racks line the walls. Scuff marks and dried bloodstains suggest this place sees heavy use. A sign reads: '|wHit things here. Not in town.|n'

---

## vault_of

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `vault_of_gold` | **The Vault of Gold** | AwtownRoom | north→fw_8 |

### The Vault of Gold (`vault_of_gold`)

> A squat stone building with a heavy iron door. Polished wood counters, barred windows, and the air of serious finance. Banker Guildred Copperpot handles everything with gnomish precision.

**NPCs:**
- **Banker Guildred Copperpot** (`npc_guildred`, banker) — A gnome banker of absolute precision and immovable principles. He speaks in decimal points.
- **Vault Guard Holt** (`npc_holt`, guard) — An enormous human in chainmail who communicates primarily through presence.

---

## warden

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `warden_barracks` | **The Warden's Barracks** | AwtownRoom | south→fw_1, yard→training_yard |

### The Warden's Barracks (`warden_barracks`)

> A long, practical room smelling of leather polish and cold iron. Bunk frames and weapons racks line opposite walls. A duty roster and wanted-notice board hang beside the door.

**NPCs:**
- **Sergeant Dorn** (`npc_dorn`, trainer) — A scarred veteran with a permanent scowl and a dry sense of humour.
- **Guard Recruit Pip** (`npc_recruit_pip`, generic) — First week on the job, nervously polishing a helmet that is too large for him.

---

## washhouse

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `washhouse` | **The Washhouse** | AwtownRoom | east→ww_3 |
| `washhouse_lower` | **The Washhouse (Lower)** | AwtownRoom | east→ww_6 |

### The Washhouse (`washhouse`)

> A surprisingly pleasant public washhouse with warm water always available. Clean towels smell faintly of lavender. Certain trail debuffs clear faster here.

### The Washhouse (Lower) (`washhouse_lower`)

> A second public washhouse serving the southern end of Warden's Way, identical in appointments with slightly better water pressure.

---

## watchtower

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `watchtower` | **The Watchtower** | AwtownRoom | east→ww_7 |

### The Watchtower (`watchtower`)

> A narrow stone tower. Arrow slits look out over the southern approaches. Watchman Teris maintains a sharp eye here and turns distant sightings into quests.

**NPCs:**
- **Watchman Teris** (`npc_teris`, quest_giver) — A sharp-eyed half-elf ranger who notices what moves on the horizon.

---

## ww

| Room Key | Name | Type | Exits |
|----------|------|------|-------|
| `ww_1` | **Along Warden's Way** | AwtownRoadRoom | north→fw_1, south→ww_2, west→guardroom |
| `ww_2` | **Along Warden's Way** | AwtownRoadRoom | north→ww_1, south→ww_3 |
| `ww_3` | **Along Warden's Way** | AwtownRoadRoom | east→teal_main [gate], north→ww_2, south→ww_4, west→washhouse |
| `ww_4` | **Along Warden's Way** | AwtownRoadRoom | east→ww_5, north→ww_3, west→pantry |
| `ww_5` | **Along Warden's Way** | AwtownRoadRoom | south→ww_6, west→ww_4 |
| `ww_6` | **Along Warden's Way** | AwtownRoadRoom | north→ww_5, south→ww_7, west→washhouse_lower |
| `ww_7` | **Along Warden's Way** | AwtownRoadRoom | north→ww_6, south→teal_sw [gate], west→watchtower |

### Along Warden's Way (`ww_1`)

> Warden's Way turns south off Founder's Walk here. A quieter road for craftsmen and those who know the side streets. The Guardroom door is just to the west.

### Along Warden's Way (`ww_2`)

> A mid-stretch of Warden's Way. The buildings press close; cobblestones are rougher here.

### Along Warden's Way (`ww_3`)

> The Washhouse offers its services to the west. An iron-banded gate to the east opens into the Cartographer's Den courtyard.

### Along Warden's Way (`ww_4`)

> Warden's Way bends briefly east here. The Pantry's plain door is to the west.

### Along Warden's Way (`ww_5`)

> A brief eastern jog in the road. The stones are worn smooth by years of wheelbarrow traffic.

### Along Warden's Way (`ww_6`)

> The second Washhouse occupies the western wall. The forge district is very close; the smell of hot metal is constant.

### Along Warden's Way (`ww_7`)

> The southern terminus of Warden's Way. The Watchtower's narrow door is to the west. A heavy gate to the south leads into the Lantern Court.

---

