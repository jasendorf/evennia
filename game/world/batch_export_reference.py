"""
batch_export_reference.py  —  Export live world to a readable markdown reference
Run with:  @batchcode world.batch_export_reference

Writes /usr/src/game/server/world_export_reference.md
Copy to repo:  kubectl exec deploy/evennia -c evennia -- cat /usr/src/game/server/world_export_reference.md > reference/world_export_reference.md
"""

# HEADER

import evennia
from typeclasses.exits import AwtownGate, AwtownCityGate

ROOM_TAG = "awtown_dbkey"
NPC_TAG  = "awtown_npc"
OUTFILE  = "/usr/src/game/server/world_export_reference.md"

# ── Gather all data ──────────────────────────────────────────────────────────

rooms = {}
for room in evennia.search_tag(category=ROOM_TAG):
    db_key = room.tags.get(category=ROOM_TAG)
    if db_key:
        rooms[db_key] = room

npcs_by_room = {}
for npc in evennia.search_tag(category=NPC_TAG):
    npc_key = npc.tags.get(category=NPC_TAG)
    if not npc_key or not npc.location:
        continue
    loc_key = npc.location.tags.get(category=ROOM_TAG)
    if loc_key:
        npcs_by_room.setdefault(loc_key, []).append(npc)

# ── Group rooms by area prefix ───────────────────────────────────────────────

areas = {}
for db_key, room in sorted(rooms.items()):
    # Use prefix before underscore, or the full key if no underscore
    prefix = db_key.rsplit("_", 1)[0] if "_" in db_key else db_key
    areas.setdefault(prefix, []).append((db_key, room))

# ── Build markdown ───────────────────────────────────────────────────────────

lines = []
lines.append("# DorfinMUD — Live World Export")
lines.append("")
lines.append(f"**{len(rooms)} rooms** | **{sum(len(v) for v in npcs_by_room.values())} NPCs**")
lines.append("")
lines.append("---")
lines.append("")

for area_prefix in sorted(areas):
    area_rooms = areas[area_prefix]
    # Use the first room's name prefix as area title
    lines.append(f"## {area_prefix}")
    lines.append("")
    lines.append("| Room Key | Name | Type | Exits |")
    lines.append("|----------|------|------|-------|")

    for db_key, room in area_rooms:
        tc_name = type(room).__name__
        exit_strs = []
        for ex in sorted(room.exits, key=lambda e: e.key):
            dest = ex.destination
            dest_key = dest.tags.get(category=ROOM_TAG) if dest else "?"
            marker = ""
            if isinstance(ex, AwtownCityGate):
                marker = " [city_gate]"
            elif isinstance(ex, AwtownGate):
                gate_name = ex.db.gate_name or "gate"
                marker = f" [{gate_name}]"
            exit_strs.append(f"{ex.key}→{dest_key}{marker}")
        exits_str = ", ".join(exit_strs) if exit_strs else "none"
        lines.append(f"| `{db_key}` | **{room.name}** | {tc_name} | {exits_str} |")

    lines.append("")

    # Room details
    for db_key, room in area_rooms:
        desc = room.db.desc or "(no description)"
        lines.append(f"### {room.name} (`{db_key}`)")
        lines.append("")
        lines.append(f"> {desc}")
        lines.append("")

        room_npcs = npcs_by_room.get(db_key, [])
        if room_npcs:
            lines.append("**NPCs:**")
            for npc in room_npcs:
                npc_key = npc.tags.get(category=NPC_TAG)
                role = npc.db.npc_role or "generic"
                npc_desc = npc.db.desc or ""
                lines.append(f"- **{npc.name}** (`{npc_key}`, {role}) — {npc_desc}")
            lines.append("")

    lines.append("---")
    lines.append("")

with open(OUTFILE, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

caller.msg(f"|g[batch_export_reference] Wrote {OUTFILE}|n")
caller.msg(f"|g  {len(rooms)} rooms across {len(areas)} areas.|n")
