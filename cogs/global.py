from __future__ import annotations

import functools
import os
from typing import TYPE_CHECKING, Literal, Optional, Union

import discord
from better_profanity import profanity
from discord import app_commands
from discord.ext import commands

from utils import views
from utils.extra import ChatType
from utils.views import Confirm

if TYPE_CHECKING:
    from main import Sincroni


class Global(commands.Cog):
    "Global Chat Commands"

    def __init__(self, bot: Sincroni):
        self.bot: Sincroni = bot

    @staticmethod
    def _check_channel_permissions(
        channel: Union[discord.TextChannel, discord.Thread],
        member: discord.Member,
    ) -> bool:
        TO_CHECK = ["send_messages", "read_messages"]
        perms = channel.permissions_for(member)
        return all(getattr(perms, attr) for attr in TO_CHECK)

    @property
    def base_commands_embed(self) -> discord.Embed:
        emb = discord.Embed(
            title="🌐 Global Chat Setup",
        )
        return emb

    @functools.cached_property
    def mod_webhook(self) -> Optional[discord.Webhook]:
        webhook_url = os.environ["MOD_WEBHOOK"]
        return self.bot.get_webhook_from_url(webhook_url)

    @commands.hybrid_group(name="global")
    @commands.guild_only()
    @commands.has_permissions(manage_guilds=True)
    async def _global(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @_global.command(name="link")
    @commands.guild_only()
    @commands.has_permissions(manage_guilds=True)
    @app_commands.rename(_type="type")
    async def link(
        self,
        ctx: commands.Context,
        channel: Union[discord.TextChannel, discord.Thread] = commands.CurrentChannel,
        _type: Literal["public", "developer"] = "public",
    ):
        """Link a channel as global chat.

        Parameters
        ----------
        channel : Union[discord.TextChannel, discord.Thread]
            The channel to link. Defaults to the current channel.
        """
        # silent the type checker
        if not ctx.guild:
            return

        emb = self.base_commands_embed.copy()
        if self.bot.db.get_global_chat(channel.id):
            emb.description = f"Error\n{channel.mention} is already linked as a global chat."
            return await ctx.send(embed=emb)

        bot_has_permissions = self._check_channel_permissions(channel, ctx.guild.me)
        user_has_permissions = self._check_channel_permissions(channel, ctx.author)  # type: ignore # no, ctx.author is not User

        if not bot_has_permissions or not user_has_permissions:
            if not bot_has_permissions and not user_has_permissions:
                who = "We both"
            elif not bot_has_permissions:
                who = "I"
            else:
                who = "You"

            emb.description = (
                f"Error\n{who} don't have the required permissions to link {channel.mention} as global chat."
            )
            emb.add_field(
                name="Required Permissions",
                value="`Send Messages`, `Read Messages` and `Manage Webhooks`",
            )
            return await ctx.send(embed=emb)

        # user perms
        if not self._check_channel_permissions(channel, ctx.author):  # type: ignore # no, ctx.author is not User
            emb.description = (
                "Error\nYou do not have the required permissions to link {channel.mention} as global chat."
            )
            emb.add_field(
                name="Required Permissions",
                value="`Send Messages`, `Read Messages`",
            )
            return await ctx.send(embed=emb)

        guild_global_chats = list(
            filter(
                lambda modal: modal.server_id == ctx.guild.id, self.bot.db.global_chats  # type: ignore # no, ctx.guild is not None
            )
        )
        enum_type = ChatType[_type.lower()]
        if any(model.chat_type is enum_type for model in guild_global_chats):
            emb.description = f"Error\nThis guild already has a global chat with the chosen type: `{_type}`. Please choose another type or unlink the existing one."
            return await ctx.send(embed=emb)

        webhook_url = None
        if channel.permissions_for(ctx.guild.me).manage_webhooks and channel.permissions_for(ctx.author).manage_webhooks:  # type: ignore # no, ctx.author is not User
            webhook_channel: discord.TextChannel = channel  # type: ignore # no, its not a thread
            if isinstance(channel, discord.Thread):
                webhook_channel = channel.parent  # type: ignore # no, its not a forum

                webhook = await webhook_channel.create_webhook(name=f"{self.bot.user.name} GC")  # type: ignore # bot.user is not None
                webhook_url = webhook.url

        linked = await self.bot.db.add_global_chat(ctx.guild.id, channel.id, enum_type, webhook_url)
        emb.description = f"Success\n{linked.channel} is now linked as global chat."
        await ctx.send(embed=emb)

    @_global.command(name="unlink")
    @commands.guild_only()
    @commands.has_permissions(manage_guilds=True)
    async def unlink(
        self,
        ctx: commands.Context,
        channel: Union[discord.TextChannel, discord.Thread] = commands.CurrentChannel,
    ):
        """Unlink a channel as global chat.

        Parameters
        ----------
        channel : Union[discord.TextChannel, discord.Thread]
            The channel to unlink. Defaults to the current channel.
        """
        # silent the type checker
        if not ctx.guild:
            return

        emb = self.base_commands_embed.copy()
        if self.bot.db.get_global_chat(channel.id):
            emb.description = f"Error\n{channel.mention} is not linked as a global chat."
            return await ctx.send(embed=emb)

        view = await Confirm.prompt(
            ctx,
            user_id=ctx.author.id,
            content=f"Are you sure you want to unlink {channel.mention} as global chat?",
        )
        if view.value is None:
            await view.message.edit(
                content=f"~~{view.message.content}~~ you didn't respond on time!... not doing anything."
            )
            return
        elif view.value is False:
            await view.message.edit(
                content=f"~~{view.message.content}~~ okay, not unlinking {channel.mention} as global chat."
            )
            return
        else:
            await view.message.edit(content=f"~~{view.message.content}~~ unlinking {channel.mention} as global chat.")

        await self.bot.db.remove_global_chat(channel.id)

    @commands.Cog.listener("on_message")
    async def global_chat_handler(self, message: discord.Message):
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

        global_chat = self.bot.db.get_global_chat(ctx.channel.id)
        if not global_chat:
            return

        records = list(
            filter(
                lambda record: (
                    record.chat_type is global_chat.chat_type and record.channel_id != global_chat.channel_id
                ),
                self.bot.db.global_chats,
            )
        )

        guild_icon = message.guild.icon.url if message.guild.icon else "https://i.imgur.com/3ZUrjUP.png"
        message_content = await commands.clean_content().convert(ctx, message.content)

        mod_embed = discord.Embed(
            description=str(message_content),
            color=0xEB6D15,
            timestamp=ctx.message.created_at,
        )
        mod_embed.set_footer(text=str(ctx.guild))
        mod_embed.set_thumbnail(url=guild_icon)

        mod_embed.add_field(name="Guild ID", value=str(message.guild.id), inline=False)
        mod_embed.add_field(name="Channel ID", value=str(message.channel.id), inline=False)
        mod_embed.add_field(name="User ID", value=str(message.author.id), inline=False)
        mod_embed.add_field(name="Message ID", value=str(message.id), inline=False)

        message_content = profanity.censor(message_content, censor_char="#")

        embed = discord.Embed(
            description=str(message_content),
            color=0xEB6D15,
            timestamp=message.created_at,
        )
        embed.set_author(name=message.author, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=ctx.guild)
        embed.set_thumbnail(url=guild_icon)

        webhook_embed = discord.Embed(
            description=str(message_content),
            color=0xEB6D15,
            timestamp=ctx.message.created_at,
        )
        webhook_embed.set_footer(text=str(ctx.guild), icon_url=guild_icon)

        if self.mod_webhook:
            try:
                await self.mod_webhook.send(
                    username=str(ctx.author),
                    embed=mod_embed,
                    avatar_url=ctx.author.display_avatar.url,
                )
            except (discord.HTTPException, discord.Forbidden):
                # TODO: handle invalid mod webhook
                pass

        for record in records:
            # TODO: handle not found global chat channel
            if not record.channel:
                return

            if not record.webhook:
                try:
                    await record.channel.send(embed=embed)
                except (discord.HTTPException, discord.Forbidden):
                    # TODO: handle invalid global chat channel
                    pass
                return

            kwargs = {
                "username": str(ctx.author),
                "embed": embed,
                "avatar_url": ctx.author.display_avatar.url,
            }
            if isinstance(record.channel, discord.Thread):
                kwargs["thread"] = record.channel

            try:
                await record.webhook.send(**kwargs)
            except (discord.HTTPException, discord.Forbidden):
                # TODO: handle invalid global chat webhook
                pass


async def setup(bot: Sincroni):
    await bot.add_cog(Global(bot))
