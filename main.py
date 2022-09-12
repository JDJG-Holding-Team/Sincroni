import os

import discord
import dotenv
from discord.ext import commands

# import asyncpg -> soon

bot = commands.Bot(intents=discord.Intents.all(), command_prefix="s.")
# figure out a clean way to support prefixes

# dotenv.load_dotenv() -> not sure where I will place this yet


@bot.event
async def on_ready():
    print("Bot is ready")
    print(bot.user)
    print(bot.user.id)
    # will be changed later


bot.run(os.environ["TOKEN"])
