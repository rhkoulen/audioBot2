import os
from dotenv import load_dotenv
import discord

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} is online.')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('.ping'):
        await message.channel.send('pong')

load_dotenv()
client.run(os.getenv('DISCORD_BOT_KEY'))