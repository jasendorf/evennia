"""
Scripts

Scripts are powerful jacks-of-all-trades. They have no location and
can store arbitrary data on themselves. They can be used to implement
game rules, time-based events, and more.
"""

from evennia.scripts.scripts import DefaultScript


class Script(DefaultScript):
    """
    This is the base Script typeclass for DorfinMUD. Inherit from
    this to create different types of scripts.
    """

    pass
