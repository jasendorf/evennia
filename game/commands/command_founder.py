"""
Founder buff commands.

Players visit one of the three Founders on Founder's Walk and type
'buff' or 'blessing' to receive their daily buff.

Each buff lasts 1 real hour and has a 24-hour cooldown per Founder.
All three buff effects stack — visit all three Founders before heading out.

Depends on:
    contrib_dorfin/founder_buffs.py   — buff classes and cooldown helpers
    evennia.contrib.rpg.buffs         — BuffHandler on the character
"""

from evennia.commands.command import Command
from evennia.utils.utils import time_format

from contrib_dorfin.founder_buffs import (
    _BUFFS_AVAILABLE,
    FOUNDER_REGISTRY,
    get_founder_data,
    is_on_cooldown,
    set_cooldown,
)


class CmdBuff(Command):
    """
    Receive a blessing from one of the three Founders of Awtown.

    Usage:
        buff
        blessing

    Each Founder grants a different buff that lasts one hour. You may
    receive each buff once per day. Visit all three Founders to stack
    all three blessings before heading out.

    Founders and their buffs:
        Jorvyn Malgrave   — Malgrave's Rally (Persuasion, Leadership, Morale)
        Marro Hammerfall  — Hammerfall's Blessing (Weapon damage, Armour)
        Joleth Ondrel     — Ondrel's Insight (XP gain, Lore checks)
    """

    key = "buff"
    aliases = ["blessing", "bless"]
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        founder, data = get_founder_data(caller.location)

        if not founder:
            caller.msg("There is no Founder here to receive a blessing from.")
            return

        cooldown_key = data["cooldown_key"]
        on_cd, remaining = is_on_cooldown(caller, cooldown_key)

        if on_cd:
            remaining_str = time_format(remaining, style=1)
            if _BUFFS_AVAILABLE and hasattr(caller, "buffs"):
                active = caller.buffs.get(data["buff_key"])
                if active:
                    caller.msg(data["msg_active"].format(remaining=remaining_str))
                    return
            caller.msg(data["msg_cooldown"].format(remaining=remaining_str))
            return

        # Apply the buff
        if _BUFFS_AVAILABLE and hasattr(caller, "buffs"):
            caller.buffs.add(data["buff_class"])
        else:
            caller.msg(
                f"|g{data['name']} is active for 1 hour.|n\n"
                "(Note: stat effects require evennia.contrib.rpg.buffs)"
            )

        set_cooldown(caller, cooldown_key)

        caller.location.msg_contents(
            f"|c{founder.name}|n bestows |w{data['name']}|n upon |w{caller.name}|n.",
            exclude=caller,
        )


class CmdBuffs(Command):
    """
    Check your currently active Founder buffs and cooldowns.

    Usage:
        buffs
        mybuffs
    """

    key = "buffs"
    aliases = ["mybuffs"]
    help_category = "General"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        lines = ["|wFounder Buffs:|n"]
        any_info = False

        for tag_key, data in FOUNDER_REGISTRY.items():
            buff_key     = data["buff_key"]
            cooldown_key = data["cooldown_key"]
            name         = data["name"]

            is_active = False
            if _BUFFS_AVAILABLE and hasattr(caller, "buffs"):
                is_active = bool(caller.buffs.get(buff_key))

            on_cd, remaining = is_on_cooldown(caller, cooldown_key)

            if is_active:
                remaining_str = time_format(remaining, style=1)
                lines.append(f"  |g{name}|n — active, expires in {remaining_str}")
                any_info = True
            elif on_cd:
                remaining_str = time_format(remaining, style=1)
                lines.append(f"  |y{name}|n — on cooldown, available in {remaining_str}")
                any_info = True

        if not any_info:
            lines.append(
                "  |yNo active Founder buffs.|n\n"
                "  Visit the Founders on Founder's Walk before heading out."
            )

        caller.msg("\n".join(lines))
