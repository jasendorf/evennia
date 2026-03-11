"""
DorfinMUD Login Menu — EvMenu Module
=====================================

Post-login character selection screen. Launched from
``Account.at_post_login()`` as an EvMenu on the Account.

Unlike the chargen menu (where caller = session), here the
caller is the **Account** object.
"""

import evennia
from django.conf import settings
from evennia.utils import dedent

_MAX_NR_CHARACTERS = getattr(settings, "MAX_NR_CHARACTERS", 6) or 6


def menunode_charselect(caller, raw_string="", **kwargs):
    """
    Main character-select screen shown after login.

    ``caller`` is the Account.
    """
    account = caller
    characters = [c for c in account.characters if c]
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

    text = dedent(f"""\
        |w=====================================
          Welcome back, {account.key}!
          The Land of Dorfin awaits.
        =====================================|n

          |wYour characters:|n
        {char_section}

          Character slots: {total}/{_MAX_NR_CHARACTERS}
        {error_line}
          |wCommands:|n
            |wplay <name or #>|n    -- enter the game
            |wcreate|n              -- create a new character
            |wwho|n                 -- see who's online
            |wquit|n                -- disconnect
    """)

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

    characters = [c for c in account.characters if c]

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

    # Puppet the character
    sess = session or account.sessions.get()[0] if account.sessions.get() else None
    if sess:
        account.puppet_object(sess, target)
    return None


def _do_create(account, characters, session):
    """Start character creation via the contrib's charcreate command."""
    complete_count = len([c for c in characters if not c.db.chargen_step])
    in_progress = [c for c in characters if c.db.chargen_step]

    if in_progress:
        # Resume existing in-progress character
        sess = session or (account.sessions.get()[0] if account.sessions.get() else None)
        if sess:
            account.execute_cmd("charcreate", session=sess)
        return None

    if len(characters) >= _MAX_NR_CHARACTERS:
        return "menunode_charselect", {
            "session": session,
            "error": f"You've reached the maximum of {_MAX_NR_CHARACTERS} characters.",
        }

    # Start new character creation
    sess = session or (account.sessions.get()[0] if account.sessions.get() else None)
    if sess:
        account.execute_cmd("charcreate", session=sess)
    return None


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
    return None
