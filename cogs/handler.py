import discord
from discord.ext import commands
import config

class Handler(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.notify_id = config.ADMIN_ID
        self.known_exceptions = (
            commands.MissingRequiredArgument,
            commands.BadArgument,
            commands.CommandNotFound,
            commands.CommandOnCooldown,
            commands.MissingPermissions,
            commands.BotMissingPermissions,
            commands.NoPrivateMessage,
            commands.DisabledCommand,
            commands.CheckFailure,
            commands.UserInputError,
            commands.ExtensionError,
            commands.ArgumentParsingError,
        )
    # This is probably really bad, but I want it to at least say something.

    @commands.Cog.listener()
    async def on_command_error(self, ctx:commands.Context, error:commands.CommandError):
        if hasattr(ctx.command, 'on_error'): # check for existing error handlers
            return

        if hasattr(error, 'original'): # check for discord.py wrapped error
            error = getattr(error, 'original', error)

        if isinstance(error, self.known_exceptions):
            await ctx.send(f'An error occurred: {str(error)}')
        else:
            await ctx.send(f'A critical, unexpected error occurred. Notifying <@{self.notify_id}>.')
            print(str(error))

async def setup(bot):
    await bot.add_cog(Handler(bot))

async def teardown(bot):
    pass