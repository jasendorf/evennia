"""
Account

The Account represents the game "account" and each login has only one
temporary Account object. What a given Account can do is controlled by
its available cmdsets.
"""

from evennia.accounts.accounts import DefaultAccount


class Account(DefaultAccount):
    """
    This is the base Account typeclass for DorfinMUD, implementing
    the default Account. Inherit from this to create different
    Account types for the game.
    """

    pass
