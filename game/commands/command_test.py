"""
Test command - verifies the workflow is working
"""

from evennia.commands.default.mixin_admin import MixinAdminCommand


class CmdTest(MixinAdminCommand):
    """Test command to verify the Awtown workflow"""
    
    key = "test"
    aliases = ["@test"]
    help_category = "Testing"
    locks = "cmd:all()"

    def func(self):
        """Execute the test command"""
        self.caller.msg("|g✓ The test workflow is working!|n")
        self.caller.msg("|cAwtown deployment pipeline verified.|n")
