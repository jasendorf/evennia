"""
Ground Decay System for Evennia
================================

Automatically removes items left on the ground (in rooms) after a
configurable delay based on the item's level. Low-level junk vanishes
quickly; high-level gear persists longer.

Architecture
------------

A single global ``GroundDecayTicker`` script runs every ``SCAN_INTERVAL``
seconds and processes all ground items in one pass. Items are tracked via
lightweight tags and a persistent timestamp attribute — no per-item
scripts are created.

This design is robust against server restarts, code reloads, and items
that reach the ground through any mechanism (drops, mob death, teleport,
``create_object``, etc.).

Decay Formula
-------------

::

    decay_seconds = max(MIN_DECAY, item_level * SECONDS_PER_LEVEL)

With default settings:

    ======  ==============  ============
    Level   Decay time      Human
    ======  ==============  ============
      1     120 seconds     2 minutes
      5     450 seconds     7.5 minutes
     10     900 seconds     15 minutes
     20     1800 seconds    30 minutes
     40     3600 seconds    1 hour
    100     9000 seconds    2.5 hours
    ======  ==============  ============

There is no upper cap — higher-level items simply last proportionally
longer.

Quick Start
-----------

1. Add ``GroundDecayMixin`` to your item base class, **before** the
   Evennia parent::

       from contrib.ground_decay.ground_decay import GroundDecayMixin

       class MyItem(GroundDecayMixin, DefaultObject):
           ...

   That's it. The mixin handles everything automatically.

2. Items that should never decay (quest items, permanent fixtures)::

       item.db.no_decay = True

3. Control decay duration via the item's level::

       item.db.item_level = 10   # 15 minutes on the ground

   Falls back to ``db.level``, then defaults to 1.

How It Works
------------

- When an item is moved (via ``move_to``), the mixin's ``at_post_move``
  hook checks whether the item landed in a room. If so, it adds an
  ``on_ground`` tag and sets ``db.ground_dropped_at`` to the current
  Unix timestamp.

- When picked up (moved to a character or container), the tag and
  timestamp are cleared.

- The ``GroundDecayTicker`` global script scans all tagged items every
  ``SCAN_INTERVAL`` seconds. Items whose timestamp has expired are
  deleted with a room message. A warning message fires
  ``WARN_THRESHOLD`` seconds before deletion.

- On server restart/reload, ``at_init`` re-checks every item's ground
  state, preserving existing timestamps so items don't get extra time.

- The global ticker is auto-created on first ``at_init`` call — no
  manual setup or settings.py changes required.

Depends On
----------

- ``evennia.DefaultScript``
- ``evennia.objects.objects.DefaultRoom``
"""

import time as _time

from evennia import DefaultScript

# ---------------------------------------------------------------------------
# Configuration — override these at module level or subclass to customize
# ---------------------------------------------------------------------------

MIN_DECAY = 120            # minimum decay time in seconds (level 1 floor)
SECONDS_PER_LEVEL = 90     # seconds of ground time per item level
WARN_THRESHOLD = 30        # warning message fires this many seconds before decay
SCAN_INTERVAL = 15         # how often the global ticker runs (seconds)

# Tag constants (used internally)
GROUND_TAG = "on_ground"
GROUND_TAG_CATEGORY = "ground_decay"
WARNED_TAG = "decay_warned"

# Module-level flag — ensures the global ticker check runs at most once
# per server process.
_ticker_checked = False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_decay_time(item):
    """
    Calculate how long an item should persist on the ground.

    Reads ``db.item_level`` first, then ``db.level``, then falls back
    to 1. Returns ``max(MIN_DECAY, level * SECONDS_PER_LEVEL)``.

    Args:
        item: An Evennia object with a ``db`` handler.

    Returns:
        int: Seconds before the item should decay.
    """
    level = (
        getattr(item.db, "item_level", None)
        or getattr(item.db, "level", None)
        or 1
    )
    level = max(1, int(level))
    return max(MIN_DECAY, level * SECONDS_PER_LEVEL)


def is_on_ground(item):
    """
    Check whether an item is on the ground (located directly inside a
    room, not carried by a character or inside a container).

    Args:
        item: An Evennia object.

    Returns:
        bool: True if the item's location is a DefaultRoom.
    """
    if not item.location:
        return False

    loc = item.location

    from evennia.objects.objects import DefaultRoom

    if isinstance(loc, DefaultRoom):
        return True

    # Fallback for custom room types that don't inherit DefaultRoom:
    # if the location sits at the top of the containment hierarchy and
    # has exits, treat it as a room.
    if loc.location is None and hasattr(loc, "exits"):
        return True

    return False


# ---------------------------------------------------------------------------
# GroundDecayTicker — single global script
# ---------------------------------------------------------------------------

class GroundDecayTicker(DefaultScript):
    """
    A persistent global script that scans all ground-tagged items and
    handles decay timing, warnings, and deletion.

    Created automatically by ``_ensure_ticker()`` on first server boot.
    One instance exists for the entire game — it is not attached to any
    particular object.
    """

    def at_script_creation(self):
        self.key = "GroundDecayTicker"
        self.desc = "Global ground-item decay scanner."
        self.persistent = True
        self.interval = SCAN_INTERVAL
        self.start_delay = True

        # Run one-time migration from old per-item scripts
        _migrate_old_scripts()

    def at_repeat(self):
        """Scan all tagged ground items and process decay."""
        from evennia.utils.search import search_tag

        now = _time.time()
        tagged_items = search_tag(GROUND_TAG, category=GROUND_TAG_CATEGORY)

        for item in tagged_items:
            # Safety: if the item is no longer on the ground, clean up
            if not is_on_ground(item):
                _clear_ground_state(item)
                continue

            dropped_at = item.db.ground_dropped_at
            if not dropped_at:
                # Tag exists but no timestamp (recovery case) — stamp now
                item.db.ground_dropped_at = now
                continue

            decay_time = get_decay_time(item)
            elapsed = now - dropped_at
            remaining = decay_time - elapsed

            # Decay: time's up
            if elapsed >= decay_time:
                room = item.location
                item_name = item.key
                item.delete()
                if room:
                    room.msg_contents(
                        f"|x{item_name} crumbles to dust and vanishes.|n"
                    )
                continue

            # Warning: close to decay, not yet warned
            if (remaining <= WARN_THRESHOLD
                    and not item.tags.has(WARNED_TAG,
                                          category=GROUND_TAG_CATEGORY)):
                item.tags.add(WARNED_TAG, category=GROUND_TAG_CATEGORY)
                room = item.location
                if room:
                    room.msg_contents(
                        f"|x{item.key} is starting to fade...|n"
                    )


# ---------------------------------------------------------------------------
# GroundDecayMixin — add to your item typeclass
# ---------------------------------------------------------------------------

class GroundDecayMixin:
    """
    Mixin for item typeclasses that enables automatic ground decay.

    Add this **before** the Evennia parent class in your item's MRO::

        class MyItem(GroundDecayMixin, DefaultObject):
            ...

    The mixin hooks into ``at_post_move`` (and ``at_after_move`` for
    backward compatibility) to tag/untag items automatically. It also
    handles server restarts via ``at_init``.

    Attributes read from the item:
        db.no_decay    (bool) — if True, this item never decays
        db.item_level  (int)  — controls decay duration (fallback: db.level)

    Attributes managed by the mixin:
        db.ground_dropped_at  (float) — Unix timestamp when item hit the ground
    """

    def at_init(self):
        """Called on server reload — re-check ground state."""
        super().at_init()
        _ensure_ticker()
        self._check_ground_state()

    def at_post_move(self, source_location, move_type="move", **kwargs):
        """Called by Evennia's move_to() after the item arrives."""
        super().at_post_move(source_location, move_type=move_type, **kwargs)
        self._check_ground_state()

    def at_after_move(self, source_location, **kwargs):
        """Backward-compatible hook (older Evennia versions)."""
        super().at_after_move(source_location, **kwargs)
        self._check_ground_state()

    def _check_ground_state(self):
        """
        Idempotent check: tag and timestamp the item if it's on the
        ground, or clear that state if it's not.
        """
        if getattr(self.db, "no_decay", False):
            _clear_ground_state(self)
            return

        if is_on_ground(self):
            _mark_on_ground(self)
        else:
            _clear_ground_state(self)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _mark_on_ground(item):
    """Tag an item as being on the ground and set its drop timestamp."""
    if not item.tags.has(GROUND_TAG, category=GROUND_TAG_CATEGORY):
        item.tags.add(GROUND_TAG, category=GROUND_TAG_CATEGORY)
    if not item.db.ground_dropped_at:
        item.db.ground_dropped_at = _time.time()


def _clear_ground_state(item):
    """Remove ground tags and timestamp from an item."""
    item.tags.remove(GROUND_TAG, category=GROUND_TAG_CATEGORY)
    item.tags.remove(WARNED_TAG, category=GROUND_TAG_CATEGORY)
    item.db.ground_dropped_at = None


def _ensure_ticker():
    """
    Ensure the global GroundDecayTicker script exists. Uses a
    module-level flag so only one DB check happens per server process.
    """
    global _ticker_checked
    if _ticker_checked:
        return
    _ticker_checked = True

    from evennia.utils.search import search_script

    if not search_script("GroundDecayTicker"):
        from evennia import create_script
        create_script(
            GroundDecayTicker,
            key="GroundDecayTicker",
            persistent=True,
            autostart=True,
        )


def _migrate_old_scripts():
    """
    One-time migration: find and remove old per-item GroundDecayScript
    and GroundDecayWarningScript instances left over from the previous
    implementation. Stamps their items so decay continues seamlessly.
    """
    from evennia.scripts.models import ScriptDB

    old_keys = ("GroundDecayScript", "GroundDecayWarningScript")
    old_scripts = ScriptDB.objects.filter(db_key__in=old_keys)

    count = old_scripts.count()
    if not count:
        return

    from evennia.utils.logger import log_info

    for script in old_scripts:
        item = script.obj
        if item and is_on_ground(item):
            _mark_on_ground(item)
        script.delete()

    log_info(f"GroundDecay: migrated {count} old per-item script(s).")
