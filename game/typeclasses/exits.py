"""
Awtown Exit typeclasses.

    AwtownGate     — orange gate that starts closed, auto-closes after a delay.
    AwtownCityGate — main city gate, starts open, no auto-close (day/night NPC
                     schedule added in Phase 4).

Gate pairs:
    Both directions of a gate passage must be AwtownGate instances.
    After creation, set db.pair on each exit to point at the reverse exit so
    that opening one side opens both, and closing one closes both.
"""

from evennia.objects.objects import DefaultExit
from evennia.utils.utils import delay


class AwtownGate(DefaultExit):
    """
    An orange gate exit that starts closed and auto-closes after CLOSE_DELAY seconds.

    db Attributes:
        is_open   (bool) : Current open/closed state. Default False.
        gate_name (str)  : How the gate is referenced in messages. Default "gate".
        pair      (Exit) : The matching exit in the destination room. Set after
                           creation by the batch script so open/close is synchronised.
    """

    CLOSE_DELAY = 30  # seconds until auto-close after opening

    def at_object_creation(self):
        super().at_object_creation()
        self.db.is_open = False
        self.db.gate_name = "gate"
        self.db.pair = None

    def at_traverse(self, traversing_object, source_location, **kwargs):
        if not self.db.is_open:
            traversing_object.msg(
                f"|yThe {self.db.gate_name} is closed.|n "
                f"(Type '|wopen {self.db.gate_name}|n' to open it.)"
            )
            return False
        return super().at_traverse(traversing_object, source_location, **kwargs)

    def open_gate(self, opener=None):
        """Open this gate and its pair. Schedule auto-close if CLOSE_DELAY > 0."""
        self.db.is_open = True
        msg = f"|yThe {self.db.gate_name} swings open.|n"
        if self.location:
            self.location.msg_contents(msg)
        if self.db.pair and not self.db.pair.db.is_open:
            self.db.pair.db.is_open = True
            if self.db.pair.location and self.db.pair.location != self.location:
                self.db.pair.location.msg_contents(msg)
        if self.CLOSE_DELAY > 0:
            delay(self.CLOSE_DELAY, self._auto_close)

    def _auto_close(self):
        """Called by delay() to close the gate after the timer expires."""
        self.close_gate()

    def close_gate(self, closer=None):
        """Close this gate and its pair."""
        already_closed = not self.db.is_open
        pair_already_closed = not (self.db.pair and self.db.pair.db.is_open)
        if already_closed and pair_already_closed:
            return

        msg = f"|yThe {self.db.gate_name} swings shut.|n"
        self.db.is_open = False
        if self.location:
            self.location.msg_contents(msg)
        if self.db.pair and self.db.pair.db.is_open:
            self.db.pair.db.is_open = False
            if self.db.pair.location and self.db.pair.location != self.location:
                self.db.pair.location.msg_contents(msg)


class AwtownCityGate(AwtownGate):
    """
    Main city gate (Grand Gate / Warden's Gate).

    Starts open (daytime default). Does not auto-close on a timer — managed
    by NPC guard schedule in Phase 4.
    """

    CLOSE_DELAY = 0  # disable auto-close

    def at_object_creation(self):
        super().at_object_creation()
        self.db.is_open = True
        self.db.gate_name = "city gate"

    def open_gate(self, opener=None):
        """Open without scheduling any auto-close."""
        self.db.is_open = True
        if self.db.pair:
            self.db.pair.db.is_open = True
        msg = f"|yThe {self.db.gate_name} swings open.|n"
        if self.location:
            self.location.msg_contents(msg)

    def _auto_close(self):
        pass  # city gates do not auto-close
