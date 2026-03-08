"""
Object

The Object is the basic in-game entity. It can represent items, furniture,
and other things that exist in the game world but are not characters.
"""

from evennia.objects.objects import DefaultObject


class Object(DefaultObject):
    """
    This is the base Object typeclass for DorfinMUD. Inherit from
    this to create different types of in-game objects.
    """

    pass
