"""
Item Ground Decay System
========================

Items left on the ground (in a room, not carried) will eventually
vanish. The decay timer is based on the item's level — low-level
junk disappears quickly, high-level gear lingers longer.

Formula:
    decay_seconds = min(MAX_DECAY, max(MIN_DECAY, item_level * SECONDS_PER_LEVEL))

Defaults:
    Level  1 → 120 seconds  (2 minutes)
    Level  5 → 450 seconds  (7.5 minutes)
    Level 10 → 900 seconds  (15 minutes)
    Level 20 → 1800 seconds (30 minutes)
    Level 40 → 3600 seconds (60 minutes — cap)

Integration:
    Add the GroundDecayMixin to AwtownItem (or any item base class):

        class AwtownItem(GroundDecayMixin, DefaultObject):
            ...

    The mixin hooks into at_after_move() to start/cancel the decay
    timer automatically. No other changes needed.

    Items that should NEVER decay can set:
        item.db.no_decay = True

Depends on:
    evennia.DefaultScript  -- for the decay timer script
"""

from evennia import DefaultScript

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MIN_DECAY = 120       # minimum 2 minutes even for level 0/1 items
MAX_DECAY = 3600      # maximum 60 minutes even for very high level items
SECONDS_PER_LEVEL = 90   # 90 seconds per item level

# Warning message threshold — items warn the room when close to vanishing
WARN_THRESHOLD = 30   # seconds before vanishing to show a warning


def get_decay_time(item):
    """
    Calculate how long an item should persist on the ground.

    Uses db.item_level first, then db.level, then falls back to 1.

    Args:
        item: The item object.

    Returns:
        int: Seconds before the item decays.
    """
    level = (
        getattr(item.db, "item_level", None)
        or getattr(item.db, "level", None)
        or 1
    )
    level = max(1, int(level))
    return min(MAX_DECAY, max(MIN_DECAY, level * SECONDS_PER_LEVEL))


# ---------------------------------------------------------------------------
# GroundDecayScript — attached to items on the ground
# ---------------------------------------------------------------------------

class GroundDecayScript(DefaultScript):
    """
    A timer script attached to an item that's been dropped on the ground.
    When it fires, the item is deleted. Shows a warning shortly before.
    """

    def at_script_creation(self):
        self.key = "GroundDecayScript"
        self.desc = "Removes an item from the ground after a delay."
        self.persistent = True
        self.interval = MIN_DECAY   # real default — overridden by _start_decay
        self.repeats = 1
        self.start_delay = True
        self.db.warned = False

    def at_repeat(self):
        """Called when the timer fires — delete the item."""
        item = self.obj
        if not item:
            self.delete()
            return

        # Check if item is still on the ground (in a room)
        if not _is_on_ground(item):
            self.delete()
            return

        room = item.location

        # Delete the item
        item_name = item.key
        item.delete()

        # Notify the room
        if room:
            room.msg_contents(
                f"|x{item_name} crumbles to dust and vanishes.|n"
            )


class GroundDecayWarningScript(DefaultScript):
    """
    A separate short timer that fires a warning before the item decays.
    """

    def at_script_creation(self):
        self.key = "GroundDecayWarningScript"
        self.desc = "Warns that an item is about to vanish."
        self.persistent = False
        self.interval = MIN_DECAY   # real default — overridden by _start_decay
        self.repeats = 1
        self.start_delay = True

    def at_repeat(self):
        item = self.obj
        if not item or not _is_on_ground(item):
            self.delete()
            return

        room = item.location
        if room:
            room.msg_contents(
                f"|x{item.key} is starting to fade...|n"
            )
        self.delete()


# ---------------------------------------------------------------------------
# GroundDecayMixin — add to your item base class
# ---------------------------------------------------------------------------

class GroundDecayMixin:
    """
    Mixin for item typeclasses that enables automatic ground decay.

    When an item is moved to a room (dropped on the ground), a decay
    timer starts. When picked up, the timer is cancelled.

    Set db.no_decay = True on items that should never decay (quest items,
    permanent fixtures, etc.)

    Set db.item_level to control decay duration. Falls back to db.level,
    then defaults to level 1 (2 minutes).
    """

    def at_init(self):
        """Called on server reload. Start decay if already on the ground."""
        super().at_init()
        if getattr(self.db, "no_decay", False):
            return
        if _is_on_ground(self):
            existing = self.scripts.get("GroundDecayScript")
            if existing:
                # Restart to fix potentially dead tickers from old code
                for s in existing:
                    if s.interval <= 0:
                        s.interval = get_decay_time(self)
                    s.restart()
            else:
                _start_decay(self)
        else:
            # Not on ground — cancel any stale scripts
            _cancel_decay(self)

    def at_after_move(self, source_location, **kwargs):
        """Called after the item is moved to a new location."""
        super().at_after_move(source_location, **kwargs)

        if getattr(self.db, "no_decay", False):
            return

        from evennia.utils.logger import log_info
        on_ground = _is_on_ground(self)
        log_info(
            f"GroundDecay.at_after_move: {self.key} ({self.dbref}) "
            f"src={source_location} dest={self.location} "
            f"on_ground={on_ground}"
        )

        if on_ground:
            _start_decay(self)
        else:
            _cancel_decay(self)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_on_ground(item):
    """
    Check if an item is on the ground (in a room, not carried by
    a character or inside a container).
    """
    if not item.location:
        return False

    loc = item.location

    # Check if location is a room (has exits, or is a DefaultRoom)
    from evennia.objects.objects import DefaultRoom
    if isinstance(loc, DefaultRoom):
        return True

    # Fallback: if the location has no location itself, it's probably a room
    # (rooms sit at the top of the containment hierarchy)
    if loc.location is None and hasattr(loc, "exits"):
        return True

    return False


def _start_decay(item):
    """Start or restart the decay timer on an item."""
    # Cancel any existing decay first
    _cancel_decay(item)

    decay_time = get_decay_time(item)

    from evennia import create_script

    # Main decay script — create, set interval, then restart to
    # ensure the Twisted ticker registers with the correct interval.
    script = create_script(
        GroundDecayScript,
        key="GroundDecayScript",
        obj=item,
        persistent=True,
        autostart=True,
    )
    if script.interval != decay_time:
        script.interval = decay_time
        script.restart()

    # Warning script (fires WARN_THRESHOLD seconds before decay)
    if decay_time > WARN_THRESHOLD * 2:
        warn_time = decay_time - WARN_THRESHOLD
        warn_script = create_script(
            GroundDecayWarningScript,
            key="GroundDecayWarningScript",
            obj=item,
            persistent=False,
            autostart=True,
        )
        if warn_script.interval != warn_time:
            warn_script.interval = warn_time
            warn_script.restart()


def _cancel_decay(item):
    """Cancel all decay scripts on an item (when picked up)."""
    for script_key in ("GroundDecayScript", "GroundDecayWarningScript"):
        existing = item.scripts.get(script_key)
        if existing:
            for s in existing:
                s.delete()
