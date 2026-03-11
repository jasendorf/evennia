"""
Admin command to re-run character creation on an existing character.
"""

from evennia.commands.command import Command
from evennia.utils.evmenu import EvMenu

from world.chargen import BASE_STAT, STAT_KEYS


class CmdChargen(Command):
    """
    Re-run character creation on a character (admin only).

    Usage:
        @chargen [<character>]

    Without arguments, runs on your current character.
    Resets race, class, stats, and languages, then launches
    the chargen flow starting at the race selection step.
    The character's name is preserved.
    """

    key = "@chargen"
    locks = "cmd:perm(Admin) or perm(Builder)"
    help_category = "Admin"

    def func(self):
        if self.args:
            target = self.caller.search(self.args.strip())
            if not target:
                return
        else:
            target = self.caller

        # Reset chargen-related attributes
        target.db.race = None
        target.db.race_name = None
        target.db.char_class = None
        target.db.char_class_name = None
        target.db.languages = {"common": 1.0}
        target.db.wip_stats = None

        # Reset stats to base values
        if hasattr(target, "traits") and target.traits:
            for s in STAT_KEYS:
                trait = target.traits.get(s)
                if trait:
                    trait.base = BASE_STAT

        # Set chargen step so the contrib tracks it as in-progress
        target.db.chargen_step = "menunode_race_list"

        # Launch chargen EvMenu on the caller's session, skipping name step
        session = self.session
        session.new_char = target

        def finish_callback(session, menu):
            char = session.new_char
            if char.db.chargen_step:
                self.caller.msg("|yChargen exited early. Use |w@chargen|y to resume.|n")
            else:
                self.caller.msg(f"|g{char.key} has been updated.|n")

        EvMenu(
            session,
            "world.chargen",
            startnode="menunode_race_list",
            cmd_on_exit=finish_callback,
        )
