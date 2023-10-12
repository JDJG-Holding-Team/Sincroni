from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional, Union

if TYPE_CHECKING:
    from main import Sincroni

from discord.ext import commands
import discord

class Listener(commands.Cog):
    "Listener Cog for events"

    def __init__(self, bot: Sincroni):
        self.bot: Sincroni = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        channels = [channel for channel in guild.channels]
        roles = roles = [role for role in guild.roles]
        embed = discord.Embed(title=f"Bot just joined : {guild.name}", color=random.randint(0, 16777215))

        embed.set_thumbnail(url=guild.icon.url if guild.icon else "https://i.imgur.com/3ZUrjUP.png")

        embed.add_field(name="Server Name:", value=f"{guild.name}")
        embed.add_field(name="Server ID:", value=f"{guild.id}")
        embed.add_field(
            name="Server Creation Date:",
            value=f"{discord.utils.format_dt(guild.created_at, style = 'd')}\n{discord.utils.format_dt(guild.created_at, style = 'T')}",
        )
        embed.add_field(name="Server Owner:", value=f"{guild.owner}")
        embed.add_field(name="Server Owner ID:", value=f"{guild.owner_id}")
        embed.add_field(name="Member Count:", value=f"{guild.member_count}")
        embed.add_field(name="Amount of Channels:", value=f"{len(channels)}")
        embed.add_field(name="Amount of Roles:", value=f"{len(roles)}")
        await self.bot.support_webhook.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        channels = [channel for channel in guild.channels]
        roles = roles = [role for role in guild.roles]
        embed = discord.Embed(title=f"Bot just left : {guild.name}", color=random.randint(0, 16777215))

        embed.set_thumbnail(url=guild.icon.url if guild.icon else "https://i.imgur.com/3ZUrjUP.png")

        embed.add_field(name="Server Name:", value=f"{guild.name}")
        embed.add_field(name="Server ID:", value=f"{guild.id}")

        embed.add_field(
            name="Server Creation Date:",
            value=f"{discord.utils.format_dt(guild.created_at, style = 'd')}\n{discord.utils.format_dt(guild.created_at, style = 'T')}",
        )
        embed.add_field(name="Server Owner:", value=f"{guild.owner}")
        embed.add_field(name="Server Owner ID:", value=f"{guild.owner_id}")
        try:
            embed.add_field(name="Member Count:", value=f"{guild.member_count}")
        except:
            pass
        embed.add_field(name="Amount of Channels:", value=f"{len(channels)}")
        embed.add_field(name="Amount of Roles:", value=f"{len(roles)}")
        await self.bot.support_webhook.send(embed=embed)


async def setup(bot: Sincroni):
    await bot.add_cog(Listener(bot))
