from __future__ import annotations
from typing import Any, Optional

import functools
import os
import sys
import traceback

import discord
from aiohttp import ClientSession
from discord.ext import commands

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

        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                except commands.errors.ExtensionError:
                    traceback.print_exc()

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

    async def try_channel(self, id: int, /) -> Optional[discord.TextChannel]:
        maybe_channel = self.get_channel(id)

        if maybe_channel:
            return maybe_channel

        try:
            return await self.fetch_channel(id)
        except discord.errors.NotFound:
            return None


bot = Sincroni(intents=discord.Intents.all(), command_prefix="s.")
# figure out a clean way to support prefixes


@bot.event
async def on_ready():
    print("Bot is ready")
    print(bot.user)
    print(bot.user.id)
    # will be changed later


bot.run(os.environ["TOKEN"])
