from discord.ext import commands
from utils import embeds
import config
import discord
import random



class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help='This command replies to your ping with "Pong!". Might be useful to gauge response time or check if systems are up.',
        brief='pongs back',
        usage='',
        aliases=['p']
    )
    async def ping(self, ctx):
        if random.random() < 0.05:
            await ctx.send('Pong! :D')
        else:
            await ctx.send('Pong!')

    @commands.command(
        help='This command returns helpful information about the available commands. Specifying a specific command name will give lengthier information about that command (like this is, oooh meta).',
        brief='shows this message :)',
        usage='(command name)',
        aliases=[]
    )
    async def help(self, ctx, *, command_name:str=None):
        await ctx.send('AAAAAAAAAAAAAAA')
        if command_name: # help info for a specific command
            command = self.bot.get_command(command_name)
            if (command == None) or command.hidden:
                await ctx.send(f'Command `{command_name}` not found.')
                return
            else:
                await ctx.send(embed=embeds.help_embed(ctx, command))
                return
        else: # brief info for all commands
            mappings = dict()
            for cog in self.bot.cogs.values():
                cmd_list = [cmd for cmd in cog.get_commands() if not cmd.hidden]
                if cmd_list:
                    mappings[cog] = cmd_list
            await ctx.send(embed=embeds.help_all_embed(ctx, mappings))

    @commands.command(
        aliases=[],
        hidden=True
    )
    async def reload(self, ctx):
        for ext in list(self.bot.extensions): # for some reason, I can't do the same thing as in main.py. I'm pretty sure pycache is the culprit, but I don't care to tinker more.
            try:
                await self.bot.reload_extension(ext)
            except Exception as e:
                print(str(e)) # TODO: should I reraise e?

async def setup(bot):
    await bot.add_cog(General(bot))

async def teardown(bot):
    pass