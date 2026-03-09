"""
DorfinMUD Ground Decay — thin wrapper around contrib.ground_decay.

The generic, game-agnostic implementation lives in:
    contrib/ground_decay/ground_decay.py

This module re-exports everything so existing imports continue to work.
"""

from contrib.ground_decay.ground_decay import (  # noqa: F401
    MIN_DECAY,
    SECONDS_PER_LEVEL,
    WARN_THRESHOLD,
    SCAN_INTERVAL,
    get_decay_time,
    is_on_ground,
    GroundDecayTicker,
    GroundDecayMixin,
)
