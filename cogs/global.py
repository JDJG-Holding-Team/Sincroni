from __future__ import annotations

import functools
import os
import re
import traceback
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

        self.link_regex = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$\-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
        self.discord_regex = re.compile(r"(?:https?://)?(?:www\.)?discord(?:.gg|(?:app)?.com/invite)/[^/\s]+")

    async def cog_load(self):
        profanity.add_censor_words(["balls", "ballss", "ʙᴀʟʟꜱ"])

        # load censor words plus add a custom way to load them, and check the issue below:
        # https://github.com/JDJG-Holding-Team/Sincroni/issues/16#issue-2069012832

    async def cog_unload(self):
        print("cog unloaded")

        # a few extra stuff

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

    @commands.hybrid_group(name="global")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def _global(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @_global.command(name="link")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
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
    @commands.has_permissions(manage_guild=True)
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
        if not self.bot.db.get_global_chat(channel.id):
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

    @commands.hybrid_command(name="rules")
    async def rules(self, ctx: commands.Context):

        embed = discord.Embed(
            title="Rules",
            description=utils.rules)

        await ctx.send(embed=embed)

    @_global.command(name="blacklist")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def blacklist(self, ctx : commands.Context, user : Optional[discord.User], guild : Optional[int], public : bool = True, developer : bool = True):

        # make it require manage_messages only per guild

        # add documenation to the command
    
        guild_grab = bot.get_guild(guild)

        if guild and not user and not guild_grab:
            return await ctx.send("That guild does not exist sadly.")
        
        if not guild_grab and not user:
            return await ctx.send("Please pick at least one to blacklist.")

        if user:
            check_valid_user = self.db.get_blacklist(interaction.guild_id, user.id)
            if not check_valid_user:
                await self.db.add_blacklist(interaction.guild_id, user.id, pub, dev, False, utils.FilterType.user, reason)

        if guild_grab:
            check_valid_guild = self.db.get_blacklist(interaction.guild_id, guild.id)
            if not check_valid_guild:
                await self.db.add_blacklist(interaction.guild_id, guild.id, pub, dev, False, utils.FilterType.server, reason)

    @blacklist.autocomplete("guild")
    async def blacklist_guild_autocomplete(self, interaction : discord.interaction, current: str):
        # ignore current guild in results

        records = [record for record in self.bot.db.global_chats if record.guild and not interaction.guild]

        guilds = [app_commands.Choice(name=f"{record.guild}", value=record.server_id) for record in records]
        startswith: list[Choice] = [choices for choices in guilds if guilds.name.startswith(current)]
        if not (current and startswith):
            return guilds[0:25]

        return guilds


    def censor_links(self, string):

        changed_string = self.discord_regex.sub(":lock: [discord invite redacted] :lock: ", string)
        new_string = self.link_regex.sub(":lock: [link redacted] :lock: ", changed_string)

        return new_string

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

        blacklisted_servers = [
            record.entity_id
            for record in self.bot.db.blacklists
            if not record._global and record.blacklist_type.server and record.server_id == message.guild.id
        ]

        records = list(
            filter(
                lambda record: (
                    record.chat_type is global_chat.chat_type
                    and record.channel_id != global_chat.channel_id
                    and not record.server_id in blacklisted_servers
                ),
                self.bot.db.global_chats,
            )
        )

        # have an anti spam check here.
        # this new filter seems to work fine.
        # maybe make this records filter into something that can handle pub, developer, private types ie detect the chat_type and only grab blacklist stuff from that sort of thing.
        # custom function likely needed

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

        message_content = self.censor_links(message_content)

        guild_name = self.censor_links(str(ctx.guild))
        user_name = self.censor_links(str(message.author))

        embed = discord.Embed(
            description=str(message_content),
            color=0xEB6D15,
            timestamp=message.created_at,
        )
        embed.set_author(name=user_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=guild_name)
        embed.set_thumbnail(url=guild_icon)

        webhook_embed = discord.Embed(
            description=str(message_content),
            color=0xEB6D15,
            timestamp=ctx.message.created_at,
        )
        webhook_embed.set_author(name=user_name, icon_url=ctx.author.display_avatar.url)
        webhook_embed.set_footer(text=guild_name, icon_url=guild_icon)
        webhook_embed.set_thumbnail(url=guild_icon)

        global_blacklisted_user = self.bot.db.get_blacklist(0, message.author.id)
        blacklisted_guild = self.bot.db.get_blacklist(0, message.guild.id)
        blacklisted_user = self.bot.db.get_blacklist(message.guild.id, message.author.id)

        # you do not check if the current guild is blacklisted as that is the origin.

        if global_blacklisted_user or blacklisted_guild or blacklisted_user:

            if self.mod_webhook:
                try:
                    await self.mod_webhook.send(
                        username=f"Blacklisted: {ctx.author}",
                        embed=mod_embed,
                        avatar_url="https://i.imgur.com/qyk9vQq.png",
                    )
                except (discord.HTTPException, discord.Forbidden):
                    # TODO: handle invalid mod webhook
                    pass

            return

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
                print(record.channel_id)
                continue

            blacklisted_user = self.bot.db.get_blacklist(record.server_id, message.author.id)
            blacklisted_guild = self.bot.db.get_blacklist(record.server_id, message.guild.id)

            if blacklisted_user or blacklisted_guild:
                continue

            color_change = self.bot.db.get_embed_color(record.server_id, record.chat_type)

            if color_change:
                embed.color = color_change.custom_color
                webhook_embed.color = color_change.custom_color

            # changes color for specific guilds only.

            else:
                embed.color = discord.Color(0xEB6D15)
                webhook_embed.color = discord.Color(0xEB6D15)

            # changes color back to default so color does not get stuck at the custom color.

            if not record.webhook:
                try:
                    await record.channel.send(embed=embed)
                except (discord.HTTPException, discord.Forbidden) as err:
                    print(record.channel_id)
                    traceback.print_exception(type(err), err, err.__traceback__)
                    pass

                continue

            kwargs = {
                "username": user_name,
                "embed": webhook_embed,
                "avatar_url": ctx.author.display_avatar.url,
            }
            if isinstance(record.channel, discord.Thread):
                kwargs["thread"] = record.channel

            try:
                await record.webhook.send(**kwargs)
            except (discord.HTTPException, discord.Forbidden) as err:
                # TODO: handle invalid global chat webhook

                print(record.channel_id)
                print(record.webhook_url)

                traceback.print_exception(type(err), err, err.__traceback__)
                pass

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
        message_content = self.censor_links(message_content)

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
            pass


async def setup(bot: Sincroni):
    await bot.add_cog(Global(bot))
