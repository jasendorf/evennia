"""
batch_patch_tavern_stage.py  —  Targeted patch for tavern_se
Run with:  @batchcode world.batch_patch_tavern_stage

Converts tavern_se from "The Cellar" to "The Stage", replaces the
std exits between tavern_se and tavern_ne with AwtownGate (kitchen door),
updates the Kitchen description, and moves Cobble to The Stage.
"""

# HEADER

import evennia
from evennia import create_object
from evennia.objects.objects import DefaultExit
from typeclasses.exits import AwtownGate
from typeclasses.npcs import AwtownNPC

ROOM_TAG = "awtown_dbkey"
NPC_TAG  = "awtown_npc"

def _room(db_key):
    results = evennia.search_tag(db_key, category=ROOM_TAG)
    return results[0] if results else None

# ── Step 1: Update tavern_se room name and description ───────────────────────

tavern_se = _room("tavern_se")
if not tavern_se:
    caller.msg("|rERROR: tavern_se not found. Run batch_awtown first.|n")
else:
    tavern_se.name = "The Stage"
    tavern_se.db.desc = (
        "A small raised wooden platform occupies the southeast corner of the inn, "
        "ringed by mismatched benches worn smooth from years of enthusiastic audiences. "
        "Scuff marks and candle-wax drippings cover the stage. The east passage leads "
        "into the Humming Court."
    )
    caller.msg("|g  Updated tavern_se → 'The Stage'.|n")

# ── Step 2: Update tavern_ne (Kitchen) description ───────────────────────────

tavern_ne = _room("tavern_ne")
if not tavern_ne:
    caller.msg("|rERROR: tavern_ne not found.|n")
else:
    tavern_ne.db.desc = (
        "Cook Darra's domain, run with iron efficiency and complete intolerance "
        "for uninvited visitors. The smell is extraordinary. A latched door to the "
        "south bears a 'Kitchen Staff Only' sign."
    )
    caller.msg("|g  Updated tavern_ne Kitchen description.|n")

# ── Step 3: Replace std exits with AwtownGate (kitchen door) ─────────────────

if tavern_se and tavern_ne:
    # Delete existing exits between the two rooms
    deleted = 0
    for ex in list(tavern_ne.exits):
        if ex.key == "south" and ex.destination == tavern_se:
            ex.delete()
            deleted += 1
    for ex in list(tavern_se.exits):
        if ex.key == "north" and ex.destination == tavern_ne:
            ex.delete()
            deleted += 1
    caller.msg(f"|g  Deleted {deleted} old std exits.|n")

    # Create new AwtownGate exits
    south_exit = create_object(
        AwtownGate, key="south", location=tavern_ne,
        destination=tavern_se, aliases=["s"]
    )
    south_exit.db.gate_name = "kitchen door"

    north_exit = create_object(
        AwtownGate, key="north", location=tavern_se,
        destination=tavern_ne, aliases=["n"]
    )
    north_exit.db.gate_name = "kitchen door"

    # Pair them
    south_exit.db.pair = north_exit
    north_exit.db.pair = south_exit

    caller.msg("|g  Created paired AwtownGate exits (kitchen door).|n")

# ── Step 4: Move Cobble to The Stage ─────────────────────────────────────────

if tavern_se:
    cobble_results = evennia.search_tag("npc_cobble", category=NPC_TAG)
    if cobble_results:
        cobble = cobble_results[0]
        cobble.move_to(tavern_se, quiet=True)
        caller.msg("|g  Moved Cobble to The Stage.|n")
    else:
        caller.msg("|yWarning: npc_cobble not found — skipping move.|n")

caller.msg("|g[batch_patch_tavern_stage] Patch complete.|n")
