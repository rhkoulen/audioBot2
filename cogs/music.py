from discord.ext import commands
from utils import audio, embeds

from discord import FFmpegPCMAudio, PCMVolumeTransformer

# TODO: fill out the help messages in the command decorators
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_states = {} # maps guild id to a queue and other options

    def get_state(self, guild_id) -> audio.GuildMusicState: # basically a defaultdict
        if guild_id not in self.guild_states:
            self.guild_states[guild_id] = audio.GuildMusicState()
        return self.guild_states[guild_id]

    def play_song(self, ctx, song:audio.SongQueueEntry):
        music_state = self.get_state(ctx.guild.id)
        music_state.current_playback = song
        music_state.keep_playing_semaphore = True
        source = FFmpegPCMAudio(song.filepath, before_options='-nostdin', options='-vn -loglevel error')
        source = PCMVolumeTransformer(source, volume=music_state.volume)
        ctx.voice_client.play(source, after=self._after_playback(ctx))

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=['join', 'c']
    )
    async def connect(self, ctx):
        if ctx.author.voice is None: # if the user is not in a channel, connect is tough (TODO: is there a way for me to find a channel if the user specifies a channel name?)
            await ctx.send('You must be in a voice channel to use this command.')
            return
        elif ctx.voice_client is not None:
            await ctx.send(f'I\'m already in a channel.')
            # This is probably a bad idea, since it might break things if we swap channels while playing something.
            #await ctx.send(f'Swapping to: "{ctx.author.voice.channel.name}".')
            #await ctx.voice_client.disconnect()
            #await ctx.author.voice.channel.connect()
            return
        else:
            await ctx.send(f'Joining: "{ctx.author.voice.channel.name}".')
            await ctx.author.voice.channel.connect()
            return

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=['leave', 'dc']
    )
    async def disconnect(self, ctx):
        if ctx.voice_client is None: # if the bot is not in a channel, disconnect has no use
            await ctx.send('I\'m not in a voice channel.')
            return
        else: # bot in a channel, leave the channel
            await ctx.send('Leaving the VC.')
            await ctx.voice_client.disconnect() # TODO: this leaves a lot of stuff messy with the guild's music state if something is playing, make this graceful
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
        queue = self.get_state(ctx.guild.id).queue
        await queue.enqueue(song)

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=['dequeue']
    )
    async def remove(self, ctx, index:int):
        back_index = index - 1 # NOTE: the user-facing queue is 1-indexed
        try:
            queue = self.get_state(ctx.guild.id).queue
            await queue.hard_remove(back_index)
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
        music_state = self.get_state(ctx.guild.id)
        if await music_state.queue.length() == 0:
            await ctx.send('Nothing in the queue bubby.')
            return

        song_list = await music_state.queue.freeze()
        if not ctx.voice_client:
            view = embeds.QueueEmbed(
                ctx=ctx,
                song_list=song_list,
                current_song=None,
                is_paused=False,
                entries_per_page=10
            )
        else:
            view = embeds.QueueEmbed(
                ctx=ctx,
                song_list=song_list,
                current_song=music_state.current_playback,
                is_paused=ctx.voice_client.is_paused(),
                entries_per_page=10
            )

        embed = view.format_page(0)
        await ctx.send(embed=embed, view=view)


    # Loopback commands
    # this layout is chatGPT'd. I got close, but I couldn't figure out precisely how to use asyncio nonsense; turns out, discord.py has a thread creation native :/ thanks ig
    def _after_playback(self, ctx):
        def callback(error):
            if error:
                print(f"Error during playback: {error}")
            self.bot.loop.create_task(self._next_song(ctx))
        return callback
    async def _next_song(self, ctx):
        # Remove the finished song
        music_state = self.get_state(ctx.guild.id)
        finished_song = music_state.current_playback
        finished_song.cleanup()
        music_state.current_playback = None

        if not music_state.keep_playing_semaphore: # stop the playback if signalled to do so (e.g., on stop, purge, etc.)
            return
        elif await music_state.queue.length() == 0: # nothing to continue playing
            await ctx.send('Queue is now empty.')
            return

        next_song = await music_state.queue.dequeue()
        self.play_song(ctx, next_song)
        await ctx.send(f'Playing {music_state.current_playback.title}.')

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=[]
    )
    async def play(self, ctx):
        music_state = self.get_state(ctx.guild.id)
        if not ctx.voice_client:
            await ctx.send('I\'m not in a VC.')
            return
        elif ctx.voice_client.is_playing():
            await ctx.send('I\'m already playing something.')
            return
        elif ctx.voice_client.is_paused():
            await ctx.send('The current song was paused. Resuming.')
            ctx.voice_client.resume()
            return
        elif await music_state.queue.length() == 0:
            await ctx.send('There are no songs in the queue to play. Queue something up!')
            return

        new_song = await music_state.queue.dequeue()
        self.play_song(ctx, new_song)
        await ctx.send(f'Playing {music_state.current_playback.title}.')

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
    async def stop(self, ctx):
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

        await ctx.send('Stopping playback.')
        music_state = self.get_state(ctx.guild.id)
        music_state.keep_playing_semaphore = False
        ctx.voice_client.stop() # even though this triggers the `after` callback in the play loop, the semaphore makes sure playback stops

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

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=['purge']
    )
    async def clear(self, ctx):
        await ctx.send('Clearing the queue.')
        queue = self.get_state(ctx.guild.id).queue
        await queue.purge()

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=[]
    )
    async def volume(self, ctx, volume:float):
        if not 0.0 <= volume <= 1.0:
            await ctx.send('Volume must be between 0.0 and 1.0.')
            return

        music_state = self.get_state(ctx.guild.id)
        music_state.volume = volume # sets for future songs

        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = volume # sets for current song

        await ctx.send(f'Volume set to {volume * 100:.0f}%.')

    @commands.command(
        help='',
        brief='',
        usage='',
        aliases=[],
        hidden=True # don't let people see this, but it's still funny
    )
    async def evil_volume(self, ctx, volume:float):
        music_state = self.get_state(ctx.guild.id)
        music_state.volume = volume # sets for future songs

        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = volume # sets for current song

        await ctx.send(f'Volume set to {volume * 100:.0f}%.')



async def setup(bot):
    await bot.add_cog(Music(bot))

async def teardown(bot):
    music_cog = bot.get_cog('Music') # TODO: this does not happen on Ctrl+C. When does this happen?
    await music_cog.song_queue.purge()