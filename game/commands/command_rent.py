"""
Rent room command
=================

    rent room   -- rent a room at the Hearthstone Inn for the night

Must be used at the Inn Counter (room tag: tavern_sw).
Costs 20 copper. Starts a RentScript that slowly restores HP and needs.

During rest, any command triggers a warning. A second command cancels
the rest and executes the interrupted command.

Innkeeper Bess Copperladle handles check-in and check-out messages.

Depends on:
    typeclasses.characters.AwtownCharacter -- heal(), restore_hunger/thirst()
"""

from evennia.commands.command import Command
from evennia.commands.cmdset import CmdSet
from evennia import DefaultScript
from typeclasses.characters import format_money


RENT_COST      = 20    # copper
RENT_HP        = 5     # HP restored over the full rest
RENT_HUNGER    = 30    # hunger restored over the full rest
RENT_THIRST   = 30    # thirst restored over the full rest
RENT_ROOM_TAG  = "tavern_sw"
TICKS          = 6     # number of script repeats
TICK_INTERVAL  = 1     # seconds between ticks (6 ticks = 6 seconds)
HP_WELL_RESTED = 0.80  # 80% HP threshold for "well rested" prompt


class CmdRestIntercept(Command):
    """
    Intercepts commands while resting. First attempt warns,
    second attempt cancels rest and runs the command.
    """

    key = "_default"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        scripts = caller.scripts.get("RentScript")
        if not scripts:
            # Rest already ended, just run the command normally
            caller.cmdset.remove("RestCmdSet")
            caller.execute_cmd(self.raw_string)
            return

        script = scripts[0]
        if script.db.warned:
            # Second attempt — cancel rest and run the command
            script.stop()
            caller.msg("|yYou get up early, interrupting your rest.|n")
            caller.execute_cmd(self.raw_string)
        else:
            # First attempt — warn
            script.db.warned = True
            caller.msg(
                "|yYou stir restlessly. If you get up now you won't "
                "finish healing.|n  (type any command again to get up)"
            )


class RestCmdSet(CmdSet):
    key = "RestCmdSet"
    priority = 200
    mergetype = "Replace"

    def at_cmdset_creation(self):
        self.add(CmdRestIntercept())


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
        self.db.warned = False

    def at_repeat(self):
        obj = self.obj
        if not obj:
            self.stop()
            return

        tick = self.db.tick_count or 0

        # Restore a portion each tick
        hp_per_tick = max(1, RENT_HP // TICKS)
        hunger_per_tick = RENT_HUNGER // TICKS
        thirst_per_tick = RENT_THIRST // TICKS

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
            obj.cmdset.remove("RestCmdSet")


class CmdRentRoom(Command):
    """
    Rent a room at the Hearthstone Inn for the night.

    Usage:
        rent room

    Cost: 20 copper. Must be at the Inn Counter (inside the Hearthstone Inn).

    Renting a room restores your health, hunger, and thirst gradually
    over about 6 seconds. Any command during rest will prompt a warning;
    a second command will cancel the rest early.

    Innkeeper Bess Copperladle handles all check-ins.
    """

    key = "rent room"
    aliases = ["rent", "checkin", "check in"]
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller

        # Must be at the Inn Counter
        if not caller.location or not caller.location.tags.get(RENT_ROOM_TAG, category="awtown_dbkey"):
            caller.msg(
                "You need to be at the Inn Counter inside the Hearthstone Inn.\n"
                "Find Innkeeper Bess Copperladle to rent a room."
            )
            return

        # Already resting?
        if caller.scripts.get("RentScript"):
            caller.msg("You're already resting. Give it a moment.")
            return

        # Check for pending confirmation (well-rested prompt)
        if caller.ndb._rent_confirm:
            caller.ndb._rent_confirm = False
            self._do_rent(caller)
            return

        # Check funds
        copper = caller.db.copper or 0
        if copper < RENT_COST:
            caller.msg(
                f"|cBess|n shakes her head. 'A night's rest costs {format_money(RENT_COST)}, "
                f"love. You've only got {format_money(copper)}.'"
            )
            return

        # Well-rested check (80%+ HP)
        current_hp = caller.get_hp()
        max_hp = caller.get_hp_max()
        if max_hp > 0 and current_hp / max_hp >= HP_WELL_RESTED:
            caller.ndb._rent_confirm = True
            caller.msg(
                f"|cBess|n looks you over. 'You look fairly well rested, "
                f"love. Are you sure? It's {format_money(RENT_COST)}.'\n"
                f"  (type |wrent|n again to confirm)"
            )
            return

        self._do_rent(caller)

    def _do_rent(self, caller):
        """Take payment and start the rest."""
        caller.spend_money(RENT_COST)

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
                f"You pay {format_money(RENT_COST)} and receive a brass key. "
                f"'Room three, top of the stairs.'"
            )

        # Start rest
        caller.db.is_resting = True
        caller.cmdset.add("commands.command_rent.RestCmdSet")
        caller.scripts.add(RentScript)
