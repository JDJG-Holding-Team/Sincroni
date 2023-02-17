from __future__ import annotations

import functools
import logging
import os
import sys
import traceback
from typing import Any, Optional, Union

import discord
from aiohttp import ClientSession
from discord.ext import commands

from cogs import EXTENSIONS
from utils.database.connection import DatabaseConnection


class Sincroni(commands.Bot):
    session: ClientSession
    db: DatabaseConnection

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = DatabaseConnection(self, os.getenv("DB_key"))  # type: ignore

    async def setup_hook(self) -> None:
        await self.db.create_connection()
        self.session = ClientSession()

        for cog in EXTENSIONS:
            try:
                await self.load_extension(f"{cog}")
            except commands.errors.ExtensionError:
                traceback.print_exc()

        await bot.db.fetch_global_chats()

    async def close(self) -> None:
        await self.session.close()
        await self.db.close()
        await super().close()

    async def on_error(self, event, *args: Any, **kwargs: Any) -> None:
        more_information = sys.exc_info()
        error_wanted = traceback.format_exc()
        traceback.print_exc()

        # print(event)
        # print(more_information[0])
        # print(args)
        # print(kwargs)
        # check about on_error with other repos of mine as well to update this.

    async def try_user(self, id: int, /) -> Optional[discord.User]:
        maybe_user = self.get_user(id)

        if maybe_user is not None:
            return maybe_user

        try:
            return await self.fetch_user(id)
        except discord.errors.NotFound:
            return None

    async def try_member(self, guild: discord.Guild, member_id: int, /) -> Optional[discord.Member]:
        member = guild.get_member(member_id)

        if member:
            return member
        else:
            try:
                return await guild.fetch_member(member_id)
            except discord.errors.NotFound:
                return None

    @functools.cached_property
    def support_webhook(self) -> discord.Webhook:
        webhook_url = os.environ["SUPPORT_WEBHOOK"]
        return discord.Webhook.from_url(webhook_url, session=self.session)

    async def try_channel(
        self, id: int, /
    ) -> Optional[Union[discord.abc.GuildChannel, discord.abc.PrivateChannel, discord.Thread]]:
        maybe_channel = self.get_channel(id)

        if maybe_channel:
            return maybe_channel

        try:
            return await self.fetch_channel(id)
        except discord.errors.NotFound:
            return None


bot = Sincroni(intents=discord.Intents.all(), command_prefix=commands.when_mentioned_or("s."))
# figure out a clean way to support prefixes


@bot.event
async def on_ready():
    print("Bot is ready")
    print(bot.user)

    assert bot.user
    print(bot.user.id)


logging.basicConfig(level=logging.INFO)
bot.run(os.environ["TOKEN"])
