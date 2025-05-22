from discord.ext import commands
from utils import audio

from discord import FFmpegPCMAudio

# TODO: fill out the help messages in the command decorators
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = audio.SongQueue() # TODO: this only works if the bot is in a single guild.

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=['join', 'c']
    )
    async def connect(self, ctx): # if the user is not in a channel, connect is tough (TODO: is there a way for me to find a channel if the user specifies a channel name?)
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

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=['leave, dc']
    )
    async def disconnect(self, ctx):
        if ctx.voice_client is None: # if the bot is not in a channel, disconnect has no use
            await ctx.send('I\'m not in a voice channel.')
            return
        else: # bot in a channel, leave the channel
            await ctx.send('I\'m leaving.')
            await ctx.voice_client.disconnect()
            return

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=['enqueue']
    )
    async def add(self, ctx, *, search_terms):
        await ctx.send(f'Attempting to download something from that query...')
        song = await audio.download_from_query(search_terms)
        await ctx.send(f'Adding {song.title} from {song.uploader} to the queue.')
        await self.song_queue.enqueue(song)

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=['dequeue']
    )
    async def remove(self, ctx, index:int):
        back_index = index - 1 # NOTE: the user-facing queue is 1-indexed
        try:
            await self.song_queue.hard_remove(back_index)
            await ctx.send(f'Removed {index} from the queue.')
        except AssertionError:
            await ctx.send('Error encountered while removing.')

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=['view', 'list']
    )
    async def queue(self, ctx):
        # TODO: switch this to a fancy discord embed
        # TODO: make some indication of whether the first item is playing or paused or neither
        message = 'Queue:\n'
        songs = await self.song_queue.peek_all()
        for i, item in enumerate(songs):
            message += str(i+1) # NOTE: the user-facing queue is 1-indexed
            message += '. '
            message += item.title
            message += '\n'
        await ctx.send(message)

    # Loopback commands
    def _after_playback(self, ctx): # this layout is chatGPT'd. I got close, but I couldn't figure out precisely what the after parameter wanted from me...
        def callback(error):
            if error:
                print(f"Error during playback: {error}")
            self.bot.loop.create_task(self._next_song(ctx))
        return callback
    async def _next_song(self, ctx):
        # Remove the finished song
        song = await self.song_queue.dequeue()
        song.cleanup() # TODO: alert, this will break if the identical song is queued up twice.

        if await self.song_queue.length() == 0:
            await ctx.send('Queue is now empty.')
            return

        next_song = await self.song_queue.peek(0)
        source = FFmpegPCMAudio(next_song.filepath)
        ctx.voice_client.play(source, after=self._after_playback(ctx))
        await ctx.send(f'Playing {next_song.title}.')
    # The function that starts the play loop.
    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=[]
    )
    async def play(self, ctx):
        if not ctx.voice_client:
            await ctx.send('I\'m not in a VC.')
            return
        elif await self.song_queue.length() == 0:
            await ctx.send('There are no songs in the queue to play. Queue something up!')
            return
        elif ctx.voice_client.is_playing():
            await ctx.send('I\'m already playing something.')
            return
        elif ctx.voice_client.is_paused():
            await ctx.send('The previous song was paused. Resuming.')
            ctx.voice_client.resume()
            return

        song = await self.song_queue.peek(0)
        source = FFmpegPCMAudio(song.filepath)
        await ctx.send(f'Playing {song.title}.')
        ctx.voice_client.play(source, after=self._after_playback(ctx))

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=[]
    )
    async def pause(self, ctx):
        if not ctx.voice_client:
            await ctx.send('I\'m not in a VC.')
            return
        elif not ctx.voice_client.is_playing():
            await ctx.send('I\'m not playing anything.')
            return
        elif ctx.voice_client.is_paused():
            await ctx.send('I\'m already paused.')
            ctx.voice_client.resume()
            return

        await ctx.send('Pausing playback.')
        ctx.voice_client.pause()

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=[]
    )
    async def skip(self, ctx):
        if not ctx.voice_client:
            await ctx.send('I\'m not in a VC.')
            return
        elif not ctx.voice_client.is_playing():
            await ctx.send('I\'m not playing anything.')
            return

        ctx.voice_client.stop() # this will trigger the `after` callback in play or the play loop, so the next song starts automatically
        await ctx.send('Skipped the current song.')

    # TODO: probably need a function to purge the queue. this is surprisingly sucky, given the automatic trigger on _after_playback, might need a "keep dequeueing" semaphore
    # TODO: probably need a function to stop playback (not pause, like, end song and don't keep going); same issue as above


async def setup(bot):
    await bot.add_cog(Music(bot))

async def teardown(bot):
    music_cog = bot.get_cog('Music') # TODO: this does not happen on Ctrl+C. When does this happen?
    await music_cog.song_queue.purge()