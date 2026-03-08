"""
Channel

The channel class represents an in-game communication channel. It is
used by the channel system to send messages to all connected objects.
"""

from evennia.comms.comms import DefaultChannel


class Channel(DefaultChannel):
    """
    This is the base Channel typeclass for DorfinMUD. Inherit from
    this to create different types of communication channels.
    """

    pass
