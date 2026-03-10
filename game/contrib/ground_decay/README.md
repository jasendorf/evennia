# Ground Decay System

Automatically removes items left on the ground (in rooms) after a
configurable delay based on the item's level. Low-level junk vanishes in
minutes; high-level gear persists for hours.

## Quick Start

Add `GroundDecayMixin` to your item base class, **before** the Evennia parent:

```python
from contrib.ground_decay.ground_decay import GroundDecayMixin
from evennia.objects.objects import DefaultObject

class MyItem(GroundDecayMixin, DefaultObject):
    ...
```

That's it. The global ticker script is created automatically on first use.

## Configuration

### Module Constants

Edit these in `ground_decay.py` or override them in a subclass:

| Constant | Default | Description |
|---|---|---|
| `MIN_DECAY` | 120 | Floor decay time in seconds (even for level 1) |
| `SECONDS_PER_LEVEL` | 90 | Seconds of ground time per item level |
| `WARN_THRESHOLD` | 30 | Warning fires this many seconds before decay |
| `SCAN_INTERVAL` | 15 | Global ticker scan frequency in seconds |

### Per-Item Attributes

| Attribute | Type | Description |
|---|---|---|
| `db.item_level` | int | Controls decay duration (primary) |
| `db.level` | int | Fallback if `item_level` is not set |
| `db.no_decay` | bool | Set `True` to exempt an item from ever decaying |

### Decay Formula

```
decay_seconds = max(MIN_DECAY, item_level * SECONDS_PER_LEVEL)
```

There is no upper cap -- higher-level items simply last proportionally longer.

| Level | Decay Time | Human-Readable |
|---|---|---|
| 1 | 120 s | 2 minutes |
| 5 | 450 s | 7.5 minutes |
| 10 | 900 s | 15 minutes |
| 20 | 1800 s | 30 minutes |
| 40 | 3600 s | 1 hour |
| 100 | 9000 s | 2.5 hours |

## How It Works

### Architecture

A single **global script** (`GroundDecayTicker`) scans all ground items
every `SCAN_INTERVAL` seconds. Items are tracked with an Evennia tag and
a persistent timestamp attribute -- no per-item scripts are created.

### Lifecycle

1. An item reaches the ground (drop, mob death, teleport, `create_object`)
2. The mixin's `at_post_move` hook tags it `on_ground` and sets
   `db.ground_dropped_at` to the current time
3. The global ticker finds the tagged item on its next scan
4. When `WARN_THRESHOLD` seconds remain, the room sees:
   *"sword is starting to fade..."*
5. When time expires, the item is deleted:
   *"sword crumbles to dust and vanishes."*
6. If the item is picked up before decay, the tag and timestamp are cleared

### Server Restarts

- The ticker is persistent and survives restarts automatically
- `at_init` re-stamps any ground items, preserving their original timestamps
- If the ticker is missing (first boot or DB wipe), it is recreated on the
  next item interaction

### What Counts as "On the Ground"

An item is on the ground if its `location` is:
- An instance of `evennia.objects.objects.DefaultRoom`, or
- An object with no parent location that has an `exits` attribute
  (fallback for custom room types)

Items inside containers, carried by characters, or with no location are
not considered on the ground.

## Troubleshooting

Run these from the game client with `@py`.

**Is the ticker running?**
```
@py s = evennia.search_script("GroundDecayTicker"); print(s[0].is_active if s else "NOT FOUND")
```

**Check an item's decay state:**
```
@py item = self.search("sword"); print(item.tags.get("on_ground", category="ground_decay"), item.db.ground_dropped_at)
```

**Time remaining on an item:**
```
@py import time; from contrib.ground_decay.ground_decay import get_decay_time; item = self.search("sword"); print(f"{get_decay_time(item) - (time.time() - item.db.ground_dropped_at):.0f}s remaining")
```

**Force the ticker to scan now:**
```
@py evennia.search_script("GroundDecayTicker")[0].at_repeat()
```

**Manually exempt an item from decay:**
```
@py self.search("sword").db.no_decay = True
```
