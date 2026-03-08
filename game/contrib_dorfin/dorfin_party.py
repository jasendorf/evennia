"""
DorfinMUD Party Extension
==========================

Extends the generic party system (contrib/party/party.py) with
DorfinMUD-specific behavior:

  - Autoassist: when a party member enters combat, nearby party
    members with autoassist enabled automatically join the fight
    targeting the same mob.

  - Combat-aware callbacks: notifications when members join/leave
    use DorfinMUD's ANSI color conventions.

Installation
------------

Have your Character typeclass inherit from DorfinPartyMixin BEFORE
the generic PartyCharacterMixin (or instead of it — DorfinPartyMixin
already inherits from PartyCharacterMixin):

    from contrib_dorfin.dorfin_party import DorfinPartyMixin

    class AwtownCharacter(DorfinPartyMixin, DorfinNeedsMixin, ClothedCharacter):
        ...

Autoassist
----------

Players toggle autoassist with the 'autoassist' command. When enabled
(db.autoassist = True), the player will automatically join combat when
a party member in the same room attacks something.

The trigger point is in command_combat.py's CmdKill — after starting
combat, it calls trigger_party_autoassist() which checks for nearby
party members with autoassist on.
"""

from contrib.party.party import PartyCharacterMixin
from evennia.utils import lazy_property


class DorfinPartyMixin(PartyCharacterMixin):
    """
    DorfinMUD extension of PartyCharacterMixin.

    Adds autoassist toggle and combat-aware party callbacks.
    Inherits party_handler from PartyCharacterMixin.

    db Attributes:
        db.autoassist (bool) : Whether to auto-join party combat. Default False.
    """

    def at_object_creation(self):
        """Initialize autoassist flag."""
        super().at_object_creation()
        if self.db.autoassist is None:
            self.db.autoassist = False

    # ------------------------------------------------------------------
    # Callback overrides
    # ------------------------------------------------------------------

    def on_party_join(self, party):
        """Called when this character joins a party."""
        leader = party.get_leader()
        if leader and leader != self:
            self.msg(
                f"|gYou joined |w{leader.name}|g's party.|n"
            )

    def on_party_leave(self, party):
        """Called when this character leaves a party."""
        self.msg("|yYou left the party.|n")

    def on_party_disband(self, party):
        """Called when the party is disbanded."""
        self.msg("|yThe party has been disbanded.|n")

    def on_member_join(self, party, new_member):
        """Called when another player joins our party."""
        self.msg(
            f"|g{new_member.name} joined the party.|n"
        )

    def on_member_leave(self, party, leaving_member):
        """Called when another player leaves our party."""
        self.msg(
            f"|y{leaving_member.name} left the party.|n"
        )


# ---------------------------------------------------------------------------
# Autoassist trigger — called from CmdKill
# ---------------------------------------------------------------------------

def trigger_party_autoassist(attacker, target, handler):
    """
    Check if the attacker is in a party and trigger autoassist for
    nearby party members who have it enabled.

    Called by CmdKill after combat starts.

    Args:
        attacker: The character who initiated combat.
        target: The mob being attacked.
        handler: The CombatHandler for the room.
    """
    if not hasattr(attacker, "party_handler"):
        return

    party = attacker.party_handler.get_party()
    if not party:
        return

    # Get party members in the same room (excluding the attacker)
    nearby = [
        m for m in party.get_nearby_members(attacker.location)
        if m != attacker
    ]

    for member in nearby:
        # Check autoassist flag
        if not getattr(member.db, "autoassist", False):
            continue

        # Don't auto-join if already in combat
        if getattr(member.db, "in_combat", False):
            continue

        # Don't auto-join if the member is dead
        if hasattr(member, "is_alive") and not member.is_alive():
            continue

        # Join the fight
        handler.add_combatant(member, target)

        # Also add the target attacking the new member if it's a mob
        if not handler.get_target(target):
            handler.set_target(target, member)

        # Notify
        member.msg(
            f"|g[Autoassist] You leap to aid |w{attacker.name}|g, "
            f"attacking {target.get_display_name(member) if hasattr(target, 'get_display_name') else target.key}!|n"
        )
        attacker.location.msg_contents(
            f"|w{member.name}|n leaps to assist |w{attacker.name}|n!",
            exclude=[member],
        )
