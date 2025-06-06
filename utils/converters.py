from discord.ext import commands
import discord
from typing import Union



class StringToVoiceChannel(commands.Converter):
    # Need to do this as a Converter class, since it needs guild context.
    async def convert(self, ctx:commands.Context, channel_name:str) -> Union[discord.VoiceChannel, None]:
        if not channel_name and not ctx.author.voice: # no specified arg and no user VC -> error
            raise commands.BadArgument('If you are not in a voice channel, you must specify one.')
        elif not channel_name and ctx.author.voice: # no specified arg and user VC -> user VC
            return ctx.author.voice.channel
        else: # specified arg -> try to join specified arg (regardless of user VC), might error
            for channel in ctx.guild.voice_channels:
                if channel_name.lower() in channel.name.lower():
                    return channel
            raise commands.BadArgument(f'No voice channel found matching "{channel_name}".')

class ForceStringNonEmpty(commands.Converter):
    async def convert(self, ctx:commands.Context, arg:str) -> str:
        if not arg:
            raise commands.BadArgument(f'Supplied argument was empty.')
        return arg