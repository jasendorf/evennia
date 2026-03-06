"""
Gate commands — open and close AwtownGate exits.

These commands find AwtownGate exit objects in the caller's current room
and delegate to their open_gate / close_gate methods.

Added to CharacterCmdSet in default_cmdsets.py.
"""

from evennia.commands.command import Command
from typeclasses.exits import AwtownGate


class CmdOpenGate(Command):
    """
    Open a gate or door.

    Usage:
        open <gate name>
        open gate
        open door
        open north

    Opens a closed gate exit in your current location. Gate exits are the
    heavy iron-banded doors and courtyard gates shown on orange connectors
    on the town map. City gates are managed by guards and open automatically
    during the day.

    Examples:
        open gate
        open city gate
        open iron gate
    """

    key = "open"
    aliases = []
    help_category = "Travel"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        query = self.args.strip().lower()

        if not query:
            caller.msg("Open what?")
            return

        gates = [
            obj for obj in caller.location.exits
            if isinstance(obj, AwtownGate) and (
                query in obj.key.lower()
                or query in (obj.db.gate_name or "").lower()
                or any(query in a.lower() for a in obj.aliases.all())
            )
        ]

        if not gates:
            caller.msg(f"You don't see a gate or door called '{self.args.strip()}' here.")
            return

        gate = gates[0]
        if gate.db.is_open:
            caller.msg(f"The {gate.db.gate_name} is already open.")
            return

        gate.open_gate(opener=caller)
        caller.msg(f"You push open the {gate.db.gate_name}.")


class CmdCloseGate(Command):
    """
    Close a gate or door.

    Usage:
        close <gate name>
        close gate
        close door

    Closes an open gate exit in your current location. Note that most gates
    close automatically after a short time.

    Examples:
        close gate
        close iron gate
    """

    key = "close"
    aliases = []
    help_category = "Travel"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        query = self.args.strip().lower()

        if not query:
            caller.msg("Close what?")
            return

        gates = [
            obj for obj in caller.location.exits
            if isinstance(obj, AwtownGate) and (
                query in obj.key.lower()
                or query in (obj.db.gate_name or "").lower()
                or any(query in a.lower() for a in obj.aliases.all())
            )
        ]

        if not gates:
            caller.msg(f"You don't see a gate or door called '{self.args.strip()}' here.")
            return

        gate = gates[0]
        if not gate.db.is_open:
            caller.msg(f"The {gate.db.gate_name} is already closed.")
            return

        gate.close_gate(closer=caller)
        caller.msg(f"You pull the {gate.db.gate_name} shut.")
