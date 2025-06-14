from discord.ext import commands
import discord
import re

def is_url(search_terms:str):
    return re.match(r'^https?://', search_terms)


# Command decorator generator functions
def rich_decorator(predicate:callable, msg:str):
    """
    Ingests some callable that checks command context.
    If it returns False, it raises a CheckFailure with the custom message.
    This is so that I can supply custom messages to the same decorators.
    """
    async def decorator(ctx:commands.Context):
        if not predicate(ctx):
            raise commands.CheckFailure(msg)
        return True
    
    return commands.check(decorator)

def is_in_voice_channel(fail_message:str='I\'m not in a voice channel.'):
    return rich_decorator(lambda ctx: ctx.voice_client is not None, fail_message)
def is_NOT_in_voice_channel(fail_message:str='I\'m already in a voice channel.'):
    return rich_decorator(lambda ctx: ctx.voice_client is None, fail_message)

def is_guild_msg(fail_message:str='This command only works in servers.'):
    return rich_decorator(lambda ctx: ctx.guild is not None, fail_message)
def is_NOT_guild_msg(fail_message:str='This command only works in DMs.'):
    return rich_decorator(lambda ctx: ctx.guild is None, fail_message)

