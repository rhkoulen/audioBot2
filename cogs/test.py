from discord.ext import commands
from utils import converters

class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def increment(self, ctx, number:converters.atoi):
        await ctx.send(f'{number + 1}')

    @commands.command(aliases=[':)'])
    async def hehe(self, ctx):
        await ctx.send("•̀⩊•́")

    @commands.command()
    async def ping(self, ctx):
        await ctx.send('pong')

    @commands.command()
    async def hello(self, ctx):
        await ctx.send(f'hai {ctx.author.name}')

async def setup(bot):
    await bot.add_cog(Test(bot))

async def teardown(bot):
    pass #idk what would even go here :/ but the docs have it
    # I guess this is useful if your bot has a persistent storage or smtg
