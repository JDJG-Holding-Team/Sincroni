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

        if ctx.prefix:
            return message

        if message.author.bot:
            return message

        channel = self.bot.db.get_global_chat(ctx.channel.id)

        if channel:
            records = list(
                filter(
                    lambda record: record.chat_type == channel.chat_type and record.channel_id != channel.channel.id,
                    self.bot.db.global_chats,
                )
            )

            args = message.content

            args = await commands.clean_content().convert(ctx, args)
            args = profanity.censor(args, censor_char="#")

            embed = discord.Embed(description=f"{args}", color=0xEB6D15, timestamp=ctx.message.created_at)
            embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.display_avatar.url)
            embed.set_footer(text=f"{ctx.guild}")
            embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else "https://i.imgur.com/3ZUrjUP.png")

            webhook_embed = discord.Embed(description=f"{args}", color=0xEB6D15, timestamp=ctx.message.created_at)
            webhook_embed.set_footer(
                text=f"{ctx.guild}",
                icon_url=ctx.guild.icon.url if ctx.guild.icon else "https://i.imgur.com/3ZUrjUP.png",
            )

            for record in records:

                if record.webhook:
                    await record.webhook.send(
                        username=f"{ctx.author}", embed=webhook_embed, avatar_url=ctx.author.display_avatar.url
                    )

                if record.channel and not record.webhook:
                    await record.channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Global(bot))
