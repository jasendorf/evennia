"""
Account

The Account represents the game "account" and each login has only one
temporary Account object. What a given Account can do is controlled by
its available cmdsets.
"""

from evennia.utils.evmenu import EvMenu

try:
    from evennia.contrib.rpg.character_creator.character_creator import ContribChargenAccount
    _HAS_CHARGEN = True
except ImportError:
    from evennia.accounts.accounts import DefaultAccount as ContribChargenAccount
    _HAS_CHARGEN = False

_BASE_ACCOUNT = ContribChargenAccount


class Account(_BASE_ACCOUNT):
    """
    DorfinMUD Account typeclass.

    Inherits from ContribChargenAccount (character_creator contrib) which
    provides the ``charcreate`` command, in-progress character tracking via
    ``chargen_step``, and a modified OOC appearance template.

    Overrides ``at_post_login`` to show a custom EvMenu character-select
    screen instead of the default OOC look.
    """

    def at_post_login(self, session=None, **kwargs):
        """
        Called after authentication succeeds.

        Instead of the default behaviour (show OOC screen / auto-puppet),
        launch our custom login menu EvMenu.
        """
        # Minimal bookkeeping that DefaultAccount.at_post_login normally does:
        # announce to other sessions on this account, if any.
        nsess = len(self.sessions.all())
        if nsess > 1:
            self.msg(
                f"|ySession {nsess} connected.|n",
                session=session,
            )

        # Launch the login menu
        EvMenu(
            self,
            "world.login_menu",
            startnode="menunode_charselect",
            session=session,
            cmd_on_exit=None,
            persistent=True,
        )
