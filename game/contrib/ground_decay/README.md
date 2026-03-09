# Ground Decay System

Automatically removes items left on the ground after a configurable delay
based on the item's level. Low-level junk vanishes in minutes; high-level
gear persists for hours.

## Quick Start

Add `GroundDecayMixin` to your item base class, **before** the Evennia parent:

```python
from contrib.ground_decay.ground_decay import GroundDecayMixin
from evennia.objects.objects import DefaultObject

class MyItem(GroundDecayMixin, DefaultObject):
    ...
```

That's it. Items dropped in rooms will now decay automatically.

## Configuration

### Module Constants

Override these in `ground_decay.py` or by subclassing:

| Constant | Default | Description |
|---|---|---|
| `MIN_DECAY` | 120 | Minimum decay time in seconds (floor for level 1) |
| `SECONDS_PER_LEVEL` | 90 | Seconds of ground time per item level |
| `WARN_THRESHOLD` | 30 | Warning message fires this many seconds before decay |
| `SCAN_INTERVAL` | 15 | How often the global ticker runs (seconds) |

### Per-Item Attributes

| Attribute | Type | Description |
|---|---|---|
| `db.item_level` | int | Controls decay duration (primary) |
| `db.level` | int | Fallback if `item_level` is not set |
| `db.no_decay` | bool | Set `True` to exempt an item from decay |

### Decay Formula

```
decay_seconds = max(MIN_DECAY, item_level * SECONDS_PER_LEVEL)
```

There is no upper cap.

| Level | Decay Time | Human-Readable |
|---|---|---|
| 1 | 120 seconds | 2 minutes |
| 5 | 450 seconds | 7.5 minutes |
| 10 | 900 seconds | 15 minutes |
| 20 | 1800 seconds | 30 minutes |
| 40 | 3600 seconds | 1 hour |
| 100 | 9000 seconds | 2.5 hours |

## How It Works

### Architecture

The system uses a **single global script** (`GroundDecayTicker`) that scans
all ground items every `SCAN_INTERVAL` seconds. Items are tracked using
Evennia tags and a persistent timestamp attribute — no per-item scripts are
created.

### Flow

1. Player drops an item (or a mob dies, or an item is teleported/created in a room)
2. `GroundDecayMixin.at_post_move()` fires and calls `_check_ground_state()`
3. The item gets an `on_ground` tag and `db.ground_dropped_at` timestamp
4. The global ticker sees the tagged item on its next scan
5. When `WARN_THRESHOLD` seconds remain, the room sees: *"sword is starting to fade..."*
6. When time expires, the item is deleted: *"sword crumbles to dust and vanishes."*
7. If the item is picked up before decay, the tag and timestamp are cleared

### Server Restarts

- `at_init()` fires for every object on reload — items already on the ground
  keep their existing timestamps (no extra time granted)
- The global ticker is persistent and survives restarts
- If the ticker is missing (first boot), `_ensure_ticker()` creates it automatically

### What Counts as "On the Ground"

An item is considered on the ground if its `location` is:
- An instance of `evennia.objects.objects.DefaultRoom`, **or**
- An object with no parent location that has an `exits` attribute (fallback for custom room types)

Items inside containers, carried by characters, or in limbo (`location=None`)
are not on the ground.

## Troubleshooting

All commands below can be run from the game client with `@py`.

**Check if an item has decay state:**
```
@py item = self.search("sword"); print(item.tags.get("on_ground", category="ground_decay"), item.db.ground_dropped_at)
```

**Check if the global ticker is running:**
```
@py import evennia; print(evennia.search_script("GroundDecayTicker"))
```

**Manually stamp an item for decay:**
```
@py from contrib.ground_decay.ground_decay import _mark_on_ground; _mark_on_ground(self.search("sword"))
```

**Manually clear decay state:**
```
@py from contrib.ground_decay.ground_decay import _clear_ground_state; _clear_ground_state(self.search("sword"))
```

**Check how long until an item decays:**
```
@py import time; from contrib.ground_decay.ground_decay import get_decay_time; item = self.search("sword"); remaining = get_decay_time(item) - (time.time() - item.db.ground_dropped_at); print(f"{remaining:.0f}s remaining")
```

**Verify no old per-item scripts remain:**
```
@py from evennia.scripts.models import ScriptDB; print(ScriptDB.objects.filter(db_key__in=["GroundDecayScript", "GroundDecayWarningScript"]).count())
```
