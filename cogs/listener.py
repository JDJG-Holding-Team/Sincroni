from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional, Union

if TYPE_CHECKING:
    from main import Sincroni

from discord.ext import commands


class Listener(commands.Cog):
    "Listener Cog for events"

    def __init__(self, bot: Sincroni):
        self.bot: Sincroni = bot


async def setup(bot: Sincroni):
    await bot.add_cog(Listener(bot))
