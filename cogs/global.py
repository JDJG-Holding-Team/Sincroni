import re

import discord
from better_profanity import profanity
from discord.ext import commands


class Global(commands.Cog):
    "Global Chat Commands"

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="global", invoke_without_command=False)
    async def _global(self, ctx):
        return

    @_global.command(name="Link")
    async def link(self, ctx):
        await ctx.send("Linking chat.")


async def setup(bot):
    await bot.add_cog(Global(bot))
