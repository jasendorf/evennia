"""
Command sets for DorfinMUD.

All custom commands are wired in here. Import order matches execution
dependency — if a command depends on a typeclass, that typeclass must
already exist before the server starts.

Phase completion status:
    Phase 1  -- Typeclasses (rooms, exits, npcs)         COMPLETE
    Phase 2  -- Batch script (103 rooms, all NPCs)       COMPLETE
    Phase 3  -- Dialogue, shops, founder buffs, kit      COMPLETE
    Phase 4  -- Character, items, needs, equipment       COMPLETE
    Phase 5  -- Combat (attack, flee, XP, loot)          COMPLETE
    Phase 6  -- Quests                                   PENDING
"""

from evennia import default_cmds

# Clothing contrib -- adds: wear, remove, cover, uncover, inventory (override)
try:
    from evennia.contrib.game_systems.clothing.clothing import ClothedCharacterCmdSet
    _HAS_CLOTHING = True
except ImportError:
    _HAS_CLOTHING = False

# Phase 3 commands
from commands.command_test import CmdTest
from commands.command_gates import CmdOpenGate, CmdCloseGate
from commands.command_say import CmdDorfinSay, CmdAsk
from commands.command_shop import CmdList, CmdBuy, CmdSell
from commands.command_founder import CmdBuff, CmdBuffs
from commands.command_kit import CmdClaimKit

# Phase 4 commands
from commands.command_equip import CmdWield, CmdUnwield, CmdEq
from commands.command_eat import CmdEat, CmdDrink
from commands.command_rent import CmdRentRoom

# Phase 5 commands
from commands.command_combat import (
    CmdKill, CmdFlee, CmdConsider, CmdWimpy, CmdRest, CmdScore,
)
from commands.command_admin_combat import (
    CmdTrainingRoom, CmdSpawnMob, CmdStopCombat, CmdCombatDebug, CmdFixCombat,
)


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    Commands available to all in-game characters at all times.
    Merged with AccountCmdSet when an Account puppets a Character.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()

        # Clothing contrib cmdset (wear, remove, cover, uncover)
        if _HAS_CLOTHING:
            self.add(ClothedCharacterCmdSet)

        # --- Gates ---
        self.add(CmdOpenGate())
        self.add(CmdCloseGate())

        # --- Communication ---
        self.add(CmdDorfinSay())       # overrides default say; triggers NPC dialogue
        self.add(CmdAsk())             # ask <npc> about <topic>

        # --- Shopping ---
        self.add(CmdList())            # list wares
        self.add(CmdBuy())             # buy <item>
        self.add(CmdSell())            # sell <item>

        # --- Founder buffs ---
        self.add(CmdBuff())            # buff / blessing (at Founder NPC)
        self.add(CmdBuffs())           # buffs / mybuffs

        # --- Starter kit ---
        self.add(CmdClaimKit())        # claim (at Outfitter's Rest)

        # --- Equipment ---
        self.add(CmdWield())           # wield <weapon>
        self.add(CmdUnwield())         # unwield [slot]
        self.add(CmdEq())              # eq / equipment

        # --- Eat & Drink ---
        self.add(CmdEat())             # eat <food>
        self.add(CmdDrink())           # drink <item>

        # --- Rest ---
        self.add(CmdRentRoom())        # rent room (at Inn Counter)

        # --- Combat (Phase 5) ---
        self.add(CmdKill())            # kill / attack / k <target>
        self.add(CmdFlee())            # flee / retreat / run
        self.add(CmdConsider())        # consider / con <target>
        self.add(CmdWimpy())           # wimpy <hp>
        self.add(CmdRest())            # rest / recover
        self.add(CmdScore())           # score / stats / sc

        # --- Admin: Combat (Phase 5) ---
        self.add(CmdTrainingRoom())    # @trainingroom
        self.add(CmdSpawnMob())        # @spawnmob [name]
        self.add(CmdStopCombat())      # @stopcombat
        self.add(CmdCombatDebug())     # @combatdebug / @cdebug
        self.add(CmdFixCombat())       # @fixcombat (global cleanup)

        # --- Testing ---
        self.add(CmdTest())


class AccountCmdSet(default_cmds.AccountCmdSet):
    """
    Commands available to the Account at all times, combined with
    CharacterCmdSet when puppeting a Character.
    """

    key = "DefaultAccount"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    """
    Commands available before logging in — create account, login, etc.
    """

    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()


class SessionCmdSet(default_cmds.SessionCmdSet):
    """
    Session-level commands, available once logged in.
    """

    key = "DefaultSession"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
