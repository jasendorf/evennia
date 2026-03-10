# Ground Decay -- DorfinMUD Notes

Implementation notes for the ground decay system. The generic contrib
lives in `contrib/ground_decay/`. This file covers DorfinMUD-specific
integration and lessons learned.

## Integration

`AwtownItem`, `AwtownClothing`, and `AwtownContainer` all inherit
`GroundDecayMixin`. The import in `typeclasses/items.py` points to the
contrib:

```python
from contrib.ground_decay.ground_decay import GroundDecayMixin
```

A backward-compat re-export exists in `contrib_dorfin/ground_decay.py`
so any old imports still work.

## Evennia Gotchas

### `at_after_move` vs `at_post_move`

Modern Evennia (`evennia/evennia:latest`) calls `at_post_move()` from
`move_to()`, not `at_after_move()`. The mixin overrides both for
backward compatibility.

### `at_init` and DB writes

`at_init` fires during idmapper hydration before the object is fully
connected to the database. Any DB writes (`db.*`, `tags.add`, etc.) will
raise:

```
ValueError: instance is on database "None", value is on database "default"
```

Fix: defer all DB work with `evennia.utils.delay(0, callback)`.

### Script `.restart()` does not exist

Evennia scripts have `.start()` and `.stop()` but not `.restart()`. Use
`script.stop(); script.start()` instead.

### Persistent scripts and Twisted registration

A script can exist in the database with `is_active=True` but not be
registered with Twisted's TickerHandler (so `at_repeat` never fires).
This happens when a script is created during a deferred context. Fix:
call `.stop(); .start()` once per server process to force re-registration.

## Migration from Per-Item Scripts

The old implementation created two scripts per ground item:
`GroundDecayScript` and `GroundDecayWarningScript`. The
`_migrate_old_scripts()` function runs automatically on first ticker
creation and cleans these up, stamping their items with the new
tag/timestamp system.
