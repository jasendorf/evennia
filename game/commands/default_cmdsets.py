"""
Command sets for DorfinMUD.
"""

from evennia import default_cmds
from commands.command_test import CmdTest
from commands.command_gates import CmdOpenGate, CmdCloseGate
from commands.command_say import CmdDorfinSay, CmdAsk
from commands.command_shop import CmdList, CmdBuy, CmdSell
from commands.command_founder import CmdBuff, CmdBuffs
from commands.command_kit import CmdClaimKit


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdTest())
        self.add(CmdOpenGate())
        self.add(CmdCloseGate())
        self.add(CmdDorfinSay())
        self.add(CmdAsk())
        self.add(CmdList())
        self.add(CmdBuy())
        self.add(CmdSell())
        self.add(CmdBuff())
        self.add(CmdBuffs())
        self.add(CmdClaimKit())


class AccountCmdSet(default_cmds.AccountCmdSet):
    key = "DefaultAccount"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()


class SessionCmdSet(default_cmds.SessionCmdSet):
    key = "DefaultSession"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
