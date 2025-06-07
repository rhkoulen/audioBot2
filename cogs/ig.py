import discord
from discord.ext import commands
import utils.posts as posts

import instaloader


class IGPostEmbeds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loader = instaloader.Instaloader( # suppress all file handling, just use data streams (i had quite enough in dealing with the music stuff)
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern=""
        )

    @commands.command(
        help='This command scrapes content from the specified Instagram link and sends it as an attachment. This is capable of downloading content from sidecars (slides). If you send a link to an IG sidecar, you can specify an index (1-indexed) for it to specifically download, otherwise it attaches all of them.',
        brief='displays instagram content',
        usage='<URL> (index for slides)',
        aliases=['ig', 'ig_embed']
    )
    async def igembed(self, ctx:commands.Context, url, index:int=0):
        author = ctx.author.nick
        await ctx.message.delete()
        await ctx.send(f'Attempting to download something from that query...', delete_after=3.)
        result = await posts.download_from_query(url, index, self.loader) # TODO: I have no idea what errors this might produce
        await ctx.send(f'Post courtesy of {author}.')
        self.bot.loop.create_task(posts.post_files(ctx, result))

async def setup(bot):
    await bot.add_cog(IGPostEmbeds(bot))