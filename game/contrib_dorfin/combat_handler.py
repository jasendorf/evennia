"""
DorfinMUD Combat Handler
=========================

Tick-based combat engine. One CombatHandler script per room. Ticks every
COMBAT_TICK_INTERVAL seconds (default 4). Each tick, every combatant
auto-attacks their current target.

Design
------

The handler is an Evennia Script attached to a room. It is created when
the first attack command fires in that room, and stops itself when combat
ends (all enemies dead, all players fled, or no valid target pairs).

Combatants and targets are stored as dbrefs (strings) for persistence
across server reloads. The handler resolves them to live objects each tick.

The handler distinguishes mobs from players using ``db.is_mob``.

Integration points
------------------

Combat rules:   contrib_dorfin.combat_rules   (resolve_attack, check_flee, etc.)
Mob death:      typeclasses.mobs.AwtownMob    (at_defeat -> corpse + loot)
Player death:   typeclasses.characters        (at_death -> teleport + XP loss)
Party system:   contrib_dorfin.dorfin_party   (autoassist hook, chunk 6)

Usage
-----

The combat commands (chunk 4) call these class methods:

    # Start or join combat
    handler = CombatHandler.get_or_create(room)
    handler.add_combatant(attacker, target)

    # Flee
    handler.remove_combatant(character)

    # Switch target
    handler.set_target(attacker, new_target)

    # Rescue aggro lock
    handler.set_aggro_lock(mob, rescuer, duration_ticks=2)
"""

from evennia import DefaultScript
from evennia.utils.logger import log_err


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COMBAT_TICK_INTERVAL = 4   # seconds between combat rounds
AGGRO_LOCK_TICKS = 2       # how many ticks a rescue aggro lock lasts


# ---------------------------------------------------------------------------
# CombatHandler
# ---------------------------------------------------------------------------

class CombatHandler(DefaultScript):
    """
    Per-room combat manager. Created when combat starts, deleted when
    combat ends.

    Persistent db Attributes:
        combatants (list)    : List of combatant dbrefs (str).
        targets (dict)       : {attacker_dbref: target_dbref} — who is
                               attacking whom.
        aggro_locks (dict)   : {mob_dbref: {"target": rescuer_dbref,
                               "expires": tick_number}} — rescue locks.
        tick_count (int)     : Running count of ticks since combat started.
    """

    # ------------------------------------------------------------------
    # Script lifecycle
    # ------------------------------------------------------------------

    def at_script_creation(self):
        self.key = "CombatHandler"
        self.desc = "Manages tick-based combat in a room."
        self.interval = COMBAT_TICK_INTERVAL
        self.persistent = True
        self.start_delay = True     # wait one interval before first tick

        self.db.combatants = []
        self.db.targets = {}
        self.db.aggro_locks = {}
        self.db.tick_count = 0

    def at_stop(self):
        """Called when the script stops. Clean up combat state on all combatants."""
        for dbref in list(self.db.combatants or []):
            obj = self._resolve(dbref)
            if obj:
                self._cleanup_combatant(obj)

    def at_repeat(self):
        """Called every COMBAT_TICK_INTERVAL seconds. Run one combat round."""
        self.db.tick_count = (self.db.tick_count or 0) + 1

        try:
            self._run_tick()
        except Exception as err:
            log_err(f"CombatHandler.at_repeat error: {err}")

    # ------------------------------------------------------------------
    # Public API — called by combat commands
    # ------------------------------------------------------------------

    @classmethod
    def get_or_create(cls, room):
        """
        Get the existing CombatHandler for a room, or create one.

        Args:
            room: The room object.

        Returns:
            CombatHandler: The handler script.
        """
        existing = room.scripts.get("CombatHandler")
        if existing:
            return existing[0]

        from evennia import create_script
        handler = create_script(
            cls,
            key="CombatHandler",
            obj=room,
            persistent=True,
            autostart=True,
        )
        return handler

    @classmethod
    def get_handler(cls, room):
        """
        Get the CombatHandler for a room if one exists.

        Args:
            room: The room object.

        Returns:
            CombatHandler or None.
        """
        existing = room.scripts.get("CombatHandler")
        return existing[0] if existing else None

    def add_combatant(self, combatant, target=None):
        """
        Add a combatant to the fight. If they're already in, just
        update their target.

        Renting characters are protected and cannot be added to combat.
        Resting characters have their rest cancelled before joining.

        Args:
            combatant: The object entering combat.
            target: Optional initial target.

        Returns:
            bool: True if the combatant was added, False if blocked.
        """
        # Renting players are in a paid safe state — refuse combat
        if hasattr(combatant, "db") and getattr(combatant.db, "is_renting", False):
            return False

        # Cancel rest if the combatant is resting
        if hasattr(combatant, "db") and getattr(combatant.db, "is_resting", False):
            rest_scripts = combatant.scripts.get("RestScript")
            if rest_scripts:
                rest_scripts[0].stop()
            combatant.msg("|rYour rest is interrupted!|n")

        dbref = combatant.dbref
        combatants = self.db.combatants or []

        if dbref not in combatants:
            combatants.append(dbref)
            self.db.combatants = combatants
            combatant.db.in_combat = True

        if target:
            self.set_target(combatant, target)

        return True

    def remove_combatant(self, combatant, quiet=False):
        """
        Remove a combatant from the fight.

        Also removes them as anyone's target, and cleans up aggro locks.

        Args:
            combatant: The object leaving combat.
            quiet (bool): If True, suppress departure messages.
        """
        dbref = combatant.dbref
        combatants = self.db.combatants or []

        if dbref in combatants:
            combatants.remove(dbref)
            self.db.combatants = combatants

        # Remove from targets dict (both as attacker and as target)
        targets = self.db.targets or {}
        targets.pop(dbref, None)
        # Anyone targeting this combatant loses their target
        for attacker_ref, target_ref in list(targets.items()):
            if target_ref == dbref:
                del targets[attacker_ref]
        self.db.targets = targets

        # Remove any aggro locks involving this combatant
        aggro_locks = self.db.aggro_locks or {}
        aggro_locks.pop(dbref, None)
        for mob_ref, lock_data in list(aggro_locks.items()):
            if lock_data.get("target") == dbref:
                del aggro_locks[mob_ref]
        self.db.aggro_locks = aggro_locks

        # Clean up the combatant
        self._cleanup_combatant(combatant)

        if not quiet:
            self._check_combat_end()

    def set_target(self, attacker, target):
        """
        Set or switch an attacker's target.

        Args:
            attacker: The combatant switching targets.
            target: The new target.
        """
        targets = self.db.targets or {}
        targets[attacker.dbref] = target.dbref
        self.db.targets = targets

    def set_aggro_lock(self, mob, rescuer, duration_ticks=None):
        """
        Lock a mob's target to a specific rescuer for a number of ticks.

        During the lock, the mob cannot switch targets (used by rescue).

        Args:
            mob: The mob being taunted.
            rescuer: The combatant who rescued.
            duration_ticks (int): Number of ticks the lock lasts.
                                  Defaults to AGGRO_LOCK_TICKS.
        """
        if duration_ticks is None:
            duration_ticks = AGGRO_LOCK_TICKS

        tick = self.db.tick_count or 0
        aggro_locks = self.db.aggro_locks or {}
        aggro_locks[mob.dbref] = {
            "target": rescuer.dbref,
            "expires": tick + duration_ticks,
        }
        self.db.aggro_locks = aggro_locks

        # Force the mob's target to the rescuer
        self.set_target(mob, rescuer)

    def get_target(self, combatant):
        """
        Return the current target object for a combatant, or None.

        Args:
            combatant: The combatant to query.

        Returns:
            Object or None.
        """
        targets = self.db.targets or {}
        target_ref = targets.get(combatant.dbref)
        if not target_ref:
            return None
        return self._resolve(target_ref)

    def get_combatants(self):
        """
        Return list of all live combatant objects currently in this fight.

        Returns:
            list: Resolved combatant objects (filters out None/missing).
        """
        return [
            obj for obj in
            (self._resolve(ref) for ref in (self.db.combatants or []))
            if obj is not None
        ]

    def get_opponents(self, combatant):
        """
        Return all combatants that are targeting the given combatant.

        Args:
            combatant: The combatant to find opponents of.

        Returns:
            list: Objects currently targeting this combatant.
        """
        dbref = combatant.dbref
        targets = self.db.targets or {}
        opponents = []
        for attacker_ref, target_ref in targets.items():
            if target_ref == dbref:
                obj = self._resolve(attacker_ref)
                if obj:
                    opponents.append(obj)
        return opponents

    def is_in_combat(self, combatant):
        """Check if a combatant is in this fight."""
        return combatant.dbref in (self.db.combatants or [])

    # ------------------------------------------------------------------
    # Autoassist hook — called by the party system (Chunk 6)
    # ------------------------------------------------------------------

    def trigger_autoassist(self, combatant, target):
        """
        Hook for the party system to auto-add party members to combat.

        Called when a party member enters combat. The party layer is
        responsible for finding eligible members and calling this for each.

        Args:
            combatant: The party member to auto-add.
            target: The target they should attack.
        """
        self.add_combatant(combatant, target)
        room = self.obj
        if room:
            room.msg_contents(
                f"|w{combatant.name}|n leaps to assist, attacking "
                f"{target.get_display_name(combatant) if hasattr(target, 'get_display_name') else target.key}!",
                exclude=[combatant],
            )
            combatant.msg(
                f"|gYou leap to assist, attacking "
                f"{target.get_display_name(combatant) if hasattr(target, 'get_display_name') else target.key}!|n"
            )

    # ------------------------------------------------------------------
    # Internal — tick resolution
    # ------------------------------------------------------------------

    def _run_tick(self):
        """Execute one full combat round."""
        room = self.obj
        if not room:
            self.delete()
            return

        # Expire old aggro locks
        self._expire_aggro_locks()

        # Prune combatants that left the room or no longer exist
        self._prune_missing()

        # Get ordered combatant list
        combatants = self._get_initiative_order()
        if len(combatants) < 2:
            self._end_combat()
            return

        # Track deaths this tick (process after all attacks)
        deaths = []

        # Each combatant attacks their target
        for combatant in combatants:
            # Skip if already dead this tick
            if combatant in deaths:
                continue

            # Skip if not alive
            if not self._is_alive(combatant):
                deaths.append(combatant)
                continue

            # Check wimpy auto-flee (players only)
            if self._check_wimpy(combatant):
                continue

            # Get target
            target = self.get_target(combatant)
            if not target or not self._is_alive(target) or target in deaths:
                # Try to find a new target
                target = self._find_new_target(combatant)
                if not target:
                    continue

            # Resolve attack
            self._resolve_combat_tick(combatant, target, deaths)

        # Process deaths
        for dead in deaths:
            self._handle_death(dead)

        # Check if combat should end
        self._check_combat_end()

    def _resolve_combat_tick(self, attacker, defender, deaths):
        """
        Resolve one auto-attack between attacker and defender.

        Args:
            attacker: The attacking combatant.
            defender: The defending combatant.
            deaths (list): Accumulator for combatants that die this tick.
        """
        from contrib_dorfin.combat_rules import resolve_attack

        result = resolve_attack(attacker, defender)
        room = self.obj

        atk_name = self._display_name(attacker)
        def_name = self._display_name(defender)

        if result["hit"]:
            damage = result["damage"]

            # Record HP before damage to detect kills
            hp_before = self._get_hp(defender)

            # Apply damage
            if hasattr(defender, "take_damage"):
                defender.take_damage(damage, source=attacker)
            else:
                # Fallback for objects without take_damage
                if hasattr(defender, "db"):
                    defender.db.hp = max(0, (defender.db.hp or 0) - damage)

            # Build the hit message
            if damage >= 15:
                hit_verb = "|r*** CRUSHES ***|n"
            elif damage >= 10:
                hit_verb = "|rhits hard|n"
            elif damage >= 5:
                hit_verb = "|yhits|n"
            else:
                hit_verb = "scratches"

            if room:
                room.msg_contents(
                    f"  {atk_name} {hit_verb} {def_name} "
                    f"for |w{damage}|n damage!"
                )

            # Post-damage status feedback
            is_defender_mob = (
                getattr(defender.db, "is_mob", False)
                if hasattr(defender, "db") else False
            )
            if is_defender_mob:
                # Mob: qualitative condition to the room
                condition = _mob_condition(defender)
                if condition and room:
                    room.msg_contents(f"  {def_name} {condition}.")
            else:
                # Player: private HP update
                hp_now = self._get_hp(defender)
                hp_max = defender.get_hp_max() if hasattr(defender, "get_hp_max") else 100
                hp_color = "|g" if hp_now > hp_max * 0.5 else ("|y" if hp_now > hp_max * 0.25 else "|r")
                if hasattr(defender, "msg"):
                    defender.msg(
                        f"  {hp_color}[HP: {hp_now}/{hp_max}]|n"
                    )

            # Check for kill (compare against pre-damage HP)
            if hp_before > 0 and hp_before <= damage:
                if defender not in deaths:
                    deaths.append(defender)

            # Also check via is_alive for mobs
            elif not self._is_alive(defender):
                if defender not in deaths:
                    deaths.append(defender)

        else:
            # Miss
            if room:
                room.msg_contents(
                    f"  {atk_name} swings at {def_name} "
                    f"but |xmisses|n."
                )

    # ------------------------------------------------------------------
    # Death handling
    # ------------------------------------------------------------------

    def _handle_death(self, dead):
        """
        Process the death of a combatant.

        For mobs: award XP, call at_defeat (spawns corpse + loot).
        For players: remove from combat (at_death already fired via take_damage).

        Args:
            dead: The defeated combatant.
        """
        is_mob = getattr(dead.db, "is_mob", False) if hasattr(dead, "db") else False
        room = self.obj

        if is_mob:
            # Award XP to all player combatants
            xp_value = getattr(dead.db, "xp_value", 0) or 0
            if xp_value > 0:
                self._award_xp(xp_value, dead)

            # Remove from combat first (so at_defeat delete doesn't cause issues)
            self.remove_combatant(dead, quiet=True)

            # Spawn corpse and loot
            if hasattr(dead, "at_defeat"):
                dead.at_defeat()

        else:
            # Player death — at_death() already called by take_damage()
            # Just remove from combat
            if room:
                room.msg_contents(
                    f"|r{dead.name} has been defeated!|n",
                    exclude=[dead],
                )
            self.remove_combatant(dead, quiet=True)

    def _award_xp(self, xp_value, dead_mob):
        """
        Split XP among all player combatants in this fight.

        Args:
            xp_value (int): Total XP to distribute.
            dead_mob: The mob that was killed (for messaging).
        """
        # Find all player combatants (not mobs)
        players = [
            c for c in self.get_combatants()
            if not (getattr(c.db, "is_mob", False) if hasattr(c, "db") else False)
        ]

        if not players:
            return

        xp_each = max(1, xp_value // len(players))

        # Check for XP bonus buff (Ondrel's Insight)
        for player in players:
            bonus = 0
            if hasattr(player, "buffs") and player.buffs:
                try:
                    bonus = int(player.buffs.check(0, "xp_bonus"))
                except Exception:
                    pass

            actual_xp = xp_each + (xp_each * bonus // 100) if bonus else xp_each
            player.db.xp = (player.db.xp or 0) + actual_xp
            player.msg(f"|g  You receive {actual_xp} experience points.|n")

    # ------------------------------------------------------------------
    # Wimpy auto-flee
    # ------------------------------------------------------------------

    def _check_wimpy(self, combatant):
        """
        Check if a combatant should auto-flee due to wimpy setting.

        Works for both players and mobs. Mobs default to wimpy=0 (fight
        to the death) but can have db.wimpy set to trigger auto-flee.

        Returns True if they fled (and were removed from combat).
        """
        wimpy = getattr(combatant.db, "wimpy", 0) or 0
        if wimpy <= 0:
            return False

        current_hp = self._get_hp(combatant)
        if current_hp > wimpy:
            return False

        # Attempt auto-flee
        from contrib_dorfin.combat_rules import check_flee
        opponents = self.get_opponents(combatant)
        result = check_flee(combatant, opponents)

        is_mob = getattr(combatant.db, "is_mob", False) if hasattr(combatant, "db") else False
        room = self.obj
        if result["success"]:
            if room:
                if is_mob:
                    room.msg_contents(
                        f"|y{combatant.name} whimpers and flees!|n"
                    )
                else:
                    room.msg_contents(
                        f"|y{combatant.name} panics and flees from combat!|n",
                        exclude=[combatant],
                    )
                    combatant.msg("|yYour wimpy threshold triggered! You flee from combat!|n")
            # Collect mob opponents before removing from combat (for chase)
            mob_opponents = [
                opp for opp in opponents
                if hasattr(opp, "db") and getattr(opp.db, "is_mob", False)
            ]
            self.remove_combatant(combatant)
            exit_used = self._move_to_random_exit(combatant)
            # Trigger chase for mob opponents (only when a player flees)
            if exit_used and not is_mob:
                try:
                    from contrib_dorfin.mob_movement import trigger_chase
                    for mob in mob_opponents:
                        trigger_chase(mob, combatant, exit_used)
                except ImportError:
                    pass
            return True
        else:
            if is_mob:
                if room:
                    room.msg_contents(
                        f"|y{combatant.name} tries to flee but can't escape!|n"
                    )
            else:
                combatant.msg(
                    "|rYour wimpy triggered but you failed to flee!|n"
                )
            return False

    def _move_to_random_exit(self, combatant):
        """
        Move a fleeing combatant through a random available exit.

        Returns:
            The exit object used, or None if flee failed.
        """
        room = self.obj
        if not room:
            return None

        # Prefer open exits (skip closed gates)
        exits = [
            ex for ex in room.exits
            if getattr(ex.db, "is_open", True) is not False
        ]

        if not exits:
            # All exits are closed gates — can't flee anywhere
            combatant.msg("|rAll exits are blocked! You can't escape!|n")
            return None

        from random import choice
        exit_obj = choice(exits)
        combatant.move_to(exit_obj.destination, quiet=False)
        return exit_obj

    # ------------------------------------------------------------------
    # Target management
    # ------------------------------------------------------------------

    def _find_new_target(self, combatant):
        """
        Find a valid target for a combatant whose current target is
        dead or gone.

        Mobs prefer players. Players prefer mobs.

        Args:
            combatant: The combatant needing a new target.

        Returns:
            Object or None.
        """
        is_mob = getattr(combatant.db, "is_mob", False) if hasattr(combatant, "db") else False
        all_combatants = self.get_combatants()

        candidates = [
            c for c in all_combatants
            if c != combatant
            and self._is_alive(c)
            and c.location == self.obj  # must be in the room
        ]

        if not candidates:
            return None

        if is_mob:
            # Mobs prefer players
            players = [c for c in candidates if not getattr(c.db, "is_mob", False)]
            target = players[0] if players else candidates[0]
        else:
            # Players prefer mobs
            mobs = [c for c in candidates if getattr(c.db, "is_mob", False)]
            target = mobs[0] if mobs else candidates[0]

        self.set_target(combatant, target)
        return target

    def _expire_aggro_locks(self):
        """Remove expired aggro locks."""
        tick = self.db.tick_count or 0
        aggro_locks = self.db.aggro_locks or {}
        expired = [
            mob_ref for mob_ref, data in aggro_locks.items()
            if data.get("expires", 0) <= tick
        ]
        for mob_ref in expired:
            del aggro_locks[mob_ref]
        self.db.aggro_locks = aggro_locks

    # ------------------------------------------------------------------
    # Initiative ordering
    # ------------------------------------------------------------------

    def _get_initiative_order(self):
        """
        Return combatants sorted by initiative (highest first).

        Initiative is rolled once per tick. Uses cached values for
        consistency within a single tick.
        """
        from contrib_dorfin.combat_rules import roll_initiative

        combatants = self.get_combatants()
        # Roll initiative for each
        inits = []
        for c in combatants:
            try:
                init = roll_initiative(c)
            except Exception:
                init = 10
            inits.append((init, c))

        # Sort descending by initiative
        inits.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in inits]

    # ------------------------------------------------------------------
    # Pruning and cleanup
    # ------------------------------------------------------------------

    def _prune_missing(self):
        """
        Remove combatants that no longer exist, left the room, or
        are disconnected.
        """
        room = self.obj
        combatants = list(self.db.combatants or [])
        to_remove = []

        for dbref in combatants:
            obj = self._resolve(dbref)
            if not obj:
                to_remove.append(dbref)
                continue
            if obj.location != room:
                to_remove.append(dbref)
                continue

        if to_remove:
            for dbref in to_remove:
                if dbref in combatants:
                    combatants.remove(dbref)
                targets = self.db.targets or {}
                targets.pop(dbref, None)
                for k, v in list(targets.items()):
                    if v == dbref:
                        del targets[k]
                self.db.targets = targets
            self.db.combatants = combatants

    def _check_combat_end(self):
        """
        Check if combat should end. Ends if:
        - Fewer than 2 combatants remain
        - Only one "side" remains (all mobs dead or all players gone)

        Has a 1-tick grace period to avoid ending combat before all
        combatants have been added.
        """
        # Grace period: don't auto-end on the very first tick
        if (self.db.tick_count or 0) < 1:
            return

        combatants = self.get_combatants()
        alive = [c for c in combatants if self._is_alive(c)]

        if len(alive) < 2:
            self._end_combat()
            return

        # Check if only one side remains
        has_mobs = any(
            getattr(c.db, "is_mob", False)
            for c in alive if hasattr(c, "db")
        )
        has_players = any(
            not getattr(c.db, "is_mob", False)
            for c in alive if hasattr(c, "db")
        )

        if not has_mobs or not has_players:
            self._end_combat()

    def _end_combat(self):
        """
        End combat. Clean up all combatants and delete the script.
        """
        room = self.obj
        if room:
            room.msg_contents("|xCombat has ended.|n")

        # Clean up all remaining combatants
        for dbref in list(self.db.combatants or []):
            obj = self._resolve(dbref)
            if obj:
                self._cleanup_combatant(obj)

        self.db.combatants = []
        self.db.targets = {}
        self.db.aggro_locks = {}

        # Delete rather than just stop — a stopped script still shows up
        # in scripts.get() and blocks things like mob respawn checks.
        self.delete()

    def _cleanup_combatant(self, combatant):
        """Remove all combat-related temporary attributes from a combatant."""
        if hasattr(combatant, "db"):
            combatant.db.in_combat = False
            combatant.db.combat_target = None

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _resolve(self, dbref):
        """
        Resolve a dbref string to a live object.

        Returns None if the object no longer exists.
        """
        if not dbref:
            return None
        try:
            from evennia import search_object
            results = search_object(dbref)
            return results[0] if results else None
        except Exception:
            return None

    def _is_alive(self, combatant):
        """Check if a combatant is alive."""
        if hasattr(combatant, "is_alive"):
            return combatant.is_alive()
        if hasattr(combatant, "get_hp"):
            return combatant.get_hp() > 0
        return True

    def _get_hp(self, combatant):
        """Get a combatant's current HP."""
        if hasattr(combatant, "get_hp"):
            try:
                return combatant.get_hp()
            except Exception:
                return 0
        return 0

    def _display_name(self, combatant):
        """Get a display-safe name for combat messages."""
        if hasattr(combatant, "get_display_name"):
            try:
                return combatant.get_display_name(combatant)
            except Exception:
                pass
        return getattr(combatant, "key", "something")


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _mob_condition(mob):
    """
    Return a qualitative condition string based on a mob's HP percentage.

    Returns None if the mob is at full health (no need to report).
    """
    hp = mob.get_hp() if hasattr(mob, "get_hp") else 0
    hp_max = mob.get_hp_max() if hasattr(mob, "get_hp_max") else 1

    if hp_max <= 0:
        return "|xis dead|n"

    ratio = hp / hp_max

    if ratio >= 1.0:
        return None  # no report at full health
    elif ratio > 0.75:
        return "has a few scratches"
    elif ratio > 0.50:
        return "|yis bleeding|n"
    elif ratio > 0.25:
        return "|yis badly wounded|n"
    elif ratio > 0.10:
        return "|ris severely hurt|n"
    elif ratio > 0:
        return "|r*** is nearly dead ***|n"
    else:
        return "|xis dead|n"
