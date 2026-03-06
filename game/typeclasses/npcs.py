"""
Awtown NPC typeclass.

AwtownNPC extends DefaultCharacter so NPCs render in the "Characters" section
of room descriptions (same as players). NPCs have no account and cannot be
logged into. Their cmdsets are cleared at creation — interaction is handled
via the dialogue system added in Phase 3.
"""

from evennia.objects.objects import DefaultCharacter


class AwtownNPC(DefaultCharacter):
    """
    Base typeclass for all Awtown NPCs.

    db Attributes:
        is_npc         (bool) : Always True. Lets systems distinguish NPCs from players.
        npc_role       (str)  : Role hint for future systems.
                                One of: "generic", "merchant", "trainer", "guard",
                                "quest_giver", "banker", "innkeeper", "founder".
        dialogue       (dict) : Keyword (lowercase str) → response (str) mapping.
                                Populated in batch_awtown.py; wired in Phase 3.
        shop_inventory (list) : Prototype keys for the shop system (Phase 3).
        quest_keys     (list) : Quest identifiers (Phase 4).

    Example dialogue dict:
        {
            "hello":  "Welcome, traveller. Awtown's gates are open to all.",
            "jobs":   "I've got deliveries piling up — speak to the Steward.",
            "quest":  "Ask me about 'deliveries' for work.",
        }
    """

    def at_object_creation(self):
        super().at_object_creation()

        # Clear the default character cmdset — NPCs don't use player commands.
        # The dialogue system (Phase 3) hooks in via at_msg_receive / scripts.
        self.cmdset.clear()

        self.db.is_npc = True
        self.db.npc_role = "generic"
        self.db.dialogue = {}
        self.db.shop_inventory = []
        self.db.quest_keys = []

    def get_display_name(self, looker, **kwargs):
        """NPCs render their name in cyan to distinguish them from players."""
        return f"|c{self.name}|n"

    def at_msg_receive(self, text=None, from_obj=None, **kwargs):
        """
        Placeholder for Phase 3 dialogue system.
        NPCs will react to 'say' commands via this hook.
        """
        return super().at_msg_receive(text=text, from_obj=from_obj, **kwargs)


# Evennia requires a class named 'Character' in typeclasses.characters.
# npcs.py is not the default characters module, but we alias here for safety.
Character = AwtownNPC
