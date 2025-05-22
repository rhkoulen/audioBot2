from discord.ext import commands
from utils import validate

from discord import FFmpegPCMAudio

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
    
    @commands.command()
    async def join(self, ctx): # if the user is not in a channel, join is tough (TODO: is there a way for me to find a channel if the user specifies a channel name?)
        if ctx.author.voice is None:
            await ctx.send('You must be in a voice channel to use this command.')
            return
        elif ctx.voice_client is not None: # if already in a channel, swap to one the user is in
            await ctx.send(f'Swapping to: "{ctx.author.voice.channel.name}".')
            await ctx.voice_client.disconnect()
            await ctx.author.voice.channel.connect()
            return
        else: # user in a channel, bot not, join the user
            await ctx.send(f'Joining: "{ctx.author.voice.channel.name}".')
            await ctx.author.voice.channel.connect()
            return

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client is None: # if the bot is not in a channel, leave has no use
            await ctx.send('I\'m not in a voice channel.')
            return
        else: # bot in a channel, leave the channel
            await ctx.send('I\'m leaving.')
            await ctx.voice_client.disconnect()
            return

    @commands.command()
    async def add(self, ctx, *, search_terms):
        await ctx.send(f'Adding {search_terms} to the queue.')
        print(search_terms)
        print(type(search_terms))
        self.queue.append(search_terms)

    @commands.command()
    async def remove(self, ctx, index:int):
        back_index = index - 1 # NOTE: the user-facing queue is 1-indexed
        if (back_index < 0) or (back_index > len(self.queue) - 1):
            await ctx.send(f'{index} is out of range for the queue.')
            return
        else:
            await ctx.send(f'Removing {index} from the queue.')
            self.queue.pop(back_index)
            return

    @commands.command()
    async def queue(self, ctx):
        message = ''
        for i, item in enumerate(self.queue):
            message += str(i+1)
            message += '. '
            message += item
            message += '\n'
        await ctx.send(message)




async def setup(bot):
    await bot.add_cog(Music(bot))

async def teardown(bot):
    pass #idk what would even go here :/ but the docs have it
    # I guess this is useful if your bot has a persistent storage or smtg