import discord
from discord.ext import commands
import config
import asyncio

bot = commands.Bot(command_prefix=config.PREFIX, intents=config.INTENTS)

@bot.event
async def on_ready():
    print(f'{bot.user} is online.')

async def go_cog_mode():
    for cog in config.ACTIVE_COGS:
        await bot.load_extension(f'cogs.{cog}') # load the Cog submodules

asyncio.run(go_cog_mode())
bot.run(config.TOKEN)