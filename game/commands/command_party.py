"""
Party commands
==============

    party create              -- create a new party
    party invite <player>     -- invite a player to your party
    party accept              -- accept a pending invite
    party decline             -- decline a pending invite
    party leave               -- leave your party
    party disband             -- disband the party (leader only)
    party kick <player>       -- kick a member (leader only)
    party transfer <player>   -- transfer leadership (leader only)
    party list                -- show party members
    party / party status      -- alias for party list

    autoassist                -- toggle autoassist on/off

Depends on:
    contrib.party.party          -- generic party system
    contrib_dorfin.dorfin_party  -- DorfinMUD party layer
"""

from evennia.commands.command import Command


class CmdParty(Command):
    """
    Manage your party.

    Usage:
        party create              -- create a new party (you become leader)
        party invite <player>     -- invite a player
        party accept              -- accept a pending invite
        party decline             -- decline a pending invite
        party leave               -- leave the party
        party disband             -- disband (leader only)
        party kick <player>       -- kick a member (leader only)
        party transfer <player>   -- transfer leadership (leader only)
        party list                -- show party members
        party                     -- show party members (shortcut)

    Party members in the same room with autoassist enabled will
    automatically join combat when you attack a mob.

    Examples:
        party create
        party invite Gandalf
        party kick Pippin
        party list
    """

    key = "party"
    aliases = ["group"]
    help_category = "Party"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args or args.lower() in ("list", "status", "info"):
            self._do_list()
            return

        parts = args.split(None, 1)
        subcmd = parts[0].lower()
        subargs = parts[1].strip() if len(parts) > 1 else ""

        dispatch = {
            "create": self._do_create,
            "invite": self._do_invite,
            "accept": self._do_accept,
            "decline": self._do_decline,
            "leave": self._do_leave,
            "disband": self._do_disband,
            "kick": self._do_kick,
            "transfer": self._do_transfer,
        }

        func = dispatch.get(subcmd)
        if func:
            func(subargs)
        else:
            caller.msg(
                f"Unknown party command: '{subcmd}'. "
                f"Try |wparty list|n or |whelp party|n."
            )

    # ------------------------------------------------------------------
    # Subcommands
    # ------------------------------------------------------------------

    def _do_create(self, args):
        caller = self.caller

        if caller.party_handler.in_party():
            caller.msg("You are already in a party. Leave first with |wparty leave|n.")
            return

        party = caller.party_handler.create()
        if party:
            caller.msg(
                "|gYou created a party. You are the leader.|n\n"
                "Invite others with |wparty invite <player>|n."
            )
        else:
            caller.msg("Could not create a party.")

    def _do_invite(self, args):
        caller = self.caller

        if not args:
            caller.msg("Invite whom? Usage: |wparty invite <player>|n")
            return

        target = caller.search(args, global_search=True, quiet=True)
        if not target:
            caller.msg(f"Player '{args}' not found.")
            return
        if isinstance(target, list):
            # Prefer players over other objects
            players = [t for t in target if hasattr(t, "party_handler")]
            target = players[0] if players else target[0]

        if target == caller:
            caller.msg("You can't invite yourself.")
            return

        if not hasattr(target, "party_handler"):
            caller.msg(f"{target.name} can't join a party.")
            return

        success, msg = caller.party_handler.invite(target)
        if success:
            caller.msg(f"|gYou invited |w{target.name}|g to the party.|n")
            target.msg(
                f"|w{caller.name}|n invited you to join their party.\n"
                f"Type |wparty accept|n or |wparty decline|n."
            )
        else:
            caller.msg(msg)

    def _do_accept(self, args):
        caller = self.caller
        success, msg = caller.party_handler.accept()
        caller.msg(f"|g{msg}|n" if success else msg)

    def _do_decline(self, args):
        caller = self.caller
        success, msg = caller.party_handler.decline()
        caller.msg(f"|y{msg}|n" if success else msg)

        # Notify the party leader
        if success:
            invite_id = caller.db.party_invite_id
            if invite_id:
                try:
                    from evennia.scripts.models import ScriptDB
                    party = ScriptDB.objects.get(id=invite_id)
                    leader = party.get_leader()
                    if leader:
                        leader.msg(f"|y{caller.name} declined the party invite.|n")
                except Exception:
                    pass

    def _do_leave(self, args):
        caller = self.caller
        success, msg = caller.party_handler.leave()
        caller.msg(f"|y{msg}|n" if success else msg)

    def _do_disband(self, args):
        caller = self.caller
        success, msg = caller.party_handler.disband()
        caller.msg(f"|r{msg}|n" if success else msg)

    def _do_kick(self, args):
        caller = self.caller

        if not args:
            caller.msg("Kick whom? Usage: |wparty kick <player>|n")
            return

        target = caller.search(args, global_search=True, quiet=True)
        if not target:
            caller.msg(f"Player '{args}' not found.")
            return
        if isinstance(target, list):
            target = target[0]

        success, msg = caller.party_handler.kick(target)
        if success:
            caller.msg(f"|yYou kicked |w{target.name}|y from the party.|n")
            target.msg(f"|rYou have been kicked from the party.|n")
        else:
            caller.msg(msg)

    def _do_transfer(self, args):
        caller = self.caller

        if not args:
            caller.msg("Transfer to whom? Usage: |wparty transfer <player>|n")
            return

        target = caller.search(args, global_search=True, quiet=True)
        if not target:
            caller.msg(f"Player '{args}' not found.")
            return
        if isinstance(target, list):
            target = target[0]

        success, msg = caller.party_handler.transfer(target)
        if success:
            caller.msg(f"|gYou transferred leadership to |w{target.name}|g.|n")
            target.msg(f"|gYou are now the party leader.|n")

            # Notify other members
            party = caller.party_handler.get_party()
            if party:
                for member in party.get_members():
                    if member != caller and member != target:
                        member.msg(
                            f"|w{target.name}|n is now the party leader."
                        )
        else:
            caller.msg(msg)

    def _do_list(self):
        caller = self.caller

        if not caller.party_handler.in_party():
            caller.msg(
                "You are not in a party.\n"
                "Create one with |wparty create|n."
            )
            return

        party = caller.party_handler.get_party()
        if not party:
            caller.msg("You are not in a party.")
            return

        members = party.get_members()
        leader_dbref = party.db.leader

        lines = ["|w=== Party ===|n"]
        for member in members:
            # Location info
            same_room = member.location == caller.location
            loc_str = "|g(here)|n" if same_room else f"|x({member.location.name if member.location else '???'})|n"

            # Leader marker
            leader_str = " |y[Leader]|n" if member.dbref == leader_dbref else ""

            # HP if available
            hp_str = ""
            if hasattr(member, "get_hp"):
                hp = member.get_hp()
                hp_max = member.get_hp_max()
                hp_color = "|g" if hp > hp_max * 0.5 else ("|y" if hp > hp_max * 0.25 else "|r")
                hp_str = f" {hp_color}HP:{hp}/{hp_max}|n"

            # Autoassist
            aa_str = ""
            if getattr(member.db, "autoassist", False):
                aa_str = " |c[AA]|n"

            lines.append(
                f"  |w{member.name}|n{leader_str}{hp_str}{aa_str} {loc_str}"
            )

        lines.append(f"\n  Members: {len(members)}")
        autoassist_status = "ON" if getattr(caller.db, "autoassist", False) else "OFF"
        lines.append(f"  Your autoassist: |w{autoassist_status}|n")
        caller.msg("\n".join(lines))


# ---------------------------------------------------------------------------
# autoassist toggle
# ---------------------------------------------------------------------------

class CmdAutoAssist(Command):
    """
    Toggle automatic combat assistance for party members.

    Usage:
        autoassist
        autoassist on
        autoassist off

    When autoassist is ON and a party member in your room attacks
    a mob, you will automatically join the fight targeting the same mob.

    Without arguments, toggles your current setting.
    """

    key = "autoassist"
    aliases = ["aa"]
    help_category = "Party"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip().lower()

        current = getattr(caller.db, "autoassist", False)

        if args == "on":
            caller.db.autoassist = True
        elif args == "off":
            caller.db.autoassist = False
        else:
            caller.db.autoassist = not current

        new_state = caller.db.autoassist
        state_str = "|gON|n" if new_state else "|yOFF|n"
        caller.msg(f"Autoassist: {state_str}")

        if new_state and not caller.party_handler.in_party():
            caller.msg(
                "|x(You're not in a party — autoassist has no effect until you join one.)|n"
            )
