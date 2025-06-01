from discord.ext import commands
import discord
import config
import asyncio

bot = commands.Bot(
    command_prefix=config.PREFIX,
    help_command=None, # I know you're really not supposed to do this, but I really dislike the default framework.
    intents=config.INTENTS,
)

@bot.event
async def on_ready():
    print(f'{bot.user} is online.')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='>help'))

async def go_cog_mode():
    for cog in config.ACTIVE_COGS:
        await bot.load_extension(f'cogs.{cog}') # load the Cog submodules

asyncio.run(go_cog_mode())
bot.run(config.TOKEN)