"""
Say and Ask commands with NPC dialogue targeting.

Default say:  first matching NPC in the room responds.
Directed say: say to <npc> <message>  — targets a specific NPC.
Ask:          ask <npc> about <topic> — MUD-traditional NPC query.
"""

from evennia.commands.default.general import CmdSay
from evennia.commands.command import Command
from typeclasses.npcs import AwtownNPC


def _npcs_in_room(location):
    return [obj for obj in location.contents if isinstance(obj, AwtownNPC)]


def _find_npc(location, name_query):
    """Find an NPC in the room by partial name match."""
    name_query = name_query.lower().strip()
    for obj in location.contents:
        if isinstance(obj, AwtownNPC) and name_query in obj.name.lower():
            return obj
    return None


class CmdDorfinSay(CmdSay):
    """
    Speak aloud in the current room.

    Usage:
        say <message>
        ' <message>
        say to <npc name> <message>

    Your words are heard by everyone in the room. NPCs may respond if
    they recognise what you've said. Only the first matching NPC responds
    unless you direct your speech at a specific NPC with 'say to'.

    To speak directly to a specific NPC:
        say to Vonn what's the danger here?
        say to Bess I need a room

    To ask an NPC about a topic, see the 'ask' command.

    Examples:
        say hello
        say to Bramwick what jobs are available?
    """

    key = "say"
    aliases = ["'"]

    def func(self):
        if not self.args:
            self.caller.msg("Say what?")
            return

        raw = self.args.strip()
        targeted_npc = None

        # Check for "say to <npc> <message>"
        if raw.lower().startswith("to "):
            remainder = raw[3:].strip()
            # Find the longest NPC name match from the start of remainder
            npcs = _npcs_in_room(self.caller.location)
            for npc in npcs:
                npc_name_lower = npc.name.lower()
                if remainder.lower().startswith(npc_name_lower):
                    targeted_npc = npc
                    raw = remainder[len(npc_name_lower):].strip()
                    break
            # Fallback: try first word(s) as NPC name
            if not targeted_npc:
                parts = remainder.split(" ", 1)
                candidate = _find_npc(self.caller.location, parts[0])
                if candidate:
                    targeted_npc = candidate
                    raw = parts[1].strip() if len(parts) > 1 else ""

        # Temporarily set args to the (possibly trimmed) message for super().func()
        original_args = self.args
        self.args = " " + raw if raw else original_args
        super().func()
        self.args = original_args

        if not raw:
            return

        npcs = _npcs_in_room(self.caller.location)
        if not npcs:
            return

        if targeted_npc:
            # Directed — only the target responds
            targeted_npc.hear_say(self.caller, raw)
        else:
            # Undirected — first matching NPC responds
            for npc in npcs:
                if npc.hear_say(self.caller, raw):
                    break


class CmdAsk(Command):
    """
    Ask an NPC about a specific topic.

    Usage:
        ask <npc> about <topic>
        ask <npc> <topic>

    This is the primary way to get information from NPCs in Awtown.
    The NPC must be in your current room.

    Examples:
        ask Bramwick about quests
        ask Vonn about the gate
        ask Marta about kit
        ask Bess about rooms
    """

    key = "ask"
    help_category = "Communication"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Ask whom about what?")
            return

        # Parse "ask <npc> about <topic>" or "ask <npc> <topic>"
        if " about " in args.lower():
            idx = args.lower().index(" about ")
            npc_part = args[:idx].strip()
            topic = args[idx + 7:].strip()
        else:
            parts = args.split(" ", 1)
            npc_part = parts[0].strip()
            topic = parts[1].strip() if len(parts) > 1 else ""

        if not topic:
            caller.msg("Ask them about what topic?")
            return

        npc = _find_npc(caller.location, npc_part)
        if not npc:
            caller.msg(f"You don't see anyone called '{npc_part}' here.")
            return

        if not npc.hear_say(caller, topic):
            caller.msg(
                f"|c{npc.name}|n doesn't seem to know anything about that."
            )
