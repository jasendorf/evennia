"""
DorfinMUD — Custom Room Typeclass
===================================
All rooms in the game should use this typeclass (or a subclass of it).
It establishes the base attribute set that systems like shops, day/night,
combat, crafting, and weather will read from.

Room types (db.room_type):
    "road"       — outdoor street/path segment
    "gate"       — entry/exit point between areas
    "exterior"   — outdoor open area (commons, stables, garden)
    "courtyard"  — open-air but enclosed (Crystal Repository)
    "building"   — generic interior
    "inn"        — Hearthstone Inn rooms
    "temple"     — Temple of the Eternal Flame rooms
    "crafting"   — Grand Forge / Tinker's Den / Alchemist's Corner
    "training"   — Apprentice Hall / Study Hall
    "lookout"    — Watchtower / The Precipice
    "founder"    — Founders' offices (Malgrave, Hammerfall, Oldmere)
"""

from evennia import DefaultRoom


class Room(DefaultRoom):
    """
    Base room for all DorfinMUD locations.

    Attributes set at creation (all overridable in batch script):

    Identification
        zone        (str)   — area name, e.g. "awtown", "wilds"
        room_type   (str)   — category string (see module docstring)

    Environment
        is_outdoor  (bool)  — exposed to weather / sky
        is_safe     (bool)  — no PvP, no hostile mob spawns
        light_level (int)   — 0 (pitch black) to 5 (full daylight)
        desc_night  (str)   — alternate description shown at night
                              (empty string = use default desc always)

    Services
        shop_npc    (int)   — dbref# of the NPC running a shop here, or None
        trainer_npc (int)   — dbref# of a class/skill trainer here, or None
        rest_bonus  (int)   — HP/MP recovery rate multiplier (0 = no bonus)
                              1 = minor (washhouse), 2 = normal (inn room),
                              3 = premium (future: private room)

    Gameplay
        no_teleport (bool)  — block teleport in/out (locked rooms, etc.)
        encounter_table (str) — name of the encounter table to use,
                                or None for no random encounters

    Flavor
        ambient     (list)  — list of ambient message strings shown randomly
                              to players in the room (empty = none)
    """

    def at_object_creation(self):
        """Called once when the room is first created."""
        super().at_object_creation()

        # --- Identification ---
        self.db.zone = "unset"
        self.db.room_type = "building"

        # --- Environment ---
        self.db.is_outdoor = False
        self.db.is_safe = True
        self.db.light_level = 4          # well-lit interior default
        self.db.desc_night = ""          # empty = no alternate night desc

        # --- Services ---
        self.db.shop_npc = None
        self.db.trainer_npc = None
        self.db.rest_bonus = 0

        # --- Gameplay ---
        self.db.no_teleport = False
        self.db.encounter_table = None

        # --- Flavor ---
        self.db.ambient = []

    def get_display_desc(self, looker, **kwargs):
        """
        Return the room description. If it is 'night' in the game world
        and desc_night is set, return that instead of the default desc.

        The day/night system will set a server-level flag when implemented.
        For now this just returns the default desc.
        """
        # Future hook: check global day/night flag here
        # from world.time_system import is_night
        # if is_night() and self.db.desc_night:
        #     return self.db.desc_night
        return super().get_display_desc(looker, **kwargs)

    def at_object_receive(self, moved_obj, source_location, move_type="move", **kwargs):
        """
        Called when something arrives in this room.
        Hook point for: encounter triggers, ambient greetings, zone entry
        messages, etc.
        """
        super().at_object_receive(moved_obj, source_location,
                                  move_type=move_type, **kwargs)
        # Future: trigger ambient NPC greetings, zone transition messages, etc.

    def at_object_leave(self, moved_obj, target_location, move_type="move", **kwargs):
        """
        Called when something leaves this room.
        Hook point for: encounter checks on exit, guild tracking, etc.
        """
        super().at_object_leave(moved_obj, target_location,
                                move_type=move_type, **kwargs)


# ---------------------------------------------------------------------------
# Specialised subclasses
# ---------------------------------------------------------------------------

class OutdoorRoom(Room):
    """
    Convenience subclass for outdoor rooms.
    Sets is_outdoor=True and light_level=5 by default.
    Used for: roads, exterior areas, gates, courtyards.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.is_outdoor = True
        self.db.light_level = 5          # full daylight outdoors


class RoadRoom(OutdoorRoom):
    """
    A named road segment. Outdoor, safe, no services.
    Used for: Founder's Walk, Market Row, Craftsman's Road, etc.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.room_type = "road"


class GateRoom(OutdoorRoom):
    """
    A gate or entry point. Outdoor, safe.
    Guards typically present; may be flagged no_teleport in future.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.room_type = "gate"


class ExteriorRoom(OutdoorRoom):
    """
    An open exterior area: commons, stables, gardens.
    Outdoor, generally safe. May have encounter tables in wilds.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.room_type = "exterior"


class CourtyardRoom(OutdoorRoom):
    """
    Open-air but enclosed: Crystal Repository, etc.
    Outdoor for weather purposes, but sheltered feel.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.room_type = "courtyard"
        self.db.light_level = 4          # slightly sheltered


class InnRoom(Room):
    """
    Hearthstone Inn rooms. Rest bonus active.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.room_type = "inn"
        self.db.rest_bonus = 2


class TempleRoom(Room):
    """
    Temple of the Eternal Flame rooms. Safe, minor rest bonus.
    Future: healing modifier, resurrection anchor point.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.room_type = "temple"
        self.db.rest_bonus = 1


class CraftingRoom(Room):
    """
    Forge / workshop rooms. Safe, crafting stations present.
    Future: crafting_stations list attribute.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.room_type = "crafting"
        self.db.crafting_stations = []   # populated when workstations are built


class TrainingRoom(Room):
    """
    Apprentice Hall, Study Hall. Safe, training-specific.
    Future: available_skills list, training cost modifier.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.room_type = "training"


class FounderRoom(Room):
    """
    Founder offices. Safe. Buff-granting NPCs present.
    Future: buff_npc reference, cooldown tracking.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.room_type = "founder"


class LookoutRoom(OutdoorRoom):
    """
    High vantage points: Watchtower, The Precipice.
    Outdoor. Future: reveals map areas, trigger scouting skill checks.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.room_type = "lookout"
