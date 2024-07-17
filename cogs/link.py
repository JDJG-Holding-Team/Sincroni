from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

from better_profanity import profanity
from discord.ext import commands

import utils

if TYPE_CHECKING:
    from main import Sincroni


class Link(commands.Cog):
    "Linked Chat Commands"

    def __init__(self, bot: Sincroni):
        self.bot: Sincroni = bot

    @commands.Cog.listener("on_message")
    async def linked_channel_handler(self, message: discord.Message):
        supported_message_types = (
            discord.MessageType.default,
            discord.MessageType.reply,
        )
        if (
            not message.guild
            or not message.content
            or message.author.bot
            or message.type not in supported_message_types
        ):
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        linked_channel = self.bot.db.get_linked_channel(ctx.channel.id)
        if not linked_channel:
            return

        # I may need to make two versions when someone links it and then remove the copy.
        # i don't know yet.

        guild_icon = message.guild.icon.url if message.guild.icon else "https://i.imgur.com/3ZUrjUP.png"
        message_content = await commands.clean_content().convert(ctx, message.content)
        message_content = profanity.censor(message_content, censor_char="#")
        message_content = utils.censor_link(message_content)
        message_content = utils.censor_invite(message_content)

        embed = discord.Embed(
            description=str(message_content),
            color=0xEB6D15,
            timestamp=message.created_at,
        )

        embed.set_author(name=message.author, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=ctx.guild)
        embed.set_thumbnail(url=guild_icon)

        if not linked_channel.destination_channel:
            return print(f"missing destination channel : {linked_channel.destination_channel_id}")

        try:
            await linked_channel.destination_channel.send(embed=embed)

        except (discord.HTTPException, discord.Forbidden) as err:
            print("problematic linked channels")
            print(linked_channel.origin_channel_id)
            print(linked_channel.destination_channel_id)
            traceback.print_exception(type(err), err, err.__traceback__)

            # handle error for non working linked channel.

        # maybe make a way for there to be a webhooks on the linked chat too.

    @commands.hybrid_command(name="source")
    async def source(self, ctx: commands.Context):
        github_url = "https://github.com/JDJG-Holding-Team/Sincroni"

        embed = discord.Embed(
            title="Github link", description=f"{github_url}", color=15428885, timestamp=ctx.message.created_at
        )

        embed.set_footer(
            text="This Bot's License is MIT, you must credit if you use my code, but please just make your own, if you don't know something works ask me, or try to learn how mine works."
        )

        await ctx.send(embed=embed)


async def setup(bot: Sincroni):
    await bot.add_cog(Link(bot))
