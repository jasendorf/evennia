"""
Awtown Room typeclasses.

Hierarchy:
    AwtownRoom          — base for all Awtown rooms (safe, building by default)
    AwtownRoadRoom      — road segments (outdoor)
    AwtownCourtyardRoom — teal courtyards (outdoor)
    AwtownExteriorRoom  — /4 exterior sets: stables, commons, garden (outdoor)
"""

from evennia.objects.objects import DefaultRoom


class AwtownRoom(DefaultRoom):
    """
    Base room typeclass for all rooms in Awtown.

    db Attributes:
        is_safe   (bool) : No PvP, no aggressive mobs. Default True.
        room_type (str)  : Category hint — "building", "road", "courtyard", "exterior".
        is_outdoor(bool) : Whether weather/time messages apply. Default False.
        desc_day  (str)  : Optional description override during game daytime (hours 6-19).
        desc_night(str)  : Optional description override during game night (hours 20-5).

    If desc_day / desc_night are empty strings, the standard db.desc is always used.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.is_safe = True
        self.db.room_type = "building"
        self.db.is_outdoor = False
        self.db.desc_day = ""
        self.db.desc_night = ""

    def return_appearance(self, looker, **kwargs):
        """
        Injects day/night description when one is set.
        Falls back to db.desc when no time-specific override is defined.
        """
        desc_day = self.db.desc_day or ""
        desc_night = self.db.desc_night or ""

        if desc_day or desc_night:
            try:
                from evennia.utils import gametime
                secs = int(gametime.gametime())
                # Treat a full game-day as 86400 real seconds for now.
                # Phase 4 will introduce a proper game-clock multiplier.
                hour = (secs % 86400) // 3600
                is_day = 6 <= hour < 20
            except Exception:
                is_day = True

            original = self.db.desc
            if is_day and desc_day:
                self.db.desc = desc_day
            elif not is_day and desc_night:
                self.db.desc = desc_night

            result = super().return_appearance(looker, **kwargs)
            self.db.desc = original
            return result

        return super().return_appearance(looker, **kwargs)


class AwtownRoadRoom(AwtownRoom):
    """A road segment. Always outdoor, always safe."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.room_type = "road"
        self.db.is_outdoor = True


class AwtownCourtyardRoom(AwtownRoom):
    """An open courtyard (teal rooms on the map). Outdoor, safe."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.room_type = "courtyard"
        self.db.is_outdoor = True


class AwtownExteriorRoom(AwtownRoom):
    """
    Exterior /4 room sets: Dusty Paddock, Eastern Commons, Garden of Remembrance.
    Outdoor, safe. The Garden receives night-specific descs for undead events (Phase 4).
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.room_type = "exterior"
        self.db.is_outdoor = True


# Evennia requires a class named 'Room' to exist in typeclasses.rooms.
# We alias it to AwtownRoom so the default typeclass lookup works.
Room = AwtownRoom
