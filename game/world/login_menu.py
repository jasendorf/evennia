"""
DorfinMUD Login Menu — EvMenu Module
=====================================

Post-login character selection screen. Launched from
``Account.at_post_login()`` as an EvMenu on the Account.

Unlike the chargen menu (where caller = session), here the
caller is the **Account** object.

Important: side-effects like puppeting or launching the chargen EvMenu
must NOT happen inside goto callbacks (the login EvMenu is still active).
Instead, store the intended action on ``account.ndb._login_action`` and
return ``None`` — the ``on_login_menu_exit`` callback runs after the
EvMenu is fully torn down and executes the deferred action.
"""

import string
from random import choices

import evennia
from django.conf import settings
from evennia.objects.models import ObjectDB
from evennia.utils import dedent
from evennia.utils.evmenu import EvMenu

_MAX_NR_CHARACTERS = getattr(settings, "MAX_NR_CHARACTERS", 6) or 6

try:
    _CHARGEN_MENU = settings.CHARGEN_MENU
except AttributeError:
    _CHARGEN_MENU = "world.chargen"


def on_login_menu_exit(caller, menu):
    """
    Called after the login EvMenu is fully closed.

    Checks ``caller.ndb._login_action`` for a deferred action
    (puppet a character or launch chargen) and executes it.
    """
    account = caller
    action = account.ndb._login_action
    if not action:
        return
    account.ndb._login_action = None

    sess = action["session"]
    if not sess:
        return

    if action["type"] == "puppet":
        account.puppet_object(sess, action["character"])

    elif action["type"] == "chargen":
        new_char = action["character"]
        startnode = action["startnode"]
        sess.new_char = new_char

        def _finish_chargen(sess_obj, menu):
            char = sess_obj.new_char
            if char.db.chargen_step:
                account.msg(
                    account.at_look(target=account.characters.all(), session=sess_obj),
                    session=sess_obj,
                )
            else:
                try:
                    account.puppet_object(sess_obj, char)
                except RuntimeError:
                    account.msg("Could not enter the game.", session=sess_obj)

        EvMenu(
            sess,
            _CHARGEN_MENU,
            startnode=startnode,
            cmd_on_exit=_finish_chargen,
        )


def menunode_exit(caller, raw_string="", **kwargs):
    """
    Empty node — returning None as text tells EvMenu to shut down.
    The ``on_login_menu_exit`` callback then handles any deferred action.
    """
    return None, None


def menunode_charselect(caller, raw_string="", **kwargs):
    """
    Main character-select screen shown after login.

    ``caller`` is the Account.
    """
    account = caller
    characters = [c for c in account.characters.all() if c]
    complete_chars = [c for c in characters if not c.db.chargen_step]
    in_progress = [c for c in characters if c.db.chargen_step]
    total = len(characters)

    # Build character list
    char_lines = []
    for i, char in enumerate(characters, 1):
        if char.db.chargen_step:
            char_lines.append(f"    |w{i}|n. |y[IN PROGRESS]|n  (type |wcreate|n to continue)")
        else:
            # Build descriptors from available data
            parts = []
            level = char.db.level
            if level is not None:
                parts.append(f"Level {level}")
            if char.db.race_name:
                parts.append(char.db.race_name)
            if char.db.char_class_name:
                parts.append(char.db.char_class_name)
            desc = " ".join(parts) if parts else ""
            if desc:
                char_lines.append(f"    |w{i}|n. |G{char.key}|n ({desc})")
            else:
                char_lines.append(f"    |w{i}|n. |G{char.key}|n")

    if not characters:
        char_section = "    (no characters yet -- type |wcreate|n to make one!)"
    else:
        char_section = "\n".join(char_lines)

    if error := kwargs.get("error"):
        error_line = f"\n  |r{error}|n\n"
    else:
        error_line = ""

    text = (
        f"|w=====================================\n"
        f"  Welcome back, {account.key}!\n"
        f"  The Land of Dorfin awaits.\n"
        f"=====================================|n\n"
        f"\n"
        f"  |wYour characters:|n\n"
        f"{char_section}\n"
        f"\n"
        f"  Character slots: {total}/{_MAX_NR_CHARACTERS}\n"
        f"{error_line}"
        f"  |wCommands:|n\n"
        f"    |wplay <name or #>|n    -- enter the game\n"
        f"    |wcreate|n              -- create a new character\n"
        f"    |wwho|n                 -- see who's online\n"
        f"    |wquit|n                -- disconnect\n"
    )

    options = {"key": "_default", "goto": (_parse_input, {"session": kwargs.get("session")})}
    return text, options


def _parse_input(caller, raw_string, session=None, **kwargs):
    """Dispatch input from the character select menu."""
    account = caller
    cmd = raw_string.strip()

    if not cmd:
        return "menunode_charselect", {"session": session}

    parts = cmd.split(None, 1)
    action = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    characters = [c for c in account.characters.all() if c]

    # --- play ---
    if action in ("play", "p", "ic"):
        return _do_play(account, arg, characters, session)

    # Bare number = shortcut for play
    if action.isdigit():
        return _do_play(account, action, characters, session)

    # --- create ---
    if action in ("create", "cr", "new", "charcreate"):
        return _do_create(account, characters, session)

    # --- who ---
    if action == "who":
        return _do_who(caller, session)

    # --- quit ---
    if action in ("quit", "q", "logout"):
        return _do_quit(account, session)

    # --- delete (future) ---
    if action in ("delete", "del"):
        return "menunode_charselect", {
            "session": session,
            "error": "Character deletion is not yet available.",
        }

    return "menunode_charselect", {
        "session": session,
        "error": f"Unknown command: {action}",
    }


def _do_play(account, arg, characters, session):
    """Attempt to puppet a character."""
    if not characters:
        return "menunode_charselect", {
            "session": session,
            "error": "You have no characters. Type |wcreate|n to make one.",
        }

    if not arg:
        if len(characters) == 1:
            target = characters[0]
        else:
            return "menunode_charselect", {
                "session": session,
                "error": "Specify a character name or number.",
            }
    else:
        target = None
        # Try as number
        try:
            idx = int(arg) - 1
            if 0 <= idx < len(characters):
                target = characters[idx]
        except ValueError:
            pass

        # Try as name
        if not target:
            for c in characters:
                if c.key.lower() == arg.lower():
                    target = c
                    break

    if not target:
        return "menunode_charselect", {
            "session": session,
            "error": f"No character matching '{arg}' found.",
        }

    if target.db.chargen_step:
        return "menunode_charselect", {
            "session": session,
            "error": "That character is still in progress. Type |wcreate|n to continue.",
        }

    # Defer puppeting until the login EvMenu is fully closed
    sess = session or (account.sessions.get()[0] if account.sessions.get() else None)
    account.ndb._login_action = {
        "type": "puppet",
        "session": sess,
        "character": target,
    }
    return "menunode_exit"


def _do_create(account, characters, session):
    """Create a new character or resume an in-progress one, then launch chargen."""
    in_progress = [c for c in characters if c.db.chargen_step]
    sess = session or (account.sessions.get()[0] if account.sessions.get() else None)

    if not sess:
        return "menunode_charselect", {
            "session": session,
            "error": "No active session found.",
        }

    if in_progress:
        new_char = in_progress[0]
    else:
        if len(characters) >= _MAX_NR_CHARACTERS:
            return "menunode_charselect", {
                "session": session,
                "error": f"You've reached the maximum of {_MAX_NR_CHARACTERS} characters.",
            }

        # Create character with temp random name (replaced during chargen)
        key = "".join(choices(string.ascii_letters + string.digits, k=10))
        new_char, errors = account.create_character(
            key=key, location=None, ip=sess.address,
        )
        if errors or not new_char:
            err_msg = " ".join(errors) if errors else "Unknown error."
            return "menunode_charselect", {
                "session": session,
                "error": f"Could not create character: {err_msg}",
            }
        new_char.db.chargen_step = "menunode_welcome"
        try:
            new_char.db.prelogout_location = ObjectDB.objects.get_id(
                settings.START_LOCATION
            )
        except Exception:
            pass

    # Defer chargen launch until the login EvMenu is fully closed
    startnode = new_char.db.chargen_step
    account.ndb._login_action = {
        "type": "chargen",
        "session": sess,
        "character": new_char,
        "startnode": startnode,
    }
    return "menunode_exit"


def _do_who(caller, session):
    """Show online players."""
    sessions = evennia.SESSION_HANDLER.get_sessions()
    online = []
    for sess in sessions:
        if not sess.logged_in:
            continue
        puppet = sess.get_puppet()
        if puppet:
            online.append(puppet.key)
        else:
            acct = sess.get_account()
            if acct:
                online.append(f"{acct.key} (OOC)")

    if online:
        caller.msg("|wCurrently online:|n\n  " + "\n  ".join(sorted(online)))
    else:
        caller.msg("|wNo one else is online.|n")

    return "menunode_charselect", {"session": session}


def _do_quit(account, session):
    """Disconnect the session."""
    sess = session or (account.sessions.get()[0] if account.sessions.get() else None)
    if sess:
        account.msg("|wGoodbye!|n", session=sess)
        sess.sessionhandler.disconnect(sess, "Goodbye!")
    return "menunode_exit"
