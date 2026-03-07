"""
Gate commands — open and close AwtownGate exits.

Players can refer to a gate by:
  - direction:  open south / open north
  - gate name:  open iron gate / open city gate
  - generic:    open gate  (opens the first CLOSED gate found, not the first gate)
"""

from evennia.commands.command import Command
from typeclasses.exits import AwtownGate


def _find_gate(location, query):
    """
    Find a gate exit in the room matching query.

    Priority:
      1. Direction match (e.g. 'south', 's')
      2. Key/alias/gate_name match
      3. If query == 'gate'/'door', fall back to first CLOSED gate
         (so 'open gate' opens something useful rather than an already-open one)
    """
    query = query.lower().strip()
    gates = [obj for obj in location.exits if isinstance(obj, AwtownGate)]

    if not gates:
        return None

    # 1. Direction match — exact key or alias
    for g in gates:
        if g.key.lower() == query:
            return g
        if any(a.lower() == query for a in g.aliases.all()):
            return g

    # 2. gate_name or key contains query
    for g in gates:
        if query in (g.db.gate_name or "").lower():
            return g
        if query in g.key.lower():
            return g

    # 3. Generic "gate" / "door" — prefer a closed one so the command is useful
    if query in ("gate", "door"):
        closed = [g for g in gates if not g.db.is_open]
        if closed:
            return closed[0]
        return gates[0]

    return None


class CmdOpenGate(Command):
    """
    Open a gate or door.

    Usage:
        open <direction>
        open <gate name>
        open gate

    You can refer to a gate by the direction it leads (recommended when
    multiple gates are in the room), by its name, or generically as 'gate'.
    When using 'open gate' generically, the command prefers a closed gate.

    Examples:
        open south
        open east
        open gate
        open city gate
    """

    key = "open"
    aliases = []
    help_category = "Travel"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        query = self.args.strip().lower()

        if not query:
            caller.msg("Open what? Specify a direction or gate name (e.g. 'open south').")
            return

        gate = _find_gate(caller.location, query)

        if not gate:
            caller.msg(f"You don't see a gate or door called '{self.args.strip()}' here.")
            return

        if gate.db.is_open:
            caller.msg(
                f"The {gate.db.gate_name} to the {gate.key} is already open. "
                f"If you meant a different gate, specify its direction (e.g. 'open south')."
            )
            return

        gate.open_gate(opener=caller)
        caller.msg(f"You push open the {gate.db.gate_name} ({gate.key}).")


class CmdCloseGate(Command):
    """
    Close a gate or door.

    Usage:
        close <direction>
        close <gate name>
        close gate

    Examples:
        close south
        close gate
        close city gate
    """

    key = "close"
    aliases = []
    help_category = "Travel"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        query = self.args.strip().lower()

        if not query:
            caller.msg("Close what? Specify a direction or gate name (e.g. 'close south').")
            return

        gate = _find_gate(caller.location, query)

        if not gate:
            caller.msg(f"You don't see a gate or door called '{self.args.strip()}' here.")
            return

        if not gate.db.is_open:
            caller.msg(f"The {gate.db.gate_name} to the {gate.key} is already closed.")
            return

        gate.close_gate(closer=caller)
        caller.msg(f"You pull the {gate.db.gate_name} ({gate.key}) shut.")
