"""
batch_export_data.py  —  Export live world to batch_awtown-style data tuples
Run with:  @batchcode world.batch_export_data

Writes /usr/src/game/server/world_export_data.txt
Copy to repo:  kubectl exec deploy/evennia -c evennia -- cat /usr/src/game/server/world_export_data.txt > reference/world_export_data.txt
"""

# HEADER

import evennia
from typeclasses.exits import AwtownGate, AwtownCityGate

ROOM_TAG = "awtown_dbkey"
NPC_TAG  = "awtown_npc"
OUTFILE  = "/usr/src/game/server/world_export_data.txt"

# ── Gather rooms ─────────────────────────────────────────────────────────────

rooms_by_key = {}
for room in evennia.search_tag(category=ROOM_TAG):
    db_key = room.tags.get(category=ROOM_TAG)
    if not db_key:
        continue
    # Determine type key from typeclass
    tc_name = type(room).__name__
    tc_map = {
        "AwtownRoadRoom": "road",
        "AwtownCourtyardRoom": "courtyard",
        "AwtownExteriorRoom": "exterior",
        "AwtownRoom": "building",
    }
    tc_key = tc_map.get(tc_name, "building")
    desc = room.db.desc or ""
    rooms_by_key[db_key] = (db_key, room.name, tc_key, desc)

# ── Gather exits ─────────────────────────────────────────────────────────────

exit_rows = []
for db_key, (_, _, _, _) in sorted(rooms_by_key.items()):
    room = evennia.search_tag(db_key, category=ROOM_TAG)[0]
    for ex in sorted(room.exits, key=lambda e: e.key):
        dest = ex.destination
        if not dest:
            continue
        dest_key = dest.tags.get(category=ROOM_TAG)
        if not dest_key:
            continue
        # Determine exit type
        if isinstance(ex, AwtownCityGate):
            etype = "city_gate"
        elif isinstance(ex, AwtownGate):
            etype = "gate"
        else:
            etype = "std"
        gate_name = ex.db.gate_name if hasattr(ex.db, 'gate_name') and ex.db.gate_name else None
        alias = ex.aliases.all()[0] if ex.aliases.all() else ex.key[0]
        exit_rows.append((db_key, ex.key, alias, dest_key, etype, gate_name))

# ── Gather NPCs ──────────────────────────────────────────────────────────────

npc_rows = []
for npc in evennia.search_tag(category=NPC_TAG):
    db_key = npc.tags.get(category=NPC_TAG)
    if not db_key:
        continue
    loc_key = None
    if npc.location:
        loc_key = npc.location.tags.get(category=ROOM_TAG)
    desc = npc.db.desc or ""
    role = npc.db.npc_role or "generic"
    npc_rows.append((db_key, npc.name, desc, loc_key or "UNKNOWN", role))

# ── Write output ─────────────────────────────────────────────────────────────

lines = []
lines.append("# World Export — batch_awtown data format")
lines.append(f"# {len(rooms_by_key)} rooms, {len(exit_rows)} exits, {len(npc_rows)} NPCs")
lines.append("")

lines.append("ROOM_DATA = [")
for key in sorted(rooms_by_key):
    db_key, name, tc_key, desc = rooms_by_key[key]
    lines.append(f'    ("{db_key}","{name}","{tc_key}",')
    lines.append(f'     "{desc}"),')
lines.append("]")
lines.append("")

lines.append("EXIT_DATA = [")
for row in exit_rows:
    from_key, direction, alias, to_key, etype, gate_name = row
    gn = f'"{gate_name}"' if gate_name else "None"
    lines.append(f'    ("{from_key}","{direction}","{alias}","{to_key}","{etype}",{gn}),')
lines.append("]")
lines.append("")

lines.append("NPC_DATA = [")
for row in sorted(npc_rows, key=lambda r: r[0]):
    db_key, name, desc, loc_key, role = row
    lines.append(f'    ("{db_key}","{name}",')
    lines.append(f'     "{desc}",')
    lines.append(f'     "{loc_key}","{role}"),')
lines.append("]")

with open(OUTFILE, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

caller.msg(f"|g[batch_export_data] Wrote {OUTFILE}|n")
caller.msg(f"|g  {len(rooms_by_key)} rooms, {len(exit_rows)} exits, {len(npc_rows)} NPCs.|n")
