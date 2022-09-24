import os
import traceback

import aiohttp
import asyncpg
import discord
import dotenv
from discord.ext import commands

dotenv.load_dotenv()
# -> not sure where I will place this yet


class Sincroni(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:

        self.session = aiohttp.ClientSession()
        self.db = await asyncpg.create_pool(os.getenv("DB_key"))
        # get permission to use Juuzoq's record class, I get how it works, I just don't have permission to use it.

        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                except commands.errors.ExtensionError:
                    traceback.print_exc()


bot = Sincroni(intents=discord.Intents.all(), command_prefix="s.")
# figure out a clean way to support prefixes


@bot.event
async def on_ready():
    print("Bot is ready")
    print(bot.user)
    print(bot.user.id)
    # will be changed later


bot.run(os.environ["TOKEN"])
