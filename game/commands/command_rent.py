"""
Rent room command
=================

    rent room   -- rent a room from a renter NPC

Must be used in a room tagged with the "room_can_rent" tag (category
"awtown_room_type"). Any room can support renting as long as it has that
tag and contains at least one NPC with db.is_renter = True.

Cost defaults to RENT_COST but can be overridden per NPC via db.rent_cost.
Starts a RentScript that heals to full HP over 30 seconds (6 x 5s ticks).
Also restores hunger and thirst incrementally.

Renting is SEPARATE from resting:
    - Renting  : db.is_renting = True, uninterruptable, 30s, full recovery,
                 costs copper, requires a renter NPC, safe from mob aggro.
    - Resting  : db.is_resting = True, interruptable, 6s, 5% HP recovery,
                 free, usable anywhere, NOT safe from mob aggro.

Renter NPC stub attributes (all optional — fallbacks are built in):
    db.is_renter           = True        required to be found as a renter
    db.rent_cost           = int         copper cost (overrides RENT_COST)
    db.msg_combat_refusal  = str         said when player is in combat
    db.msg_wellrested      = str         said when player is at 80%+ health
    db.msg_checkin         = str         said privately to the player on check-in
    db.msg_checkin_room    = str         broadcast to room on check-in
    db.msg_checkout        = str         said privately to player on waking
    db.msg_checkout_room   = str         broadcast to room on check-out

All dialogue strings support .format() placeholders. Available variables
per message type:

    msg_combat_refusal  : {npc}, {name}, {cost}
    msg_wellrested      : {npc}, {name}, {cost}
    msg_checkin         : {npc}, {name}, {cost}
    msg_checkin_room    : {npc}, {name}, {cost}
    msg_checkout        : {npc}, {name}          (cost not available at checkout)
    msg_checkout_room   : {npc}, {name}

Example Bess attribute values:
    db.msg_combat_refusal = "|cBess|n plants her hands on the counter. 'I won't rent to you while you're fighting in my inn!'"
    db.msg_wellrested     = "|cBess|n squints at you. 'You look pretty hale to me, {name}. Sure you need a room? It\\'s {cost}.'"
    db.msg_checkin_room   = "|cBess|n takes {name}\\'s coin and hands over a brass key. 'Room three, top of the stairs. Sleep well.'"
    db.msg_checkin        = "You pay {cost} and follow Bess upstairs. The room smells of pine soap and old wood."
    db.msg_checkout       = "You gather your things and head downstairs, rested and ready."
    db.msg_checkout_room  = "|w{name}|n emerges from the stairs looking considerably more alert."

Depends on:
    typeclasses.characters.AwtownCharacter -- heal(), restore_hunger/thirst()
"""

import math

from evennia.commands.command import Command
from evennia.commands.cmdset import CmdSet
from evennia.commands.cmdhandler import CMD_NOMATCH
from evennia import DefaultScript
from typeclasses.characters import format_money


# ---------------------------------------------------------------------------
# Module-level defaults
# ---------------------------------------------------------------------------

RENT_COST      = 20    # copper (can be overridden per NPC via db.rent_cost)
RENT_HUNGER    = 30    # hunger points restored over the full stay
RENT_THIRST    = 30    # thirst points restored over the full stay
RENT_ROOM_TAG  = "room_can_rent"   # room tag category: "awtown_room_type"
TICKS          = 6     # number of recovery ticks
TICK_INTERVAL  = 5     # seconds between ticks  (6 x 5 = 30 seconds total)
HP_WELL_RESTED = 0.80  # HP ratio above which the NPC warns the player


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_renter_npc(location):
    """
    Return the first NPC in the room that has db.is_renter = True,
    or None if no such NPC is present.
    """
    for obj in location.contents:
        if getattr(obj.db, "is_renter", False):
            return obj
    return None


def _npc_msg(npc_obj, attr, fallback, **kwargs):
    """
    Return the NPC's custom dialogue string for *attr* if set,
    otherwise return *fallback*. Any keyword arguments are interpolated
    into the string via .format(), so NPC dialogue can reference
    context variables by name.

    Available placeholders (pass as kwargs at each call site):
        {npc}   -- the NPC's name
        {name}  -- the renting player's name
        {cost}  -- the formatted copper cost string (e.g. "20 copper")

    Example NPC attribute value:
        "|cBess|n says, 'That'll be {cost}, {name}. Sleep well.'"

    If format() fails for any reason the raw string is returned as-is
    so a misconfigured NPC attribute never raises an error mid-session.
    """
    custom = getattr(npc_obj.db, attr, None) if npc_obj else None
    template = custom if custom else fallback
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template
    return template


def _night_fraction(tick_count, total_ticks):
    """
    Return a human-readable fraction string for how far through the
    night the player is, reduced to lowest terms.

    tick_count is the number of ticks *already completed* (0-based).

    Examples (total_ticks=6):
        0 -> special: "just drifted off"
        1 -> "1/6"
        2 -> "1/3"
        3 -> "1/2"
        4 -> "2/3"
        5 -> "5/6"
    """
    if tick_count == 0:
        return None   # caller handles the zero case
    divisor = math.gcd(tick_count, total_ticks)
    num   = tick_count // divisor
    denom = total_ticks // divisor
    return f"{num}/{denom}"


# ---------------------------------------------------------------------------
# RentCmdSet  — applied to the character while renting
# ---------------------------------------------------------------------------

class CmdRentIntercept(Command):
    """
    Intercepts ALL commands while the character is renting a room.
    Renting is uninterruptable: the first attempt warns with how far
    through the night they are; subsequent attempts repeat the warning.
    The script always completes on its own schedule.
    """

    key = CMD_NOMATCH
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        scripts = caller.scripts.get("RentScript")

        if not scripts:
            # Script is gone (finished or error) — clean up the cmdset
            try:
                caller.cmdset.remove("RentCmdSet")
            except Exception:
                pass
            caller.execute_cmd(self.raw_string)
            return

        script = scripts[0]
        tick_done = script.db.tick_count or 0
        fraction  = _night_fraction(tick_done, TICKS)

        if fraction is None:
            progress = "you've only just drifted off"
        else:
            progress = f"you're {fraction} of the way through the night"

        caller.msg(
            f"|yYou can't do that in your sleep! {progress.capitalize()}.|n"
        )


class RentCmdSet(CmdSet):
    key = "RentCmdSet"
    priority = 200
    mergetype = "Replace"
    no_exits = True
    no_objs = True

    def at_cmdset_creation(self):
        self.add(CmdRentIntercept())


# ---------------------------------------------------------------------------
# RentScript
# ---------------------------------------------------------------------------

class RentScript(DefaultScript):
    """
    Temporary script attached to a character while renting a room.

    Heals to full HP over 30 seconds (6 ticks x 5 seconds).
    Also restores hunger and thirst incrementally.

    db Attributes:
        tick_count  (int) : ticks completed so far (used for fraction display)
        hp_per_tick (int) : HP healed each tick (calculated once at start)
    """

    DEFAULT_MESSAGES = [
        "You settle into the warm bed. The inn's sounds fade to a comfortable murmur.",
        "Your muscles begin to unknot. You feel yourself relaxing.",
        "You drift in and out of a light, comfortable doze.",
        "Halfway through your rest — you feel considerably better.",
        "Sleep tugs at you deeply. Nearly there.",
        "|gYou wake refreshed. The room has been well worth the coin.|n",
    ]

    def at_script_creation(self):
        self.key = "RentScript"
        self.desc = "Renting a room to recover."
        self.interval = TICK_INTERVAL
        self.repeats = TICKS
        self.start_delay = True
        self.persistent = False
        self.db.tick_count = 0
        self.db.hp_per_tick = 0

    def at_start(self):
        obj = self.obj
        if obj and hasattr(obj, "get_hp") and hasattr(obj, "get_hp_max"):
            missing = obj.get_hp_max() - obj.get_hp()
            self.db.hp_per_tick = max(1, missing // TICKS) if missing > 0 else 0

    def at_repeat(self):
        obj = self.obj
        if not obj:
            self.stop()
            return

        tick = self.db.tick_count or 0

        # --- Heal HP ---
        hp_per_tick = self.db.hp_per_tick or 0
        healed = 0
        if hasattr(obj, "heal"):
            if tick == TICKS - 1:
                # Last tick: top off any remainder to guarantee full recovery
                healed = obj.get_hp_max() - obj.get_hp()
                if healed > 0:
                    obj.heal(healed)
            elif hp_per_tick:
                obj.heal(hp_per_tick)
                healed = hp_per_tick

        # --- Restore hunger / thirst ---
        hunger_per_tick = RENT_HUNGER // TICKS
        thirst_per_tick = RENT_THIRST // TICKS
        if hasattr(obj, "restore_hunger"):
            obj.restore_hunger(hunger_per_tick)
        if hasattr(obj, "restore_thirst"):
            obj.restore_thirst(thirst_per_tick)

        # --- Send tick message ---
        msg = self.DEFAULT_MESSAGES[min(tick, len(self.DEFAULT_MESSAGES) - 1)]
        hp_now = obj.get_hp()    if hasattr(obj, "get_hp")     else "?"
        hp_max = obj.get_hp_max() if hasattr(obj, "get_hp_max") else "?"

        if healed > 0:
            obj.msg(f"{msg}  |w(+{healed} HP — {hp_now}/{hp_max} HP)|n")
        else:
            obj.msg(f"{msg}  |w({hp_now}/{hp_max} HP)|n")

        self.db.tick_count = tick + 1

    def at_stop(self):
        obj = self.obj
        if not obj:
            return

        # Clear the renting flag and cmdset
        obj.db.is_renting = False
        try:
            obj.cmdset.remove("RentCmdSet")
        except Exception:
            pass

        # Check-out message from the NPC if still in a rent room
        if obj.location:
            npc = _find_renter_npc(obj.location)
            npc_name = npc.name if npc else "The innkeeper"
            checkout_msg = _npc_msg(
                npc, "msg_checkout",
                "You gather your things and step out, well rested.",
                npc=npc_name, name=obj.name,
            )
            checkout_room = _npc_msg(
                npc, "msg_checkout_room",
                f"|w{obj.name}|n emerges from their room, looking refreshed.",
                npc=npc_name, name=obj.name,
            )
            obj.msg(checkout_msg)
            obj.location.msg_contents(checkout_room, exclude=[obj])


# ---------------------------------------------------------------------------
# CmdRentRoom
# ---------------------------------------------------------------------------

class CmdRentRoom(Command):
    """
    Rent a room to fully recover HP, hunger, and thirst.

    Usage:
        rent room
        rent

    Cost: varies by location. Must be at a location with a renter NPC
    (innkeeper, boarding-house keeper, etc.).

    Renting a room puts you in a safe, uninterruptable recovery state
    for about 30 seconds. Your HP (and hunger/thirst) are restored to
    full over that time. You cannot rent while in combat.

    If your health is already high, the NPC will ask you to confirm.
    Type |wrent|n again to confirm the charge.
    """

    key = "rent room"
    aliases = ["rent", "checkin", "check in"]
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller

        # --- Must be in a room that supports renting ---
        if not caller.location or not caller.location.tags.get(
            RENT_ROOM_TAG, category="awtown_room_type"
        ):
            caller.msg("There's nowhere to rent a room here.")
            return

        # --- Must have a renter NPC present ---
        npc = _find_renter_npc(caller.location)
        if not npc:
            caller.msg("There's no one here to rent you a room.")
            return

        # --- Already renting? ---
        has_rent_flag = getattr(caller.db, "is_renting", False)
        rent_scripts = caller.scripts.get("RentScript")
        has_rent_script = bool(rent_scripts)
        if has_rent_flag and has_rent_script:
            # Genuinely renting — both flag and script present
            caller.msg("You're already asleep in your room.")
            return
        if has_rent_flag or has_rent_script:
            # Orphaned state — flag without script or script without flag.
            # Use delete() not stop() to avoid triggering at_repeat/at_stop.
            caller.db.is_renting = False
            if rent_scripts:
                for s in rent_scripts:
                    s.delete()
            try:
                caller.cmdset.remove("RentCmdSet")
            except Exception:
                pass

        # --- Cannot rent while resting ---
        if getattr(caller.db, "is_resting", False):
            caller.msg("You're already resting. Get up first.")
            return

        # --- Determine cost for this NPC ---
        cost = getattr(npc.db, "rent_cost", None) or RENT_COST

        # --- Cannot rent while in combat ---
        if getattr(caller.db, "in_combat", False):
            refusal = _npc_msg(
                npc, "msg_combat_refusal",
                f"|c{npc.name}|n says, 'I won't rent to you while you're fighting!'",
                npc=npc.name, name=caller.name, cost=format_money(cost),
            )
            caller.msg(refusal)
            return

        # --- Check for pending well-rested confirmation ---
        if caller.ndb._rent_confirm:
            caller.ndb._rent_confirm = False
            self._do_rent(caller, npc, cost)
            return

        # --- Check funds ---
        copper = caller.db.copper or 0
        if copper < cost:
            caller.msg(
                f"|c{npc.name}|n says, 'A night's rest costs {format_money(cost)}. "
                f"You've only got {format_money(copper)}.'"
            )
            return

        # --- Well-rested check: all relevant stats >= 80% ---
        # Currently only HP. Extend this check when mana/movement are added.
        well_rested = False
        if hasattr(caller, "get_hp") and hasattr(caller, "get_hp_max"):
            hp_max = caller.get_hp_max()
            if hp_max > 0 and caller.get_hp() / hp_max >= HP_WELL_RESTED:
                well_rested = True

        if well_rested:
            caller.ndb._rent_confirm = True
            wellrested_msg = _npc_msg(
                npc, "msg_wellrested",
                f"|c{npc.name}|n looks you over. 'You look fairly well rested. "
                f"Are you sure? It's {format_money(cost)}.'\n"
                f"  (type |wrent|n again to confirm)",
                npc=npc.name, name=caller.name, cost=format_money(cost),
            )
            caller.msg(wellrested_msg)
            return

        self._do_rent(caller, npc, cost)

    def _do_rent(self, caller, npc, cost):
        """Charge the player, apply the renting state, and start the script."""
        caller.spend_money(cost)

        # NPC check-in dialogue (to room)
        checkin_room = _npc_msg(
            npc, "msg_checkin_room",
            f"|c{npc.name}|n takes {caller.name}'s coin and hands over a key. "
            f"'Sleep well.'",
            npc=npc.name, name=caller.name, cost=format_money(cost),
        )
        caller.location.msg_contents(checkin_room)

        # Private confirmation to the player
        checkin_msg = _npc_msg(
            npc, "msg_checkin",
            f"You pay {format_money(cost)} and follow {npc.name} upstairs.",
            npc=npc.name, name=caller.name, cost=format_money(cost),
        )
        caller.msg(checkin_msg)

        # Apply renting state
        caller.db.is_renting = True
        caller.cmdset.add("commands.command_rent.RentCmdSet", persistent=False)
        caller.scripts.add(RentScript)