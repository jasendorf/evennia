"""
DorfinMUD Needs Extension
=========================

Extends the generic needs system (contrib_dorfin/needs.py) with DorfinMUD-
specific hunger and thirst mechanics.

This is the game-specific layer. The contrib layer (needs.py) contains
no references to stats, message strings, or game content.

---

HUNGER
------

Decays at 5 points per tick (default tick = 1 real hour).

  100–51  Well-fed. No effect.
  50–26   Hungry. Minor flavour message; no mechanical penalty yet.
  25–1    Very hungry. Stat penalties: STR -3, CON -2, END -3.
  0       Starving. Severe penalties: STR -6, CON -4, END -6, AGI -2.
          Repeated damage-over-time messages.

---

THIRST
------

Decays at 7 points per tick (thirst sets in faster than hunger).

  100–51  Hydrated. No effect.
  50–26   Thirsty. Flavour message; no penalty.
  25–1    Very thirsty. Penalties: DEX -2, PER -2, INT -3.
  0       Dehydrated. Severe: DEX -4, PER -4, INT -5, WIS -2.

---

INSTALLATION
------------

Have your Character typeclass inherit from DorfinNeedsMixin instead of
(or after) NeedsCharacterMixin:

    from contrib_dorfin.dorfin_needs import DorfinNeedsMixin

    class AwtownCharacter(DorfinNeedsMixin, ClothedCharacter):

        def at_object_creation(self):
            super().at_object_creation()
            # DorfinNeedsMixin.at_object_creation registers hunger+thirst
            # and starts the script automatically.

        def _register_need_callbacks(self):
            super()._register_need_callbacks()
            # Callbacks are re-registered here after reload.

---

REMOVING PENALTIES
------------------

Penalty buffs are keyed by buff key. When a need is restored above a
threshold, call remove_need_penalties(name, threshold) to remove the
associated buff. This is handled automatically by the eat/drink commands
via the _on_*_restored callbacks.

"""

from contrib_dorfin.needs import NeedsCharacterMixin, BaseNeedsBuff

try:
    from evennia.contrib.rpg.buffs import Mod
    _BUFFS_AVAILABLE = True
except ImportError:
    _BUFFS_AVAILABLE = False
    Mod = None


# ---------------------------------------------------------------------------
# Hunger penalty buffs
# ---------------------------------------------------------------------------

if _BUFFS_AVAILABLE:
    class HungerModerateBuff(BaseNeedsBuff):
        """
        No stat penalty — just messaging. Applied at hunger <= 50.
        Duration is permanent until hunger is restored above 50.
        """
        key = "hunger_moderate"
        name = "Hungry"
        flavor = "Your stomach growls quietly."
        need_name = "hunger"
        duration = -1
        mods = []

    class HungerLowBuff(BaseNeedsBuff):
        """
        Moderate stat penalties. Applied at hunger <= 25.
        Stacks on top of HungerModerateBuff.
        """
        key = "hunger_low"
        name = "Very Hungry"
        flavor = "Hunger gnaws at you. Your strength is flagging."
        need_name = "hunger"
        duration = -1
        mods = [
            Mod("str", "add", -3),
            Mod("con", "add", -2),
            Mod("end", "add", -3),
        ]

    class HungerCriticalBuff(BaseNeedsBuff):
        """
        Severe stat penalties. Applied at hunger == 0 (starving).
        """
        key = "hunger_critical"
        name = "Starving"
        flavor = "You are starving. Your body is consuming itself."
        need_name = "hunger"
        duration = -1
        mods = [
            Mod("str", "add", -6),
            Mod("con", "add", -4),
            Mod("end", "add", -6),
            Mod("agi", "add", -2),
        ]

    # ------------------------------------------------------------------

    class ThirstModerateBuff(BaseNeedsBuff):
        """No penalty — messaging only. Applied at thirst <= 50."""
        key = "thirst_moderate"
        name = "Thirsty"
        flavor = "Your throat feels dry."
        need_name = "thirst"
        duration = -1
        mods = []

    class ThirstLowBuff(BaseNeedsBuff):
        """Moderate penalties. Applied at thirst <= 25."""
        key = "thirst_low"
        name = "Very Thirsty"
        flavor = "Your lips are cracked. Concentration slips."
        need_name = "thirst"
        duration = -1
        mods = [
            Mod("dex", "add", -2),
            Mod("per", "add", -2),
            Mod("int", "add", -3),
        ]

    class ThirstCriticalBuff(BaseNeedsBuff):
        """Severe penalties. Applied at thirst == 0 (dehydrated)."""
        key = "thirst_critical"
        name = "Dehydrated"
        flavor = "You are dangerously dehydrated. Your vision swims."
        need_name = "thirst"
        duration = -1
        mods = [
            Mod("dex", "add", -4),
            Mod("per", "add", -4),
            Mod("int", "add", -5),
            Mod("wis", "add", -2),
        ]

else:
    # Stub classes when Buffs contrib is not installed.
    # Needs still decay and messages still fire — just no stat penalties.
    class HungerModerateBuff: pass
    class HungerLowBuff: pass
    class HungerCriticalBuff: pass
    class ThirstModerateBuff: pass
    class ThirstLowBuff: pass
    class ThirstCriticalBuff: pass


# ---------------------------------------------------------------------------
# Threshold → buff key map (used for cleanup on restore)
# ---------------------------------------------------------------------------

HUNGER_THRESHOLD_BUFFS = {
    50: "hunger_moderate",
    25: "hunger_low",
    0:  "hunger_critical",
}

THIRST_THRESHOLD_BUFFS = {
    50: "thirst_moderate",
    25: "thirst_low",
    0:  "thirst_critical",
}

HUNGER_BUFF_CLASSES = {
    50: HungerModerateBuff,
    25: HungerLowBuff,
    0:  HungerCriticalBuff,
}

THIRST_BUFF_CLASSES = {
    50: ThirstModerateBuff,
    25: ThirstLowBuff,
    0:  ThirstCriticalBuff,
}


# ---------------------------------------------------------------------------
# Threshold messages (fired before buff is applied)
# ---------------------------------------------------------------------------

HUNGER_MESSAGES = {
    50: "Your stomach growls quietly.",
    25: "|yYou are hungry. Your strength is beginning to flag.|n",
    0:  "|rYou are starving. Your body is failing you.|n",
}

THIRST_MESSAGES = {
    50: "Your throat feels dry.",
    25: "|yYou are thirsty. Your lips are cracking.|n",
    0:  "|rYou are dangerously dehydrated. Your vision swims.|n",
}


# ---------------------------------------------------------------------------
# DorfinNeedsMixin
# ---------------------------------------------------------------------------

class DorfinNeedsMixin(NeedsCharacterMixin):
    """
    DorfinMUD extension of NeedsCharacterMixin.

    Registers hunger and thirst with appropriate decay rates, threshold
    messages, and stat penalty buffs.

    Place before ClothedCharacter (or DefaultCharacter) in the MRO:

        class AwtownCharacter(DorfinNeedsMixin, ClothedCharacter):
            ...
    """

    def at_object_creation(self):
        """Register hunger and thirst, then start the script."""
        super().at_object_creation()

        self.needs.add(
            "hunger",
            decay_rate=5,
            initial_value=100,
            thresholds=[
                (50, self._on_hunger_moderate),
                (25, self._on_hunger_low),
                (0,  self._on_hunger_critical),
            ],
        )
        self.needs.add(
            "thirst",
            decay_rate=7,
            initial_value=100,
            thresholds=[
                (50, self._on_thirst_moderate),
                (25, self._on_thirst_low),
                (0,  self._on_thirst_critical),
            ],
        )

        self.needs.start_script()

    def _register_need_callbacks(self):
        """Re-register callbacks after a server reload."""
        super()._register_need_callbacks()

        self.needs.register_callbacks("hunger", [
            (50, self._on_hunger_moderate),
            (25, self._on_hunger_low),
            (0,  self._on_hunger_critical),
        ])
        self.needs.register_callbacks("thirst", [
            (50, self._on_thirst_moderate),
            (25, self._on_thirst_low),
            (0,  self._on_thirst_critical),
        ])

    # ------------------------------------------------------------------
    # Hunger callbacks
    # ------------------------------------------------------------------

    def _on_hunger_moderate(self, character, need_name, value):
        """Hunger dropped to/below 50. Message only, no penalty buff yet."""
        character.msg(HUNGER_MESSAGES[50])
        if _BUFFS_AVAILABLE and hasattr(character, "buffs"):
            if not character.buffs.get("hunger_moderate"):
                character.buffs.add(HungerModerateBuff)

    def _on_hunger_low(self, character, need_name, value):
        """Hunger dropped to/below 25. Apply low penalty buff."""
        character.msg(HUNGER_MESSAGES[25])
        if _BUFFS_AVAILABLE and hasattr(character, "buffs"):
            if not character.buffs.get("hunger_low"):
                character.buffs.add(HungerLowBuff)

    def _on_hunger_critical(self, character, need_name, value):
        """Hunger hit 0. Apply critical penalty buff."""
        character.msg(HUNGER_MESSAGES[0])
        if _BUFFS_AVAILABLE and hasattr(character, "buffs"):
            if not character.buffs.get("hunger_critical"):
                character.buffs.add(HungerCriticalBuff)

    # ------------------------------------------------------------------
    # Thirst callbacks
    # ------------------------------------------------------------------

    def _on_thirst_moderate(self, character, need_name, value):
        """Thirst dropped to/below 50. Message only."""
        character.msg(THIRST_MESSAGES[50])
        if _BUFFS_AVAILABLE and hasattr(character, "buffs"):
            if not character.buffs.get("thirst_moderate"):
                character.buffs.add(ThirstModerateBuff)

    def _on_thirst_low(self, character, need_name, value):
        """Thirst dropped to/below 25. Apply low penalty buff."""
        character.msg(THIRST_MESSAGES[25])
        if _BUFFS_AVAILABLE and hasattr(character, "buffs"):
            if not character.buffs.get("thirst_low"):
                character.buffs.add(ThirstLowBuff)

    def _on_thirst_critical(self, character, need_name, value):
        """Thirst hit 0. Apply critical penalty buff."""
        character.msg(THIRST_MESSAGES[0])
        if _BUFFS_AVAILABLE and hasattr(character, "buffs"):
            if not character.buffs.get("thirst_critical"):
                character.buffs.add(ThirstCriticalBuff)

    # ------------------------------------------------------------------
    # Restore helpers (called by eat/drink commands)
    # ------------------------------------------------------------------

    def restore_hunger(self, amount):
        """
        Restore hunger by amount. Clears any penalty buffs for thresholds
        we've risen above.

        Args:
            amount (int): How much hunger to restore (added to current value).

        Returns:
            int: New hunger value.
        """
        new_value = self.needs.restore("hunger", amount)
        if new_value is None:
            return None

        if _BUFFS_AVAILABLE and hasattr(self, "buffs"):
            for threshold, buff_key in HUNGER_THRESHOLD_BUFFS.items():
                if new_value > threshold:
                    existing = self.buffs.get(buff_key)
                    if existing:
                        self.buffs.remove(buff_key)

        return new_value

    def restore_thirst(self, amount):
        """
        Restore thirst by amount. Clears penalty buffs we've risen above.

        Args:
            amount (int): How much thirst to restore.

        Returns:
            int: New thirst value.
        """
        new_value = self.needs.restore("thirst", amount)
        if new_value is None:
            return None

        if _BUFFS_AVAILABLE and hasattr(self, "buffs"):
            for threshold, buff_key in THIRST_THRESHOLD_BUFFS.items():
                if new_value > threshold:
                    existing = self.buffs.get(buff_key)
                    if existing:
                        self.buffs.remove(buff_key)

        return new_value
