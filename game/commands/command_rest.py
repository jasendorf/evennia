"""
Rest command
============

    rest    -- sit down and catch your breath for 10 seconds

Resting is a brief, interruptable recovery action available anywhere.
It is SEPARATE from renting a room at an inn.

    Resting  : db.is_resting = True, interruptable, 10s, 5% of max HP,
               free, usable anywhere outside of active combat,
               NOT safe from mob aggro.
    Renting  : db.is_renting = True, uninterruptable, 30s, full HP/hunger/
               thirst recovery, costs copper, requires a renter NPC,
               safe from mob aggro.

When resting, any command triggers a warning. A second command cancels
the rest with no healing. The rest completes automatically after 10 seconds
if left undisturbed.

Recovery amount: max(1, caller.get_hp_max() // 20)  (5% of max HP, floor 1)

Future: add similar 5%-of-max recovery for mana and movement points here
when those stats are implemented.

Depends on:
    typeclasses.characters.AwtownCharacter -- heal(), get_hp(), get_hp_max()
"""

from evennia.commands.command import Command
from evennia.commands.cmdset import CmdSet
from evennia import DefaultScript


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REST_INTERVAL  = 10    # seconds until recovery triggers
REST_PCT       = 20    # divisor for recovery: hp_max // REST_PCT  (5%)


# ---------------------------------------------------------------------------
# RestScript
# ---------------------------------------------------------------------------

class RestScript(DefaultScript):
    """
    Fires once after REST_INTERVAL seconds. If still attached (not stopped
    early), heals the character for 5% of their max HP.

    db Attributes:
        warned (bool): True after the first interrupt warning has been shown.
    """

    def at_script_creation(self):
        self.key = "RestScript"
        self.desc = "Resting to recover."
        self.interval = REST_INTERVAL
        self.repeats = 1
        self.start_delay = True
        self.persistent = False
        self.db.warned = False

    def at_repeat(self):
        obj = self.obj
        if not obj:
            return

        hp_max  = obj.get_hp_max() if hasattr(obj, "get_hp_max") else 100
        recover = max(1, hp_max // REST_PCT)

        if hasattr(obj, "heal"):
            obj.heal(recover)

        hp_now = obj.get_hp()    if hasattr(obj, "get_hp")     else "?"
        hp_max_now = obj.get_hp_max() if hasattr(obj, "get_hp_max") else "?"
        obj.msg(
            f"|gYou feel refreshed. (+{recover} HP)|n  "
            f"|w({hp_now}/{hp_max_now} HP)|n"
        )
        # at_stop fires automatically after the final repeat

    def at_stop(self):
        obj = self.obj
        if obj:
            obj.db.is_resting = False
            try:
                obj.cmdset.remove("RestCmdSet")
            except Exception:
                pass


# ---------------------------------------------------------------------------
# RestCmdSet  -- applied to the character while resting
# ---------------------------------------------------------------------------

class CmdRestIntercept(Command):
    """
    Intercepts commands while the character is resting.

    First interrupt: warns the player and sets a flag.
    Second interrupt: cancels the rest (no healing) and executes the command.
    """

    key = "_default"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        scripts = caller.scripts.get("RestScript")

        if not scripts:
            # Script already gone -- force-cleanup and pass the command through
            caller.db.is_resting = False
            try:
                caller.cmdset.remove("RestCmdSet")
            except Exception:
                pass
            caller.execute_cmd(self.raw_string)
            return

        script = scripts[0]

        if script.db.warned:
            # Second attempt -- cancel the rest, no healing
            script.stop()
            # Belt-and-suspenders: ensure cmdset is removed even if at_stop failed
            caller.db.is_resting = False
            try:
                caller.cmdset.remove("RestCmdSet")
            except Exception:
                pass
            caller.msg("|yYou get up before you've finished resting. No HP recovered.|n")
            caller.execute_cmd(self.raw_string)
        else:
            # First attempt -- warn
            script.db.warned = True
            caller.msg(
                "|yIf you stop resting now you won't recover any HP.|n\n"
                "  (repeat the command to get up anyway)"
            )


class RestCmdSet(CmdSet):
    key = "RestCmdSet"
    priority = 200
    mergetype = "Replace"
    no_exits = True
    no_objs = True

    def at_cmdset_creation(self):
        self.add(CmdRestIntercept())


# ---------------------------------------------------------------------------
# CmdRest
# ---------------------------------------------------------------------------

class CmdRest(Command):
    """
    Sit down and catch your breath.

    Usage:
        rest

    Resting for 10 undisturbed seconds restores 5% of your maximum HP.
    You can rest anywhere -- after a long journey, after training a spell,
    or any time you need a quick breather.

    You cannot rest while actively in combat. Wandering or patrolling
    mobs can interrupt your rest by engaging you.

    If you issue any command during the rest, you will be warned. Issue
    it a second time to cancel the rest (no HP recovered).
    """

    key = "rest"
    aliases = ["recover"]
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller

        # --- Cannot rest in active combat ---
        if getattr(caller.db, "in_combat", False):
            caller.msg("You can't rest while in combat!")
            return

        # Double-check via CombatHandler in case the flag is stale
        try:
            from contrib_dorfin.combat_handler import CombatHandler
            handler = CombatHandler.get_handler(caller.location)
            if handler and handler.is_in_combat(caller):
                caller.msg("You can't rest while in combat!")
                return
        except ImportError:
            pass

        # --- Already resting? ---
        has_flag = getattr(caller.db, "is_resting", False)
        rest_scripts = caller.scripts.get("RestScript")
        has_script = bool(rest_scripts)
        if has_flag and has_script:
            # Genuinely resting -- both flag and script present
            caller.msg("You're already resting.")
            return
        if has_flag or has_script:
            # Orphaned state -- flag without script or script without flag.
            # Use delete() not stop() to avoid triggering at_repeat/at_stop.
            caller.db.is_resting = False
            if rest_scripts:
                for s in rest_scripts:
                    s.delete()
            try:
                caller.cmdset.remove("RestCmdSet")
            except Exception:
                pass

        # --- Cannot rest while renting ---
        if getattr(caller.db, "is_renting", False):
            caller.msg("You're already asleep in your room.")
            return

        # --- Already at full HP? ---
        if hasattr(caller, "get_hp") and hasattr(caller, "get_hp_max"):
            if caller.get_hp() >= caller.get_hp_max():
                caller.msg("You are already at full health.")
                return

        # --- Begin resting ---
        caller.db.is_resting = True
        caller.cmdset.add("commands.command_rest.RestCmdSet", persistent=False)
        caller.scripts.add(RestScript)

        caller.msg("|xYou sit down to rest...|n")
        caller.location.msg_contents(
            f"|w{caller.name}|n sits down to rest.",
            exclude=[caller],
        )
