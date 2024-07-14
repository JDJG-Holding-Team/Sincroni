from __future__ import annotations

import asyncio
import functools
import os
import random
import re
import traceback
from io import BytesIO
from typing import TYPE_CHECKING, Literal, Optional, Union

import discord
from better_profanity import profanity
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from PIL import Image

from utils import views
from utils.extra import ChatType, FilterType, rules
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
        profanity.add_censor_words(["balls", "ballss", "ʙᴀʟʟꜱ", "kys"])

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
        _type: Literal["public", "developer", "repeat"] = "public",
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
    async def _rules(self, ctx: commands.Context):
        embed = discord.Embed(title="Rules", description=rules)
        await ctx.send(embed=embed)

    @_global.command(name="blacklist")
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(manage_messages=True), commands.has_permissions(manage_guild=True))
    async def blacklist(
        self,
        ctx: commands.Context,
        user: Optional[discord.User],
        guild: Optional[str],
        reason: Optional[str],
        public: bool = True,
        developer: bool = False,
        repeat: bool = False,
    ):
        """Adds the option of user and guild to guild blacklist.

        Parameters
        ----------
        user : Optional[discord.User]
            The user to blacklist.

        guild: Optional[str]
            The guild to blacklist.

        reason: Optional[str]
            A reason why the entity or entities were blacklisted.

        public: bool
            Whatever or not the entity is blacklisted in the public global chat. Defaults to True.

        developer: bool
            Whatever or not the entity is blacklisted in the developer global chat. Defaults to False.

        repeat: bool
            Whatever or not the entity is blacklisted in the repeat global chat. Defaults to False.
        """

        if not ctx.interaction:
            return await ctx.send("You must run this as a slash command.")

        if guild:
            if not guild.isdigit():
                return await ctx.send("That's not a valid guild, please try again.", ephemeral=True)

            valid_guild = self.bot.get_guild(int(guild))

        else:
            valid_guild = None

        if guild and not user and not valid_guild:
            return await ctx.send("Please pick something to blacklist", ephemeral=True)

        if not valid_guild and not user:
            return await ctx.send("Please pick at least one to blacklist.", ephemeral=True)

        if user and not self.bot.db.get_blacklist(ctx.guild.id, user.id):
            await self.bot.db.add_blacklist(
                ctx.guild.id, user.id, public, developer, repeat, False, FilterType.user, reason
            )

            await ctx.send("Added User to blacklist sucessfully")

        if valid_guild and not self.bot.db.get_blacklist(ctx.guild.id, valid_guild.id):
            await self.bot.db.add_blacklist(
                ctx.guild.id, valid_guild.id, public, developer, repeat, False, FilterType.server, reason
            )

            await ctx.send("Added guild to blacklist sucessfully")

        else:
            await ctx.send("You must have already blacklisted someone", ephemeral=True)

    @blacklist.autocomplete("guild")
    async def blacklist_guild_autocomplete(self, interaction: discord.interaction, current: str) -> List[Choice]:
        # ignore current guild in results

        records = [
            record for record in self.bot.db.global_chats if record.guild and record.server_id != interaction.guild_id
        ]

        guilds: list[Choice] = [Choice(name=f"{record.guild}", value=str(record.server_id)) for record in records]
        startswith: list[Choice] = [choices for choices in guilds if choices.name.startswith(current)]

        if not (current and startswith):
            return guilds[0:25]

        return startswith[0:25]

    @blacklist.error
    async def blacklist_error(self, ctx: commands.Context, error):
        await ctx.send(error)

    @_global.command(name="unblacklist")
    @commands.guild_only()
    @commands.check_any(commands.has_permissions(manage_messages=True), commands.has_permissions(manage_guild=True))
    async def unblacklist(
        self,
        ctx: commands.Context,
        user: Optional[discord.User],
        guild: Optional[str],
    ):
        """Removes or Guild from guild blacklist.

        Parameters
        ----------
        user : Optional[discord.User]
            The user to remove from the blacklist.

        guild: Optional[str]
            The guild to remove from the guild blacklist (only blacklisted guilds show up).
        """

        if not ctx.interaction:
            return await ctx.send("You must run this as a slash command.")

        if guild:
            if not guild.isdigit():
                return await ctx.send("That's not a valid guild, please try again.", ephemeral=True)

            valid_guild = self.bot.get_guild(int(guild))

        else:
            valid_guild = None

        if guild and not user and not valid_guild:
            return await ctx.send("Please pick something to unblacklist", ephemeral=True)

        if not valid_guild and not user:
            return await ctx.send("Please pick at least one to unblacklist.", ephemeral=True)

        if user and self.bot.db.get_blacklist(ctx.guild.id, user.id):
            view = await Confirm.prompt(
                ctx,
                user_id=ctx.author.id,
                content=f"Are you sure you want to unblacklist {user}?",
            )

            if view.value is None:
                await view.message.edit(
                    content=f"~~{view.message.content}~~ you didn't respond on time!... not doing anything."
                )
                return

            elif view.value is False:
                await view.message.edit(content=f"~~{view.message.content}~~ okay, not unblacklisting {user}.")
                return

            else:
                await view.message.edit(content="Removed User from blacklist sucessfully")
                await self.bot.db.remove_blacklist(ctx.guild.id, user.id)

        if valid_guild and self.bot.db.get_blacklist(ctx.guild.id, valid_guild.id):
            view = await Confirm.prompt(
                ctx,
                user_id=ctx.author.id,
                content=f"Are you sure you want to unblacklist {valid_guild}?",
            )

            if view.value is None:
                await view.message.edit(
                    content=f"~~{view.message.content}~~ you didn't respond on time!... not doing anything."
                )
                return

            elif view.value is False:
                await view.message.edit(content=f"~~{view.message.content}~~ okay, not unblacklisting {valid_guild}.")
                return

            else:
                await view.message.edit(content="Removed guild from blacklist sucessfully")
                await self.bot.db.remove_blacklist(ctx.guild.id, valid_guild.id)

        else:
            await ctx.send(
                "You must have already unblacklisted them or not added them to the blacklist", ephemeral=True
            )

            # bug where this responds when this should not.

    @unblacklist.autocomplete("guild")
    async def unblacklist_guild_autocomplete(self, interaction: discord.Interaction, current: str) -> List[Choice]:
        # ignore current guild in results

        records = [
            record
            for record in self.bot.db.blacklists
            if isinstance(record.entity, discord.Guild) and record.server_id == interaction.guild_id
        ]

        guilds: list[Choice] = [Choice(name=f"{record.entity}", value=str(record.entity_id)) for record in records]

        startswith: list[Choice] = [choices for choices in guilds if choices.name.startswith(current)]

        if not (current and startswith):
            return guilds[0:25]

        return startswith[0:25]

    @unblacklist.error
    async def unblacklist_error(self, ctx: commands.Context, error):
        await ctx.send(error)

    def get_dpy_colors(self) -> dict[str, int]:
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

    def validate_color(self, color: str | None, /) -> discord.Color | None:
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

        dpy_colors = self.get_dpy_colors()

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

    def generate_color_block(self, color_int: int) -> discord.File:
        width = 250
        height = 250

        color_value = discord.Color(color_int)

        image = Image.new("RGB", (width, height), color=(color_value.r, color_value.g, color_value.b))

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        return discord.File(buffer, filename="color.png")

    @_global.command(
        name="color",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def color(
        self,
        ctx: commands.Context,
        color: str | None = None,
        chat_type: Literal["public", "developer", "repeat"] = "public",
    ):
        """Set a custom color for the specified chat type.

        Parameters
        ----------
        color: str
            The color to set. Can be a hex code, decimal, or one of the following:

            `blue, blurple, brand_green, brand_red, dark_blue, dark_embed, dark_gold, dark_gray, dark_green,
            dark_grey, dark_magenta, dark_orange, dark_purple, dark_red, dark_teal, dark_theme, darker_gray,
            darker_grey, fuchsia, gold, green, greyple, light_embed, light_gray, light_grey, lighter_gray,
            lighter_grey, magenta, og_blurple, orange, pink, purple, red, teal, yellow`.
        chat_type: str
            The chat type to set the color for. Must be one of `public`, `developer`, or `repeat`.
            Defaults to `public`.
        """

        if not ctx.interaction:
            return await ctx.send("you must use this as a slash command.")
        if not ctx.guild:
            return await ctx.send("This command can only be used in a guild.", ephemeral=True)

        enum_type = ChatType[chat_type.lower()]

        # check to make sure the same chat_type doesn't exist.
        if self.bot.db.get_embed_color(ctx.guild.id, enum_type):
            msg = f"A custom color for {chat_type} already exists in this guild."
            if not color:
                msg += " Do you want to remove it?"
            else:
                msg += " Do you want to change it?"

            view = await Confirm.prompt(
                ctx,
                user_id=ctx.author.id,
                content=msg,
            )

            if view.value is None:
                await view.message.edit(
                    content=f"~~{view.message.content}~~ you didn't respond on time!... not doing anything.",
                    view=None,
                )
                # no return needed here.

            elif view.value is False:
                await view.message.edit(
                    content=f"~~{view.message.content}~~ okay, not doing anything.",
                    view=None,
                )
                # no return needed

            else:
                if not color:
                    await self.bot.db.remove_embed_color(ctx.guild.id, enum_type)
                    await view.message.edit(content="Removed custom color succesfully", view=None)
                    # no return needed

                else:
                    await view.message.edit(content="Okay, changing the custom color.", view=None)
                    # works fairly well.

        color_value = self.validate_color(color)
        if not color or not color_value:
            dpy_colors = self.get_dpy_colors()
            return await ctx.send(
                (
                    "Invalid color! Please recheck what you passed. "
                    "It must be a valid hex code, digits, 'random', or one of the following: "
                    f"`{', '.join(dpy_colors.keys())}`"
                ),
                ephemeral=True,
            )

        embed = discord.Embed(title="Please Review", color=color_value.value, description="Color")
        embed.set_footer(text=f"Chat type: {chat_type}\nColor value: {color_value.value}")

        file = await asyncio.to_thread(self.generate_color_block, color_value.value)
        embed.set_image(url=f"attachment://{file.filename}")

        view = await Confirm.prompt(
            ctx,
            user_id=ctx.author.id,
            content="Color Check. Would you like to make this your custom color?",
            embed=embed,
            file=file,
        )

        if view.value is None:
            await view.message.edit(
                content=f"~~{view.message.content}~~ you didn't respond on time!... not doing anything.", view=None
            )
        # not needed return

        elif view.value is False:
            await view.message.edit(content=f"~~{view.message.content}~~ okay, not setting it.", view=None)
            # not needed return

        else:
            await view.message.edit(
                content=f"Set the custom color succesfully for {chat_type} to {str(color_value)}.", view=None
            )
            await self.bot.db.add_embed_color(ctx.guild.id, enum_type, color_value.value)
            # not needed return

    @color.error
    async def color_error(self, ctx: commands.Context, error):
        await ctx.send(error)

    @color.autocomplete("color")
    async def color_autocomplete(self, _: discord.Interaction, current: str) -> list[Choice[str]]:
        dpy_colors: dict[str, int] = self.get_dpy_colors()

        colors: list[Choice] = [Choice(name=name.lower(), value=str(value)) for name, value in dpy_colors.items()]
        startswith: list[Choice] = [choice for choice in colors if choice.name.startswith(current.lower())]
        return ((startswith or colors) if current else colors)[:25]

    def censor_links(self, string):
        changed_string = self.discord_regex.sub(":lock: [discord invite redacted] :lock: ", string)
        new_string = self.link_regex.sub(":lock: [link redacted] :lock: ", changed_string)

        return new_string

    def blacklist_lookup(self, chat_type: ChatType, guild_id: int):
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

        blacklisted_servers = self.blacklist_lookup(global_chat.chat_type, ctx.guild.id)

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
                    # handle error in here.

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
                # handle in here.

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
            # handle error for non working linked channel.


async def setup(bot: Sincroni):
    await bot.add_cog(Global(bot))
