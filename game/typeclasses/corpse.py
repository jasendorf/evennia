"""
DorfinMUD Corpse Typeclass
===========================

A temporary container object that holds loot from a defeated mob.
Players can retrieve items from a corpse using standard Evennia
get/take commands:

    get dagger from corpse
    get all from corpse

The corpse automatically deletes itself after DECAY_TIME seconds.
Any items still inside the corpse when it decays are deleted with it.

The corpse uses a lightweight Evennia Script for the decay timer rather
than evennia.utils.delay, so that the timer survives server reloads.

Creating a corpse
-----------------

Normally created by AwtownMob.at_defeat(), but can be created manually:

    from evennia import create_object
    from typeclasses.corpse import Corpse

    corpse = create_object(Corpse, key="the corpse of a goblin", location=room)
    corpse.db.desc = "The remains of a goblin."

    # Put loot inside
    sword.move_to(corpse, quiet=True)
"""

from evennia.objects.objects import DefaultObject
from evennia import DefaultScript


# How long a corpse lasts before decaying (in seconds)
DECAY_TIME = 120


class CorpseDecayScript(DefaultScript):
    """
    Persistent timer script that deletes a corpse after it expires.

    Attached to the corpse object on creation. Fires once after
    DECAY_TIME seconds.
    """

    def at_script_creation(self):
        self.key = "CorpseDecayScript"
        self.desc = "Corpse decay timer."
        self.interval = DECAY_TIME
        self.repeats = 1           # fire once
        self.persistent = True     # survive reloads
        self.start_delay = True    # don't fire immediately

    def at_repeat(self):
        """Called when the timer fires. Decay the corpse."""
        corpse = self.obj
        if corpse:
            corpse.at_decay()

    def at_stop(self):
        """
        Called when the script stops (either from decay or manual removal).
        """
        pass


class Corpse(DefaultObject):
    """
    A temporary container holding loot from a defeated mob.

    Players can get items from a corpse the same way they get items
    from any container. The corpse decays after DECAY_TIME seconds.

    db Attributes:
        desc      (str) : Description of the corpse.
        mob_key   (str) : Key of the mob that died (for flavor text).
        mob_level (int) : Level of the mob that died (for flavor text).
    """

    # Allow objects to be placed inside this object
    # (Evennia uses location-based containment — items inside a corpse
    #  have their location set to the corpse object)

    def at_object_creation(self):
        super().at_object_creation()

        self.db.desc = "The remains of a fallen creature."
        self.db.mob_key = "something"
        self.db.mob_level = 1

        # Lock: anyone can get items from the corpse, but not pick up
        # the corpse itself
        self.locks.add("get:false()")
        self.locks.add("get_from:true()")

        # Start the decay timer
        self.scripts.add(CorpseDecayScript)

    def at_decay(self):
        """
        Called when the corpse's decay timer expires.

        Announces the decay, deletes any remaining contents, then
        deletes itself.
        """
        location = self.location

        # Check if there are items still inside
        contents = [obj for obj in self.contents if obj != self]

        if location:
            if contents:
                item_names = ", ".join(obj.key for obj in contents[:5])
                suffix = "..." if len(contents) > 5 else ""
                location.msg_contents(
                    f"|x{self.key} crumbles to dust. "
                    f"Its remaining contents ({item_names}{suffix}) are lost.|n"
                )
            else:
                location.msg_contents(
                    f"|x{self.key} crumbles to dust and is gone.|n"
                )

        # Delete contents
        for obj in contents:
            obj.delete()

        # Delete self
        self.delete()

    def get_display_name(self, looker, **kwargs):
        """Corpses display in dark gray."""
        return f"|x{self.key}|n"

    def return_appearance(self, looker, **kwargs):
        """Show corpse description and list contents."""
        desc = self.db.desc or "The remains of a fallen creature."
        lines = [f"|x{self.key}|n", desc]

        contents = [obj for obj in self.contents if obj != self]
        if contents:
            lines.append("\n|wYou see:|n")
            for obj in contents:
                name = obj.get_display_name(looker) if hasattr(obj, "get_display_name") else obj.key
                lines.append(f"  {name}")
            lines.append(
                "\nType |wget <item> from corpse|n to take something."
            )
        else:
            lines.append("\n|xThe corpse is empty.|n")

        return "\n".join(lines)

    def at_pre_get(self, getter, **kwargs):
        """
        Called when someone tries to pick up the corpse itself.
        Corpses are too heavy / unpleasant to carry around.
        """
        getter.msg("You can't pick that up. Try |wget <item> from corpse|n instead.")
        return False
