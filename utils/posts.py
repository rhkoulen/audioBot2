### INACTIVE COG
### The whole reason I wanted this functionality was because Instagram does not embed videos.
### I want to send funny videos.
### I tried to work with this tool, instaloader, but it seems that Instagram has patched up the holes in their API.
### While this cog generally works, it can only download video thumbnails :-(


import discord
from discord.ext import commands

from .validate import is_ig_url
import instaloader
import asyncio
from itertools import count
from io import BytesIO
from aiohttp import ClientSession
from typing import Union, List

POST_TOKEN_GEN = count(0)

def get_token():
    return next(POST_TOKEN_GEN)

async def download_from_query(query:str, index:int, loader:instaloader.Instaloader) -> Union[discord.File, List[discord.File]]:
    match = is_ig_url(query)
    if not match:
        raise commands.UserInputError('Invalid Instagram URL supplied.')
    shortcode = match.group(2)

    try:
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
    except Exception as e:
        raise commands.ExtensionError('`instaloader` failed to download from that link.')

    return await _download_wrapped(post, index)

async def _download_wrapped(post:instaloader.Post, index:int) -> Union[discord.File, List[discord.File]]:
    if post.typename == 'GraphImage':
        async with ClientSession() as session:
            async with session.get(post.url) as response:
                if response.status == 200:
                    data = await response.read()
                    file = discord.File(BytesIO(data), filename=f'media_{get_token()}.jpg')
                    return file
                else:
                    raise ConnectionRefusedError('The HTTP connection failed.')
    elif post.typename == 'GraphVideo':
        async with ClientSession() as session:
            #async with session.get(post.video_url) as response:
            async with session.get(post.url) as response:
                if response.status == 200:
                    print('got it')
                    data = await response.read()
                    file = discord.File(BytesIO(data), filename=f'media_{get_token()}.mp4')
                    return file
                else:
                    raise ConnectionRefusedError('The HTTP connection failed.')
    elif post.typename == "GraphSidecar":
        media_urls = []
        for node in post.get_sidecar_nodes():
            media_urls.append(node.display_url)
            #media_urls.append(node.video_url if node.is_video else node.display_url)

        if index == 0: # post all slides in the sidecar
            files = []
            async with ClientSession() as session:
                for i, media_url in enumerate(media_urls):
                    async with session.get(post.url) as response:
                        if response.status == 200:
                            data = await response.read()
                            file = discord.File(BytesIO(data), filename=f'media_{get_token()}.{'mp4' if '.mp4' in media_url else 'jpg'}')
                            files.append(file)
                        else:
                            raise ConnectionRefusedError('The HTTP connection failed.')
            return files
        elif 1 <= index < len(media_urls)+1: # post a specific slide from the sidecar
            async with ClientSession() as session:
                async with session.get(media_urls[index-1]) as response: # 1-indexed on the user side, 0-indexed list
                    if response.status == 200:
                        data = await response.read()
                        file = discord.File(BytesIO(data), filename=f'media_{get_token()}.mp4')
                        return file
                    else:
                        raise ConnectionRefusedError('The HTTP connection failed.')
        else:
            raise commands.CheckFailure('You specified an invalid index (1-indexed, as seen on the IG post).')
    else:
        raise commands.ArgumentParsingError('I haven\'t handled this type of post.')

async def post_files(ctx:commands.Context, files:Union[discord.File, List[discord.File]], attachments_per_msg:int=10):
    """
    Instagram is always changing how many posts are allowed in slides, and the bot might be rate limited.
    Thus, this provides a dynamic way to post a list of files as attachments.
    If the attachment limit is reached, the bot simply waits for a bit and continues in another batch.
    Don't call this function from a blocking context, it might sleep for a bit.
    """
    if isinstance(files, discord.File):
        await ctx.send(file=files)
    elif isinstance(files, list):
        num_msgs = (len(files) + attachments_per_msg - 1) // attachments_per_msg
        for i in range(num_msgs):
            await ctx.send(files=files[i*attachments_per_msg:i*attachments_per_msg+attachments_per_msg])
            await asyncio.sleep(1)
