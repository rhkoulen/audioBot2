import discord
from discord.ext import commands
import config

bot = commands.Bot(command_prefix=config.PREFIX, intents=config.INTENTS)

@bot.event
async def on_ready():
    print(f'{bot.user} is online.')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith(config.PREFIX+'ping'):
        await message.channel.send('pong')


bot.run(config.TOKEN)