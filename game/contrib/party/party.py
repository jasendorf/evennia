"""
Party System Contrib
====================

A generic, game-agnostic system for player parties (groups). Provides
the engine; your game provides the behavior via callback hooks.

This contrib is intentionally bare of game-specific content. It has no
references to stats, combat, autoassist, or any particular game's
mechanics. See the DorfinMUD extension (contrib_dorfin/dorfin_party.py)
for an example of how to hook into it.

Overview
--------

The system has four components:

  Party          — An Evennia Script that stores the member list, leader,
                   and pending invites. One Party per group of players.
                   Persists across server reloads.

  PartyHandler   — Attached to a character via @lazy_property. Provides
                   a clean API for party operations without touching the
                   Script directly.

  PartyCharacterMixin — Mixin for your Character typeclass. Wires up the
                   handler and provides callback hooks.

  Callbacks      — on_member_join, on_member_leave, on_party_disband.
                   Override these in your game's mixin to add behavior
                   like autoassist, shared XP, or group buffs.

Installation
------------

1. Have your Character typeclass inherit from PartyCharacterMixin:

    from contrib.party.party import PartyCharacterMixin

    class Character(PartyCharacterMixin, DefaultCharacter):
        pass

2. The mixin provides self.party_handler (a PartyHandler).
   Players interact via commands you write (see command_party.py).

Party Lifecycle
---------------

  create  — A player creates a party. They become the leader.
  invite  — The leader invites another player. An invite expires
            after INVITE_TIMEOUT seconds (default 60).
  accept  — An invited player accepts. They join the party.
            on_member_join callback fires.
  decline — An invited player declines. The invite is removed.
  leave   — A member leaves the party. on_member_leave fires.
            If the leader leaves, leadership transfers to the next
            member. If no members remain, the party is disbanded.
  disband — The leader dissolves the party. All members are removed.
            on_party_disband fires.
  kick    — The leader removes a member. on_member_leave fires.

Configuration
-------------

  INVITE_TIMEOUT  — Seconds before a pending invite expires (default 60).
  MAX_PARTY_SIZE  — Maximum members allowed (default 0 = unlimited).

Requirements
------------

  - evennia.scripts.scripts.DefaultScript
  - evennia.utils.lazy_property
  - evennia.utils.utils.delay  (for invite expiry)
  - evennia.utils.logger       (for error logging)

No other Evennia contribs are required.

Contributing
------------

This contrib is designed to be contributed back to the Evennia project as
evennia.contrib.game_systems.party. If you improve it, please consider
opening a PR at https://github.com/evennia/evennia.

Requirements for contribution:
  - No game-specific content (names, messages, stat references)
  - Full docstrings on all public methods
  - Tests in a companion party_tests.py file
"""

import time

from evennia import DefaultScript
from evennia.utils import lazy_property
from evennia.utils.utils import delay
from evennia.utils.logger import log_err


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INVITE_TIMEOUT = 60     # seconds before a pending invite expires
MAX_PARTY_SIZE = 0      # 0 = unlimited


# ---------------------------------------------------------------------------
# Party Script
# ---------------------------------------------------------------------------

class Party(DefaultScript):
    """
    A shared Script representing a player party.

    One Party script exists per active party. It is not attached to any
    particular object (obj=None) — it is a standalone persistent script.

    db Attributes:
        leader     (str)  : Dbref of the party leader.
        members    (list) : List of member dbrefs (includes the leader).
        invites    (dict) : {target_dbref: expire_timestamp} — pending invites.
        callbacks  (dict) : NOT stored in db. Runtime-only callback registry.
    """

    def at_script_creation(self):
        self.key = "Party"
        self.desc = "A player party."
        self.persistent = True
        self.interval = 0          # no repeating tick needed

        self.db.leader = None
        self.db.members = []
        self.db.invites = {}

    # ------------------------------------------------------------------
    # Member management
    # ------------------------------------------------------------------

    def add_member(self, character):
        """
        Add a character to this party.

        Args:
            character: The character to add.

        Returns:
            bool: True if added, False if already a member or party is full.
        """
        dbref = character.dbref
        members = self.db.members or []

        if dbref in members:
            return False

        if MAX_PARTY_SIZE > 0 and len(members) >= MAX_PARTY_SIZE:
            return False

        members.append(dbref)
        self.db.members = members

        # Store party reference on the character
        character.db.party_id = self.id

        # Clear any pending invite
        invites = self.db.invites or {}
        invites.pop(dbref, None)
        self.db.invites = invites

        return True

    def remove_member(self, character):
        """
        Remove a character from this party.

        If the removed character was the leader, leadership transfers
        to the next member. If no members remain, the party is disbanded.

        Args:
            character: The character to remove.

        Returns:
            bool: True if removed, False if not a member.
        """
        dbref = character.dbref
        members = self.db.members or []

        if dbref not in members:
            return False

        members.remove(dbref)
        self.db.members = members

        # Clear party reference on the character
        character.db.party_id = None

        # Handle leader departure
        if self.db.leader == dbref:
            if members:
                self.db.leader = members[0]
            else:
                # No members left — disband
                self._do_disband()
                return True

        # If no members remain after removal, disband
        if not members:
            self._do_disband()

        return True

    def set_leader(self, character):
        """
        Transfer leadership to another member.

        Args:
            character: The new leader (must be an existing member).

        Returns:
            bool: True if leadership transferred, False if not a member.
        """
        dbref = character.dbref
        if dbref not in (self.db.members or []):
            return False
        self.db.leader = dbref
        return True

    # ------------------------------------------------------------------
    # Invite management
    # ------------------------------------------------------------------

    def add_invite(self, target):
        """
        Create a pending invite for a target character.

        The invite expires after INVITE_TIMEOUT seconds.

        Args:
            target: The character being invited.

        Returns:
            bool: True if invite created, False if already a member
                  or already has a pending invite.
        """
        dbref = target.dbref

        if dbref in (self.db.members or []):
            return False

        invites = self.db.invites or {}
        if dbref in invites:
            return False

        invites[dbref] = time.time() + INVITE_TIMEOUT
        self.db.invites = invites

        # Schedule expiry cleanup
        delay(INVITE_TIMEOUT + 1, self._expire_invite, dbref)

        return True

    def has_invite(self, target):
        """
        Check if a target has a pending (non-expired) invite.

        Args:
            target: The character to check.

        Returns:
            bool: True if they have a valid pending invite.
        """
        invites = self.db.invites or {}
        expire_time = invites.get(target.dbref)
        if not expire_time:
            return False
        if time.time() > expire_time:
            # Expired — clean up
            invites.pop(target.dbref, None)
            self.db.invites = invites
            return False
        return True

    def cancel_invite(self, target):
        """
        Cancel a pending invite.

        Args:
            target: The character whose invite to cancel.
        """
        invites = self.db.invites or {}
        invites.pop(target.dbref, None)
        self.db.invites = invites

    def _expire_invite(self, dbref):
        """
        Called by delay() to clean up an expired invite.

        Args:
            dbref (str): The target's dbref.
        """
        invites = self.db.invites or {}
        if dbref in invites:
            if time.time() >= invites[dbref]:
                del invites[dbref]
                self.db.invites = invites

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def is_member(self, character):
        """Check if a character is in this party."""
        return character.dbref in (self.db.members or [])

    def is_leader(self, character):
        """Check if a character is the party leader."""
        return character.dbref == self.db.leader

    def get_leader(self):
        """
        Return the leader character object.

        Returns:
            Character or None.
        """
        return self._resolve(self.db.leader)

    def get_members(self):
        """
        Return a list of all member character objects.

        Returns:
            list: Resolved character objects (filters out None/missing).
        """
        return [
            obj for obj in
            (self._resolve(ref) for ref in (self.db.members or []))
            if obj is not None
        ]

    def get_nearby_members(self, location):
        """
        Return party members in the same room as the given location.

        Args:
            location: A room object.

        Returns:
            list: Member character objects in that room.
        """
        return [m for m in self.get_members() if m.location == location]

    def get_size(self):
        """Return the number of members."""
        return len(self.db.members or [])

    # ------------------------------------------------------------------
    # Disband
    # ------------------------------------------------------------------

    def disband(self):
        """
        Dissolve the party. Removes all members and deletes the script.

        Calls the on_party_disband callback on each member before removal.
        """
        self._do_disband()

    def _do_disband(self):
        """Internal disband — clears all members and deletes the script."""
        members = self.db.members or []

        # Notify all members via callback before clearing
        for dbref in list(members):
            obj = self._resolve(dbref)
            if obj:
                obj.db.party_id = None
                # Fire callback if available
                if hasattr(obj, "on_party_disband"):
                    try:
                        obj.on_party_disband(self)
                    except Exception as err:
                        log_err(f"Party._do_disband callback error: {err}")

        self.db.members = []
        self.db.invites = {}
        self.db.leader = None
        self.delete()

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _resolve(self, dbref):
        """Resolve a dbref to a live object, or None."""
        if not dbref:
            return None
        try:
            from evennia import search_object
            results = search_object(dbref)
            return results[0] if results else None
        except Exception:
            return None


# ---------------------------------------------------------------------------
# PartyHandler
# ---------------------------------------------------------------------------

class PartyHandler:
    """
    API for party operations, attached to a character via @lazy_property.

    Wraps the Party script to provide a clean interface. All methods
    handle the case where the character is not in a party.

    Usage:

        character.party_handler.create()
        character.party_handler.invite(other_character)
        character.party_handler.leave()
        character.party_handler.get_members()
    """

    def __init__(self, obj):
        """
        Args:
            obj: The character this handler is attached to.
        """
        self.obj = obj

    # ------------------------------------------------------------------
    # Party access
    # ------------------------------------------------------------------

    def get_party(self):
        """
        Return the Party script this character belongs to, or None.

        Returns:
            Party or None.
        """
        party_id = self.obj.db.party_id
        if not party_id:
            return None

        try:
            from evennia.scripts.models import ScriptDB
            script = ScriptDB.objects.get(id=party_id)
            # Verify it's still a valid party and we're in it
            if script.db.members and self.obj.dbref in script.db.members:
                return script
        except Exception:
            pass

        # Stale reference — clean up
        self.obj.db.party_id = None
        return None

    def in_party(self):
        """Return True if this character is in a party."""
        return self.get_party() is not None

    def is_leader(self):
        """Return True if this character is the party leader."""
        party = self.get_party()
        if not party:
            return False
        return party.is_leader(self.obj)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(self):
        """
        Create a new party with this character as leader.

        Returns:
            Party: The new party, or None if already in a party.
        """
        if self.in_party():
            return None

        from evennia import create_script
        party = create_script(
            Party,
            key="Party",
            persistent=True,
            autostart=True,
        )
        party.db.leader = self.obj.dbref
        party.add_member(self.obj)

        # Fire callback
        if hasattr(self.obj, "on_party_join"):
            try:
                self.obj.on_party_join(party)
            except Exception as err:
                log_err(f"PartyHandler.create callback error: {err}")

        return party

    # ------------------------------------------------------------------
    # Invite / Accept / Decline
    # ------------------------------------------------------------------

    def invite(self, target):
        """
        Invite another character to this party. Only the leader can invite.

        Args:
            target: The character to invite.

        Returns:
            tuple: (success: bool, message: str)
        """
        party = self.get_party()
        if not party:
            return False, "You are not in a party."

        if not party.is_leader(self.obj):
            return False, "Only the party leader can invite."

        if party.is_member(target):
            return False, "They are already in your party."

        # Check if target is in another party
        if hasattr(target, "db") and target.db.party_id:
            return False, "They are already in a party."

        if MAX_PARTY_SIZE > 0 and party.get_size() >= MAX_PARTY_SIZE:
            return False, "The party is full."

        if not party.add_invite(target):
            return False, "An invite is already pending for them."

        # Store the party id on the target so they can accept
        target.db.party_invite_id = party.id

        return True, "Invite sent."

    def accept(self):
        """
        Accept a pending party invite.

        Returns:
            tuple: (success: bool, message: str)
        """
        invite_id = self.obj.db.party_invite_id
        if not invite_id:
            return False, "You have no pending party invite."

        # Already in a party?
        if self.in_party():
            self.obj.db.party_invite_id = None
            return False, "You are already in a party."

        # Find the party
        try:
            from evennia.scripts.models import ScriptDB
            party = ScriptDB.objects.get(id=invite_id)
        except Exception:
            self.obj.db.party_invite_id = None
            return False, "That party no longer exists."

        # Check the invite is still valid
        if not party.has_invite(self.obj):
            self.obj.db.party_invite_id = None
            return False, "Your invite has expired."

        # Join
        if not party.add_member(self.obj):
            self.obj.db.party_invite_id = None
            return False, "Could not join the party."

        self.obj.db.party_invite_id = None

        # Fire callbacks
        if hasattr(self.obj, "on_party_join"):
            try:
                self.obj.on_party_join(party)
            except Exception as err:
                log_err(f"PartyHandler.accept callback error: {err}")

        # Notify other members
        for member in party.get_members():
            if member != self.obj and hasattr(member, "on_member_join"):
                try:
                    member.on_member_join(party, self.obj)
                except Exception as err:
                    log_err(f"PartyHandler.accept notify error: {err}")

        return True, "You joined the party."

    def decline(self):
        """
        Decline a pending party invite.

        Returns:
            tuple: (success: bool, message: str)
        """
        invite_id = self.obj.db.party_invite_id
        if not invite_id:
            return False, "You have no pending party invite."

        try:
            from evennia.scripts.models import ScriptDB
            party = ScriptDB.objects.get(id=invite_id)
            party.cancel_invite(self.obj)
        except Exception:
            pass

        self.obj.db.party_invite_id = None
        return True, "Invite declined."

    # ------------------------------------------------------------------
    # Leave / Disband / Kick
    # ------------------------------------------------------------------

    def leave(self):
        """
        Leave the current party.

        If the leader leaves, leadership auto-transfers. If the party
        becomes empty, it is disbanded.

        Returns:
            tuple: (success: bool, message: str)
        """
        party = self.get_party()
        if not party:
            return False, "You are not in a party."

        # Fire callback on self
        if hasattr(self.obj, "on_party_leave"):
            try:
                self.obj.on_party_leave(party)
            except Exception as err:
                log_err(f"PartyHandler.leave callback error: {err}")

        # Notify remaining members
        for member in party.get_members():
            if member != self.obj and hasattr(member, "on_member_leave"):
                try:
                    member.on_member_leave(party, self.obj)
                except Exception as err:
                    log_err(f"PartyHandler.leave notify error: {err}")

        was_leader = party.is_leader(self.obj)
        party.remove_member(self.obj)

        if was_leader and party.get_size() > 0:
            new_leader = party.get_leader()
            return True, f"You left the party. Leadership transferred."
        elif party.get_size() == 0:
            return True, "You left the party. The party has been disbanded."
        else:
            return True, "You left the party."

    def disband(self):
        """
        Disband the party. Only the leader can disband.

        Returns:
            tuple: (success: bool, message: str)
        """
        party = self.get_party()
        if not party:
            return False, "You are not in a party."

        if not party.is_leader(self.obj):
            return False, "Only the party leader can disband."

        party.disband()
        return True, "The party has been disbanded."

    def kick(self, target):
        """
        Remove a member from the party. Only the leader can kick.

        Args:
            target: The character to remove.

        Returns:
            tuple: (success: bool, message: str)
        """
        party = self.get_party()
        if not party:
            return False, "You are not in a party."

        if not party.is_leader(self.obj):
            return False, "Only the party leader can kick members."

        if target == self.obj:
            return False, "You can't kick yourself. Use 'party leave'."

        if not party.is_member(target):
            return False, "They are not in your party."

        # Fire callbacks
        if hasattr(target, "on_party_leave"):
            try:
                target.on_party_leave(party)
            except Exception as err:
                log_err(f"PartyHandler.kick callback error: {err}")

        for member in party.get_members():
            if member != target and hasattr(member, "on_member_leave"):
                try:
                    member.on_member_leave(party, target)
                except Exception as err:
                    log_err(f"PartyHandler.kick notify error: {err}")

        party.remove_member(target)
        return True, f"Removed from the party."

    # ------------------------------------------------------------------
    # Transfer leadership
    # ------------------------------------------------------------------

    def transfer(self, target):
        """
        Transfer party leadership to another member.

        Args:
            target: The new leader.

        Returns:
            tuple: (success: bool, message: str)
        """
        party = self.get_party()
        if not party:
            return False, "You are not in a party."

        if not party.is_leader(self.obj):
            return False, "Only the party leader can transfer leadership."

        if not party.is_member(target):
            return False, "They are not in your party."

        if target == self.obj:
            return False, "You are already the leader."

        party.set_leader(target)
        return True, "Leadership transferred."

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_members(self):
        """
        Return a list of all party member character objects.

        Returns:
            list: Character objects, or empty list if not in a party.
        """
        party = self.get_party()
        if not party:
            return []
        return party.get_members()

    def get_nearby_members(self):
        """
        Return party members in the same room as this character.

        Returns:
            list: Member character objects in the same room
                  (excludes self).
        """
        party = self.get_party()
        if not party:
            return []
        return [
            m for m in party.get_nearby_members(self.obj.location)
            if m != self.obj
        ]

    def get_leader(self):
        """
        Return the party leader character object.

        Returns:
            Character or None.
        """
        party = self.get_party()
        if not party:
            return None
        return party.get_leader()

    def get_size(self):
        """
        Return the number of party members.

        Returns:
            int: Member count, or 0 if not in a party.
        """
        party = self.get_party()
        if not party:
            return 0
        return party.get_size()


# ---------------------------------------------------------------------------
# PartyCharacterMixin
# ---------------------------------------------------------------------------

class PartyCharacterMixin:
    """
    Mixin for Character typeclasses. Wires up the PartyHandler.

    Usage:

        from contrib.party.party import PartyCharacterMixin

        class Character(PartyCharacterMixin, DefaultCharacter):
            pass

    The mixin provides:
        - self.party_handler  (@lazy_property PartyHandler)
        - Callback stubs: on_party_join, on_party_leave, on_party_disband,
          on_member_join, on_member_leave

    Override the callbacks in your game-specific mixin or typeclass to
    add behavior (autoassist, shared buffs, etc).
    """

    @lazy_property
    def party_handler(self):
        """The PartyHandler attached to this character."""
        return PartyHandler(self)

    # ------------------------------------------------------------------
    # Callback stubs — override in your game layer
    # ------------------------------------------------------------------

    def on_party_join(self, party):
        """
        Called when this character joins a party (including on create).

        Args:
            party (Party): The party joined.
        """
        pass

    def on_party_leave(self, party):
        """
        Called when this character leaves a party (including kick).

        Args:
            party (Party): The party being left.
        """
        pass

    def on_party_disband(self, party):
        """
        Called when the party this character is in is disbanded.

        Args:
            party (Party): The party being disbanded.
        """
        pass

    def on_member_join(self, party, new_member):
        """
        Called when another player joins this character's party.

        Args:
            party (Party): The party.
            new_member: The character who joined.
        """
        pass

    def on_member_leave(self, party, leaving_member):
        """
        Called when another player leaves this character's party.

        Args:
            party (Party): The party.
            leaving_member: The character who left.
        """
        pass
