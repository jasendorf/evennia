"""
Awtown NPC typeclass.
"""

from evennia.objects.objects import DefaultCharacter


class AwtownNPC(DefaultCharacter):
    """
    Base typeclass for all Awtown NPCs.

    db Attributes:
        is_npc         (bool)
        npc_role       (str)  : "generic" | "merchant" | "trainer" | "guard" |
                                "quest_giver" | "banker" | "innkeeper" | "founder"
        dialogue       (dict) : lowercase keyword -> response string
        shop_inventory (list) : list of dicts: {key, name, price, desc}
        quest_keys     (list) : quest identifiers (Phase 6)
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.cmdset.clear()
        self.db.is_npc = True
        self.db.npc_role = "generic"
        self.db.dialogue = {}
        self.db.shop_inventory = []
        self.db.quest_keys = []

    def get_display_name(self, looker, **kwargs):
        return f"|c{self.name}|n"

    def hear_say(self, speaker, message):
        """
        Called when someone speaks in the same room.
        Checks db.dialogue for keyword matches and responds.
        Matches on whole words; first match wins.

        Returns True if a match was found and a response sent, else False.
        This allows callers to stop after the first responding NPC.
        """
        dialogue = self.db.dialogue or {}
        if not dialogue:
            return False

        msg_lower = message.lower()
        for keyword, response in dialogue.items():
            if keyword in msg_lower:
                self.location.msg_contents(
                    f"|c{self.name}|n says, \"|w{response}|n\""
                )
                return True

        return False


# Evennia alias
Character = AwtownNPC
