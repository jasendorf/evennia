"""
Needs System Contrib
====================

Contribution by DorfinMUD project, 2025

A generic, game-agnostic system for tracking character needs — hunger, thirst,
fatigue, or any other resource that decays over time and has consequences at
low thresholds.

This contrib is intentionally bare of game-specific content. It provides the
engine; your game provides the flavour. See the DorfinMUD extension
(contrib_dorfin/dorfin_needs.py) for an example of how to extend it.

---

OVERVIEW
--------

The system has four components:

  NeedsHandler   — Attached to a character via @lazy_property. Stores and
                   manages the current values for all registered needs.

  NeedsScript    — A persistent Evennia Script attached to the character.
                   Calls handler.tick() on a configurable interval.

  BaseNeedsBuff  — A BaseBuff subclass (requires evennia.contrib.rpg.buffs).
                   Extend this to apply stat penalties at low thresholds.

  NeedsCharacterMixin — Mixin for your Character typeclass. Wires up the
                   handler and script, and provides at_object_creation hooks.

---

INSTALLATION
------------

1. Add `evennia.contrib.rpg.buffs` to your game (see Contrib-Buffs docs).

2. Have your Character typeclass inherit from NeedsCharacterMixin:

    from evennia.utils import lazy_property
    from contrib_dorfin.needs import NeedsCharacterMixin

    class Character(NeedsCharacterMixin, DefaultCharacter):
        pass

3. In your Character's at_object_creation, register your needs:

    def at_object_creation(self):
        super().at_object_creation()
        self.needs.add(
            "hunger",
            decay_rate=5,
            thresholds=[
                (50, self._on_hunger_moderate),
                (25, self._on_hunger_low),
                (0,  self._on_hunger_critical),
            ]
        )

4. Start the needs script (called automatically by NeedsCharacterMixin):

    self.needs.start_script()

---

NEED VALUES
-----------

Each need has a value from 0 to 100.
100 = fully satisfied.
0   = completely depleted.

decay_rate is subtracted from the value each tick.
restore(name, amount) adds to the value (capped at 100).

---

THRESHOLDS
----------

Thresholds are (value, callback) tuples. When a need's value crosses a
threshold (going downward), the callback is fired. It will not fire again
until the need has been restored above the threshold and crosses it again.

The callback signature is:  callback(character, need_name, value)

---

CONFIGURATION
-------------

NeedsScript.TICK_INTERVAL  — Seconds between ticks (default: 3600 = 1 hour).
                              Override on your subclass or pass interval=
                              when calling start_script().

---

CONTRIBUTING
------------

This contrib is designed to be contributed back to the Evennia project as
evennia.contrib.game_systems.needs. If you improve it, please consider
opening a PR at https://github.com/evennia/evennia.

Requirements for contribution:
  - No game-specific content (names, messages, stat references)
  - Full docstrings on all public methods
  - Tests in a companion needs_tests.py file

"""

from evennia import DefaultScript
from evennia.utils import lazy_property
from evennia.utils.logger import log_err

try:
    from evennia.contrib.rpg.buffs import BaseBuff, Mod
    _BUFFS_AVAILABLE = True
except ImportError:
    _BUFFS_AVAILABLE = False
    BaseBuff = object
    Mod = None


# ---------------------------------------------------------------------------
# NeedsHandler
# ---------------------------------------------------------------------------

class NeedsHandler:
    """
    Manages a collection of needs on a character.

    Attached to a character via @lazy_property:

        @lazy_property
        def needs(self):
            return NeedsHandler(self)

    Needs are stored in character.db.needs as a dict:

        {
            "hunger": {
                "value": 80,
                "decay_rate": 5,
                "thresholds": [50, 25, 0],
                "crossed": [],        # thresholds currently active (crossed down)
            },
            ...
        }

    Threshold callbacks are NOT stored in the db (not pickleable). They are
    registered at runtime via add() or register_callbacks(). The mixin's
    at_post_puppet hook re-registers them after a server reload.
    """

    def __init__(self, obj):
        """
        Args:
            obj: The object (Character) this handler is attached to.
        """
        self.obj = obj
        # Runtime-only callback registry: {need_name: {threshold_value: callable}}
        self._callbacks = {}

        if not self.obj.db.needs:
            self.obj.db.needs = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def add(self, name, decay_rate=5, initial_value=100, thresholds=None):
        """
        Register a new need on this character.

        Safe to call multiple times; will not reset an existing need's value.

        Args:
            name (str): Unique identifier for this need (e.g. "hunger").
            decay_rate (float): How much to subtract from the value per tick.
            initial_value (int): Starting value (0–100). Default 100.
            thresholds (list): Optional list of (value, callback) tuples.
                               callback(character, need_name, current_value)
        """
        needs = self.obj.db.needs or {}

        if name not in needs:
            needs[name] = {
                "value": max(0, min(100, initial_value)),
                "decay_rate": decay_rate,
                "thresholds": sorted(
                    [t[0] for t in thresholds] if thresholds else [],
                    reverse=True
                ),
                "crossed": [],
            }
            self.obj.db.needs = needs

        # Always register callbacks (even if need already existed — re-registers
        # after reload)
        if thresholds:
            self.register_callbacks(name, thresholds)

    def register_callbacks(self, name, thresholds):
        """
        Register runtime callbacks for a need's thresholds.

        Called by add() and also by the mixin's at_post_puppet to restore
        callbacks after a server reload.

        Args:
            name (str): The need name.
            thresholds (list): List of (value, callback) tuples.
        """
        if name not in self._callbacks:
            self._callbacks[name] = {}
        for threshold_value, callback in thresholds:
            self._callbacks[name][threshold_value] = callback

    # ------------------------------------------------------------------
    # Value access
    # ------------------------------------------------------------------

    def get(self, name):
        """
        Return the current value of a need.

        Args:
            name (str): The need name.

        Returns:
            float: Current value (0–100), or None if need not registered.
        """
        needs = self.obj.db.needs or {}
        need = needs.get(name)
        return need["value"] if need else None

    def get_all(self):
        """
        Return a copy of all needs and their current values.

        Returns:
            dict: {name: value, ...}
        """
        needs = self.obj.db.needs or {}
        return {name: data["value"] for name, data in needs.items()}

    def is_registered(self, name):
        """Return True if a need with this name has been registered."""
        return name in (self.obj.db.needs or {})

    # ------------------------------------------------------------------
    # Value modification
    # ------------------------------------------------------------------

    def restore(self, name, amount):
        """
        Increase a need's value by amount (capped at 100).

        Also clears any thresholds that are no longer applicable after
        the restore, so they can fire again if the need drops back down.

        Args:
            name (str): The need name.
            amount (float): How much to restore (positive number).

        Returns:
            float: The new value, or None if the need is not registered.
        """
        needs = self.obj.db.needs or {}
        if name not in needs:
            return None

        old_value = needs[name]["value"]
        new_value = min(100, old_value + amount)
        needs[name]["value"] = new_value

        # Clear any thresholds we've now risen above
        crossed = needs[name].get("crossed", [])
        needs[name]["crossed"] = [t for t in crossed if t > new_value]

        self.obj.db.needs = needs
        return new_value

    def set(self, name, value):
        """
        Directly set a need's value (clamped to 0–100).

        Args:
            name (str): The need name.
            value (float): The new value.
        """
        needs = self.obj.db.needs or {}
        if name not in needs:
            return
        needs[name]["value"] = max(0, min(100, value))
        self.obj.db.needs = needs

    # ------------------------------------------------------------------
    # Tick & threshold checking
    # ------------------------------------------------------------------

    def tick(self):
        """
        Decrement all needs by their decay_rate.

        Called by NeedsScript.at_repeat(). After ticking, calls
        check_thresholds() automatically.
        """
        needs = self.obj.db.needs or {}
        for name, data in needs.items():
            data["value"] = max(0, data["value"] - data["decay_rate"])
        self.obj.db.needs = needs
        self.check_thresholds()

    def check_thresholds(self):
        """
        Check all needs against their thresholds and fire any callbacks
        for thresholds that have newly been crossed.

        A threshold fires once per crossing — it will not fire again until
        the need is restored above the threshold level.
        """
        needs = self.obj.db.needs or {}

        for name, data in needs.items():
            current_value = data["value"]
            crossed = set(data.get("crossed", []))
            thresholds = data.get("thresholds", [])
            callbacks = self._callbacks.get(name, {})

            for threshold_value in thresholds:
                if current_value <= threshold_value and threshold_value not in crossed:
                    # Newly crossed — fire callback if registered
                    crossed.add(threshold_value)
                    cb = callbacks.get(threshold_value)
                    if cb:
                        try:
                            cb(self.obj, name, current_value)
                        except Exception as e:
                            log_err(
                                f"NeedsHandler: error in threshold callback "
                                f"for {name}/{threshold_value}: {e}"
                            )

            data["crossed"] = list(crossed)

        self.obj.db.needs = needs

    # ------------------------------------------------------------------
    # Script management
    # ------------------------------------------------------------------

    def start_script(self, interval=None):
        """
        Attach a NeedsScript to this character if one isn't already running.

        Args:
            interval (int): Tick interval in seconds. Defaults to
                            NeedsScript.TICK_INTERVAL (3600).
        """
        existing = self.obj.scripts.get("NeedsScript")
        if existing:
            return existing[0]

        kwargs = {"key": "NeedsScript", "obj": self.obj, "persistent": True}
        if interval is not None:
            kwargs["interval"] = interval

        script = self.obj.scripts.add(NeedsScript, **kwargs)
        return script

    def stop_script(self):
        """Stop and remove the NeedsScript from this character."""
        for script in self.obj.scripts.get("NeedsScript"):
            script.stop()

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def display(self, names=None):
        """
        Return a formatted string showing current need values.

        Args:
            names (list): Optional list of need names to show.
                          If None, shows all needs.

        Returns:
            str: Formatted needs display.
        """
        needs = self.obj.db.needs or {}
        if names:
            needs = {k: v for k, v in needs.items() if k in names}

        if not needs:
            return "No needs registered."

        lines = []
        for name, data in needs.items():
            value = data["value"]
            bar = _render_bar(value, 100, width=20)
            color = "|g" if value > 50 else ("|y" if value > 25 else "|r")
            lines.append(
                f"  {name.capitalize():<12} {bar} {color}{value:>3.0f}/100|n"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# NeedsScript
# ---------------------------------------------------------------------------

class NeedsScript(DefaultScript):
    """
    Persistent script attached to a character. Calls needs.tick() each interval.

    Override TICK_INTERVAL on a subclass to change the default.
    """

    TICK_INTERVAL = 3600  # 1 real hour

    def at_script_creation(self):
        self.key = "NeedsScript"
        self.desc = "Manages character needs decay."
        self.interval = self.TICK_INTERVAL
        self.persistent = True
        self.start_delay = True  # Don't tick immediately on attach

    def at_repeat(self):
        """Called every interval. Ticks the needs handler."""
        obj = self.obj
        if not obj:
            self.stop()
            return
        if hasattr(obj, "needs"):
            obj.needs.tick()


# ---------------------------------------------------------------------------
# BaseNeedsBuff
# ---------------------------------------------------------------------------

if _BUFFS_AVAILABLE:
    class BaseNeedsBuff(BaseBuff):
        """
        Base class for buffs applied as penalties when a need drops to a
        critical threshold.

        Extend this class and override:
            key          — unique string identifier
            name         — human-readable buff name
            flavor       — description shown to the player
            need_name    — which need triggers this buff (e.g. "hunger")
            mods         — list of Mod objects for stat penalties
            duration     — how long the buff lasts (-1 = until manually removed)

        The buff is applied by your threshold callback and removed when the
        character's need is restored above the threshold.

        Example:

            class HungerDebuff(BaseNeedsBuff):
                key = "hunger_low"
                name = "Hungry"
                flavor = "Your empty stomach makes it hard to focus."
                need_name = "hunger"
                duration = -1  # permanent until need is restored
                mods = [
                    Mod("str", "add", -3),
                    Mod("con", "add", -2),
                ]
        """

        key = "base_need_buff"
        name = "Need Penalty"
        flavor = "A need is critically low."
        need_name = ""
        duration = -1

        def at_apply(self, *args, **kwargs):
            """Called when the buff is applied."""
            pass

        def at_remove(self, *args, **kwargs):
            """Called when the buff is removed."""
            pass

else:
    # Fallback if Buffs contrib is not installed
    class BaseNeedsBuff:
        """Placeholder — install evennia.contrib.rpg.buffs to use needs penalties."""
        pass


# ---------------------------------------------------------------------------
# NeedsCharacterMixin
# ---------------------------------------------------------------------------

class NeedsCharacterMixin:
    """
    Mixin for Character typeclasses. Wires up the NeedsHandler and NeedsScript.

    Usage:

        from contrib_dorfin.needs import NeedsCharacterMixin
        from evennia.utils import lazy_property

        class Character(NeedsCharacterMixin, DefaultCharacter):

            def at_object_creation(self):
                super().at_object_creation()
                # Register your needs here (or in a subclass mixin)
                self.needs.add("hunger", decay_rate=5, thresholds=[...])
                self.needs.add("thirst", decay_rate=7, thresholds=[...])
                self.needs.start_script()

            def _register_need_callbacks(self):
                # Called by at_post_puppet to re-register callbacks after reload.
                # Override in your subclass.
                pass

    The mixin provides:
        - `self.needs` (@lazy_property NeedsHandler)
        - `at_post_puppet` hook that restarts the script and re-registers callbacks
    """

    @lazy_property
    def needs(self):
        """The NeedsHandler attached to this character."""
        return NeedsHandler(self)

    def at_object_creation(self):
        """
        Called once when the object is first created.
        Subclasses should call super() and then register their needs.
        """
        super().at_object_creation()

    def at_post_puppet(self, **kwargs):
        """
        Called after a player puppets this character. Restarts the needs
        script if it has stopped (e.g. after a server reload) and
        re-registers threshold callbacks (which are not persistent).
        """
        super().at_post_puppet(**kwargs)
        self.needs.start_script()
        self._register_need_callbacks()

    def _register_need_callbacks(self):
        """
        Override in your subclass to re-register threshold callbacks.

        This is called by at_post_puppet after a reload. Without it,
        thresholds would be tracked correctly but no callbacks would fire.

        Example:

            def _register_need_callbacks(self):
                self.needs.register_callbacks("hunger", [
                    (50, self._on_hunger_moderate),
                    (25, self._on_hunger_low),
                    (0,  self._on_hunger_critical),
                ])
        """
        pass


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _render_bar(current, maximum, width=20, fill="|", empty="-"):
    """
    Render a simple ASCII progress bar.

    Args:
        current (float): Current value.
        maximum (float): Maximum value.
        width (int): Total bar width in characters.
        fill (str): Character for filled portion.
        empty (str): Character for empty portion.

    Returns:
        str: Formatted bar string like [||||||||||||--------]
    """
    if maximum <= 0:
        ratio = 0
    else:
        ratio = max(0.0, min(1.0, current / maximum))
    filled = int(ratio * width)
    return "[" + fill * filled + empty * (width - filled) + "]"
