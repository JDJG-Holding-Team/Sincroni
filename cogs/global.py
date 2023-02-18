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

    @_global.command(name="link")
    async def link(self, ctx):
        await ctx.send("Linking chat.")

    @commands.Cog.listener()
    async def on_message(self, message):
        ctx = await self.bot.get_context(message)

        print("test")

        if ctx.prefix:
            print(f"prefix found {message.content}")
            return message

        if message.author.bot:
            print(f"bot message {message.content}")
            return message

        print(message.content)
        # debug


async def setup(bot):
    await bot.add_cog(Global(bot))
