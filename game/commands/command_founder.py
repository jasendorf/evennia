"""
Founder buff command.

Players visit one of the three Founders and type 'buff' or 'blessing'
to receive their daily buff. Each buff lasts 1 hour real time and has
a 24-hour cooldown per Founder.
"""

from evennia.commands.command import Command
from evennia.utils.utils import time_format
import time

FOUNDER_BUFFS = {
    "npc_malgrave": {
        "name": "Malgrave's Rally",
        "attr": "buff_malgrave_expires",
        "last_attr": "buff_malgrave_last",
        "duration": 3600,       # 1 hour
        "cooldown": 86400,      # 24 hours
        "effect": {"persuasion_bonus": 5, "leadership_bonus": 5, "morale_bonus": 10},
        "msg_give": (
            "Jorvyn grabs your hand and shakes it firmly. "
            "'You've got this. Seriously. Now go.' "
            "|gYou feel a surge of confidence. Malgrave's Rally is active for 1 hour.|n"
        ),
        "msg_active": "Jorvyn smiles. 'Still going strong, I see. Come back tomorrow.'",
    },
    "npc_hammerfall": {
        "name": "Hammerfall's Blessing",
        "attr": "buff_hammerfall_expires",
        "last_attr": "buff_hammerfall_last",
        "duration": 3600,
        "cooldown": 86400,
        "effect": {"damage_bonus": 10, "armor_bonus": 10},
        "msg_give": (
            "Marro doesn't look up. He reaches over and tightens something on your gear. "
            "'Better. Now go.' "
            "|gYour weapons feel sharper and your armour heavier. "
            "Hammerfall's Blessing is active for 1 hour.|n"
        ),
        "msg_active": "[doesn't look up] 'Still holding. Come back tomorrow.'",
    },
    "npc_ondrel": {
        "name": "Ondrel's Insight",
        "attr": "buff_ondrel_expires",
        "last_attr": "buff_ondrel_last",
        "duration": 3600,
        "cooldown": 86400,
        "effect": {"xp_bonus": 15, "lore_bonus": 10},
        "msg_give": (
            "Joleth looks up from her book with a warm smile. "
            "'I've been reading about where you're heading. Fascinating history. "
            "The short version: pay attention.' "
            "|gYour mind feels sharp and ready. Ondrel's Insight is active for 1 hour.|n"
        ),
        "msg_active": "Joleth tilts her head. 'You still have the Insight. Back tomorrow.'",
    },
}


def _get_founder_npc(location):
    """Return (npc_tag, buff_data) if a Founder NPC is in this room."""
    from typeclasses.npcs import AwtownNPC
    for obj in location.contents:
        if isinstance(obj, AwtownNPC) and obj.db.npc_role == "founder":
            for tag_key, data in FOUNDER_BUFFS.items():
                if obj.tags.get(tag_key, category="awtown_npc"):
                    return obj, data
    return None, None


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
        founder, buff_data = _get_founder_npc(caller.location)

        if not founder:
            caller.msg("There's no Founder here to receive a blessing from.")
            return

        now = time.time()
        last = caller.attributes.get(buff_data["last_attr"]) or 0
        expires = caller.attributes.get(buff_data["attr"]) or 0

        # Check cooldown
        if now - last < buff_data["cooldown"] and last > 0:
            remaining = buff_data["cooldown"] - (now - last)
            caller.msg(
                f"|y{founder.name} smiles. '{buff_data['msg_active']}'\n"
                f"You can receive this blessing again in "
                f"{time_format(remaining, style=1)}.|n"
            )
            return

        # Apply buff
        caller.attributes.add(buff_data["attr"], now + buff_data["duration"])
        caller.attributes.add(buff_data["last_attr"], now)
        for attr, val in buff_data["effect"].items():
            current = caller.attributes.get(attr) or 0
            caller.attributes.add(attr, current + val)

        caller.msg(buff_data["msg_give"])
        caller.location.msg_contents(
            f"|c{founder.name}|n bestows |w{buff_data['name']}|n upon |w{caller.name}|n.",
            exclude=caller
        )


class CmdBuffs(Command):
    """
    Check your currently active Founder buffs.

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
        now = time.time()
        lines = ["|wActive Founder Buffs:|n"]
        any_active = False

        for tag_key, data in FOUNDER_BUFFS.items():
            expires = caller.attributes.get(data["attr"]) or 0
            if expires > now:
                remaining = expires - now
                lines.append(
                    f"  |g{data['name']}|n — {time_format(remaining, style=1)} remaining"
                )
                any_active = True

        if not any_active:
            lines.append("  |yNo active Founder buffs. Visit the Founders on Founder's Walk.|n")

        caller.msg("\n".join(lines))
