from discord.ext import commands
from utils import validate, audio
import random

from discord import FFmpegPCMAudio

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = audio.SongQueue()

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=['p']
    )
    async def ping(self, ctx):
        if random.random() < 0.02:
            await ctx.send('Pong! :D')
        else:
            await ctx.send('Pong!')

async def setup(bot):
    await bot.add_cog(General(bot))

async def teardown(bot):
    pass