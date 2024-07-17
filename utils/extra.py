from __future__ import annotations

import asyncio
import enum
import random
import re
from io import BytesIO
from typing import TYPE_CHECKING

import discord
from PIL import Image

if TYPE_CHECKING:
    from main import Sincroni


class ChatType(enum.IntEnum):
    public = 0
    developer = 1
    private = 2
    repeat = 3


class FilterType(enum.IntEnum):
    user = 0
    server = 1


rules = """
1. No advertising is allowed in the global chat. 
2. Please refrain from sharing NSFW content in the global chat.
3. Do not share malicious links in the global chat.
4. Racial slurs are strictly prohibited in the global chat.
5. If you have any issues with a user in the global chat, please contact me directly. If I deny your request, I will provide an explanation.
6. If you have concerns about the data collected in the global chat, please DM me. I will provide information on the data collected for bot functions, as required by Discord's Terms of Service.
7. Any other concerns or questions regarding content that may violate the rules should be discussed with me privately before taking any action.
8. I have the authority to revoke access to the global chat for any reason, but this decision will always be discussed privately among the global chat moderators.
9. Moderators have the authority to enforce message blacklisting within their guild based on their established rules and guidelines.
For further questions, feel free to DM me at JDJG or join our Discord server at https://discord.gg/JdDxFpNk8J.
"""

link_regex = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$\-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
discord_regex = re.compile(r"(?:https?://)?(?:www\.)?discord(?:.gg|(?:app)?.com/invite)/[^/\s]+")


def censor_link(string):
    changed_string = discord_regex.sub(":lock: [discord invite redacted] :lock: ", string)
    return changed_string


def censor_invite(string):
    new_string = link_regex.sub(":lock: [link redacted] :lock: ", changed_string)

    return new_string


def get_dpy_colors() -> dict[str, int]:
    """Returns a dictionary of discord.py colors.

    These are hard-coded because discord.py could change
    them at any time, and we don't want to rely on that.

    Returns
    -------
    dict[str, int]
        A dictionary of discord.py colors. ``{color_name: color_int, ...}``
    """
    colors = {
        "blue": 3447003,
        "blurple": 5793266,
        "brand_green": 5763719,
        "brand_red": 15548997,
        "dark_blue": 2123412,
        "dark_embed": 2829617,
        "dark_gold": 12745742,
        "dark_gray": 6323595,
        "dark_green": 2067276,
        "dark_grey": 6323595,
        "dark_magenta": 11342935,
        "dark_orange": 11027200,
        "dark_purple": 7419530,
        "dark_red": 10038562,
        "dark_teal": 1146986,
        "dark_theme": 3224376,
        "darker_gray": 5533306,
        "darker_grey": 5533306,
        "fuchsia": 15418782,
        "gold": 15844367,
        "green": 3066993,
        "greyple": 10070709,
        "light_embed": 15658993,
        "light_gray": 9936031,
        "light_grey": 9936031,
        "lighter_gray": 9807270,
        "lighter_grey": 9807270,
        "magenta": 15277667,
        "og_blurple": 7506394,
        "orange": 15105570,
        "pink": 15418783,
        "purple": 10181046,
        "red": 15158332,
        "teal": 1752220,
        "yellow": 16705372,
    }
    return colors


def validate_color(color: str | None, /) -> discord.Color | None:
    """Validate a color string. Basically tries to convert it to a discord.Color.

    What it does in-order:

    1. Checks if the color is falsy or ``None`` (`if not color: ...`) and returns ``None``.
    2. Checks if the color is a digit, and if so, try casting to ``int`` with base 16 and
        then to a ``discord.Color``.
    3. Checks if the color is a valid discord.py color name and returns the corresponding
        ``discord.Color``. The names are hard-coded in the function.
    4. Checks if the color is "random" and returns a random ``discord.Color`` using the
        following: ``discord.Color(random.randint(0, 0xFFFFFF))``.

    If none of the above checks pass, it tries using the ``from_str`` method on ``discord.Color``.

    Parameters
    ----------
    color: str | None
        The color to validate. Can be a hex code, decimal, or one of discord.py's
        built-in colors.

    Returns
    -------
    discord.Color | None
        The validated color. ``None`` if the color is invalid
        or ``color`` is ``None`` / falsy.
    """
    if not color:
        return None

    dpy_colors = get_dpy_colors()

    try:
        if color.isdigit():
            return discord.Color(int(color))
        elif dpy_color := dpy_colors.get(color.lower()):
            return discord.Color(dpy_color)
        elif color.lower() == "random":
            return discord.Color(random.randint(0, 0xFFFFFF))
        else:
            return discord.Color.from_str(color)
    except ValueError:
        return None


def generate_color_block(color_int: int) -> discord.File:
    width = 250
    height = 250

    color_value = discord.Color(color_int)

    image = Image.new("RGB", (width, height), color=(color_value.r, color_value.g, color_value.b))

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return discord.File(buffer, filename="color.png")


def blacklist_lookup(bot: Sincroni, chat_type: ChatType, guild_id: int):
    match chat_type:
        case chat_type.public:
            attribute = "pub"

        case chat_type.developer:
            attribute = "dev"

        case _:
            attribute = chat_type.name

    return [
        record.entity_id
        for record in self.bot.db.blacklists
        if not record._global
        and record.blacklist_type.server
        and record.server_id == guild_id
        and getattr(record, attribute)
    ]
