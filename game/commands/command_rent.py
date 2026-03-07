"""
Rent room command
=================

    rent room   -- rent a room at the Hearthstone Inn for the night

Must be used at the Inn Counter (room tag: tavern_sw).
Costs 20 copper. Starts a RentScript that slowly restores HP and needs.

Innkeeper Bess Copperladle handles check-in and check-out messages.

Depends on:
    typeclasses.characters.AwtownCharacter -- heal(), restore_hunger/thirst()
"""

from evennia.commands.command import Command
from evennia import DefaultScript


RENT_COST      = 20    # copper
RENT_DURATION  = 60    # seconds of in-game rest
RENT_HP        = 40    # HP restored over the full rest
RENT_HUNGER    = 30    # hunger restored over the full rest
RENT_THIRST    = 30    # thirst restored over the full rest
RENT_ROOM_TAG  = "tavern_sw"
TICKS          = 6     # number of script repeats over RENT_DURATION
TICK_INTERVAL  = RENT_DURATION // TICKS


class RentScript(DefaultScript):
    """
    Temporary script attached to a character during their rest.
    Restores HP, hunger, and thirst in small increments each tick.
    Sends flavour messages at each stage.
    """

    MESSAGES = [
        "You settle into the warm bed. The inn's sounds fade to a comfortable murmur.",
        "Your muscles begin to unknot. You feel yourself relaxing.",
        "Halfway through your rest. You feel considerably better.",
        "Sleep tugs at you. You drift in and out of a comfortable doze.",
        "You stretch lazily. Nearly rested.",
        "|gYou wake refreshed. The room has been well worth the coin.|n",
    ]

    def at_script_creation(self):
        self.key = "RentScript"
        self.desc = "Resting at the Hearthstone Inn."
        self.interval = TICK_INTERVAL
        self.repeats = TICKS
        self.persistent = False
        self.db.tick_count = 0

    def at_repeat(self):
        obj = self.obj
        if not obj:
            self.stop()
            return

        tick = self.db.tick_count or 0

        # Restore a portion each tick
        hp_per_tick      = RENT_HP     // TICKS
        hunger_per_tick  = RENT_HUNGER // TICKS
        thirst_per_tick  = RENT_THIRST // TICKS

        if hasattr(obj, "heal"):
            obj.heal(hp_per_tick)
        if hasattr(obj, "restore_hunger"):
            obj.restore_hunger(hunger_per_tick)
        if hasattr(obj, "restore_thirst"):
            obj.restore_thirst(thirst_per_tick)

        # Send message
        msg = self.MESSAGES[min(tick, len(self.MESSAGES) - 1)]
        obj.msg(msg)

        self.db.tick_count = tick + 1

    def at_stop(self):
        obj = self.obj
        if obj:
            obj.db.is_resting = False


class CmdRentRoom(Command):
    """
    Rent a room at the Hearthstone Inn for the night.

    Usage:
        rent room

    Cost: 20 copper. Must be at the Inn Counter (inside the Hearthstone Inn).

    Renting a room restores your health, hunger, and thirst gradually
    over one minute of real time. You can move around while resting
    but leaving the inn area will interrupt your rest.

    Innkeeper Bess Copperladle handles all check-ins.
    """

    key = "rent room"
    aliases = ["rent", "checkin", "check in"]
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller

        # Must be at the Inn Counter
        if not caller.location or not caller.location.tags.get(RENT_ROOM_TAG, category="awtown_room"):
            caller.msg(
                "You need to be at the Inn Counter inside the Hearthstone Inn.\n"
                "Find Innkeeper Bess Copperladle to rent a room."
            )
            return

        # Already resting?
        if caller.scripts.get("RentScript"):
            caller.msg("You're already resting. Give it a moment.")
            return

        # Check funds
        copper = caller.db.copper or 0
        if copper < RENT_COST:
            caller.msg(
                f"Bess shakes her head. 'A night's rest costs {RENT_COST} copper, "
                f"love. You've only got {copper}.'"
            )
            return

        # Take payment
        caller.spend_copper(RENT_COST)

        # Find Bess and have her speak
        bess = None
        for obj in caller.location.contents:
            if hasattr(obj, "db") and obj.db.npc_role and "innkeeper" in str(obj.db.npc_role).lower():
                bess = obj
                break

        if bess:
            caller.location.msg_contents(
                f"|c{bess.name}|n takes {caller.name}'s coin and hands over a brass key. "
                f"'Room three, top of the stairs. Sleep well.'",
            )
        else:
            caller.msg(
                f"You pay {RENT_COST} copper and receive a brass key. "
                f"'Room three, top of the stairs.'"
            )

        # Start rest script
        caller.db.is_resting = True
        caller.scripts.add(RentScript)
