from discord.ext import commands
from utils import audio, embeds, converters
from utils.audio import SongState as State
from utils.validate import *
from discord import FFmpegPCMAudio, PCMVolumeTransformer

from typing import Dict

class Music(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.guild_states:Dict[int, audio.GuildMusicState] = dict() # TODO: there's probably race conditions abound here :/

    def get_state(self, guild_id:int) -> audio.GuildMusicState: # basically a defaultdict
        if guild_id not in self.guild_states:
            self.guild_states[guild_id] = audio.GuildMusicState()
        return self.guild_states[guild_id]


    # Voice client interface commands
    def play_song(self, ctx:commands.Context, song:audio.SongQueueEntry):
        music_state = self.get_state(ctx.guild.id)
        source = FFmpegPCMAudio(song.filepath, before_options='-nostdin', options='-vn -loglevel error')
        source = PCMVolumeTransformer(source, volume=music_state.volume)
        if not ctx.voice_client:
            raise commands.ChannelNotFound(f'Attempted to call play without a voice client.')
        music_state.keep_playing_semaphore = True
        ctx.voice_client.play(source, after=self._after_playback(ctx))
        music_state.playback_state = State.PLAYING
        music_state.current_song = song
    def skip_song(self, ctx:commands.Context):
        music_state = self.get_state(ctx.guild.id)
        if not ctx.voice_client:
            raise commands.ChannelNotFound(f'Attempted to call resume without a voice client.')
        music_state.keep_playing_semaphore = True
        ctx.voice_client.stop() # this will trigger the `after` callback in play or the play loop, so the next song starts automatically
    def resume_song(self, ctx:commands.Context):
        music_state = self.get_state(ctx.guild.id)
        if not ctx.voice_client:
            raise commands.ChannelNotFound(f'Attempted to call resume without a voice client.')
        music_state.keep_playing_semaphore = True
        ctx.voice_client.resume()
        music_state.playback_state = State.PLAYING
    def assert_is_playing(self, ctx:commands.Context, fail_message:str='I\'m not playing anything.'):
        music_state = self.get_state(ctx.guild.id)
        if music_state.playback_state != State.PLAYING:
            raise commands.CheckFailure(fail_message)
    def assert_is_NOT_playing(self, ctx:commands.Context, fail_message:str='I\'m playing something.'):
        music_state = self.get_state(ctx.guild.id)
        if music_state.playback_state == State.PLAYING:
            raise commands.CheckFailure(fail_message)

    def pause_song(self, ctx:commands.Context):
        music_state = self.get_state(ctx.guild.id)
        if not ctx.voice_client:
            raise commands.ChannelNotFound(f'Attempted to call pause without a voice client.')
        ctx.voice_client.pause()
        music_state.playback_state = State.PAUSED
    def assert_is_paused(self, ctx:commands.Context, fail_message:str='I\'m not paused.'):
        music_state = self.get_state(ctx.guild.id)
        if music_state.playback_state != State.PAUSED:
            raise commands.CheckFailure(fail_message)
    def assert_is_NOT_paused(self, ctx:commands.Context, fail_message:str='I\'m paused.'):
        music_state = self.get_state(ctx.guild.id)
        if music_state.playback_state == State.PAUSED:
            raise commands.CheckFailure(fail_message)

    def stop_song(self, ctx:commands.Context):
        music_state = self.get_state(ctx.guild.id)
        if not ctx.voice_client:
            raise commands.ChannelNotFound(f'Attempted to call stop without a voice client.')
        music_state.keep_playing_semaphore = False
        ctx.voice_client.stop() # triggers _after_playback(), but the semaphore is down, so the queue won't continue
        music_state.playback_state = State.STOPPED
        music_state.current_song = None
    def assert_is_stopped(self, ctx:commands.Context, fail_message:str='I\'m not stopped.'):
        music_state = self.get_state(ctx.guild.id)
        if music_state.playback_state != State.STOPPED:
            raise commands.CheckFailure(fail_message)
    def assert_is_NOT_stopped(self, ctx:commands.Context, fail_message:str='I\'m stopped.'):
        music_state = self.get_state(ctx.guild.id)
        if music_state.playback_state == State.STOPPED:
            raise commands.CheckFailure(fail_message)



    # Loopback commands
    def _after_playback(self, ctx):
        # this layout is chatGPT'd. I got close, but I couldn't figure out precisely how to use asyncio nonsense; turns out, discord.py has a thread creation native :/ thanks ig
        def callback(error):
            if error:
                print(f"Error during playback: {error}")
            self.bot.loop.create_task(self._next_song(ctx))
        return callback
    async def _next_song(self, ctx):
        # Remove the finished song
        music_state = self.get_state(ctx.guild.id)
        finished_song = music_state.current_song
        finished_song.cleanup()
        music_state.current_song = None

        if not music_state.keep_playing_semaphore: # stop the playback if signalled to do so (e.g., on stop, purge, etc.)
            music_state.playback_state = State.STOPPED
            return
        elif await music_state.queue.length() == 0: # nothing to continue playing
            music_state.playback_state = State.STOPPED
            await ctx.send('Queue is now empty.')
            return
        else:
            music_state.playback_state = State.PLAYING
            next_song = await music_state.queue.dequeue()
            self.play_song(ctx, next_song)
            await ctx.send(f'Playing {music_state.current_song.title}.')

    @is_guild_msg()
    @commands.command()
    async def debug_guild_state(self, ctx):
        music_state = self.get_state(ctx.guild.id)
        await ctx.send(str(music_state.playback_state))

    @is_guild_msg()
    @is_NOT_in_voice_channel() # TODO: figure out how to swap voice channels safely (playing, paused, stopped)
    @commands.command(
        help='This command causes the bot to set up a voice client in the channel that the user sent it from. You may optionally provide an argument. This will attempt to search for that as a case-insensitive substring of any of the voice channel names.',
        brief='joins the sender\'s VC',
        usage='(channel name)',
        aliases=['join', 'vc']
    )
    async def connect(self, ctx, *, channel_name:converters.StringToVoiceChannel):
        await ctx.author.voice.channel.connect()
        await ctx.send(f'Joined "{ctx.author.voice.channel.name}".')

    @is_guild_msg()
    @is_in_voice_channel()
    @commands.command(
        help='This command causes the bot to leave the channel that it\'s currently in.',
        brief='leaves the VC',
        usage='',
        aliases=['leave', 'dc', 'fuckoff']
    )
    async def disconnect(self, ctx):
        self.assert_is_stopped(ctx, 'I can\'t leave while there\'s still music. Try `stop`.') # TODO: figure out how to leave voice channels safely (playing, paused)
        temp = ctx.voice_client.channel.name
        await ctx.voice_client.disconnect()
        await ctx.send(f'Left "{temp}".')

    @is_guild_msg()
    @commands.command(
        help='This command adds the specified song to the queue. You can specific a YT link, a YT music link, a Soundcloud link, a Spotify link (Spotify DRM isn\'t cracked publicly, so it\'ll use metadata to search YT), and many more. Any links supported by yt-dl will be accepted. Anything that is not interpreted as a valid link will be plugged into YT and interpreted as search terms.',
        brief='adds song to queue',
        usage='<URL/search terms>',
        aliases=['enqueue', 'search']
    )
    async def add(self, ctx, *, search_terms):
        await ctx.send(f'Attempting to download something from that query...', delete_after=5.)
        song = await audio.download_from_query(search_terms) # TODO: I have no idea what errors this might produce # TODO: this causes stuttering, is that network or CPU?
        queue = self.get_state(ctx.guild.id).queue
        await queue.enqueue(song)
        await ctx.send(f'Added {song.title} from {song.uploader} to the queue.')

    @is_guild_msg()
    @commands.command(
        help='This command removes the specified song from the queue. You should use the index as listed on `queue`, which is 1-indexed.',
        brief='removes song from the queue',
        usage='<index>',
        aliases=['dequeue']
    )
    async def remove(self, ctx, index:int):
        back_index = index - 1 # NOTE: the user-facing queue is 1-indexed
        queue = self.get_state(ctx.guild.id).queue
        if not queue._ind_is_valid(back_index):
            raise commands.BadArgument(f'Invalid queue index {index} (remember this is 1-indexed).')

        await queue.hard_remove(back_index)
        await ctx.send(f'Removed {index} from the queue.')

    @is_guild_msg()
    @commands.command(
        help='This command displays a paginated view of the songs in the queue. There are 10 songs per page with interactive buttons to scroll the pages. Although it is interactive, it isn\'t live. This shows a snapshot of the queue when the user posted the command. If a song ends or a new song is added, the embed will not update.',
        brief='shows the queue',
        usage='',
        aliases=['view', 'list']
    )
    async def queue(self, ctx):
        music_state = self.get_state(ctx.guild.id)
        if await music_state.queue.length() == 0:
            raise commands.CheckFailure('Nothing in the queue bubby.')

        song_list = await music_state.queue.freeze()
        view = embeds.QueueEmbed(ctx=ctx, song_list=song_list, playback_state=music_state.playback_state, current_song=music_state.current_song)
        embed = view.format_page(0)
        await ctx.send(embed=embed, view=view, delete_after=60.)

    @is_guild_msg()
    @is_in_voice_channel()
    @commands.command(
        help='This command starts the playback of songs in the queue.',
        brief='starts playback',
        usage='',
        aliases=['start']
    )
    async def play(self, ctx):
        self.assert_is_NOT_playing(ctx, 'I\'m already playing something.')

        music_state = self.get_state(ctx.guild.id)
        if music_state.playback_state == State.PAUSED:
            self.resume_song(ctx)
            await ctx.send('The current song was paused. Resmued playback.')
        elif await music_state.queue.length() == 0:
            raise commands.CheckFailure('There are no songs in the queue to play. Queue something up!')
        else:
            new_song = await music_state.queue.dequeue()
            self.play_song(ctx, new_song)
            await ctx.send(f'Playing {music_state.current_song.title}.')

    @is_guild_msg()
    @is_in_voice_channel()
    @commands.command(
        help='This command pauses the playback of the current song. This will not skip the song, allowing it to be resumed.',
        brief='pauses current song',
        usage='',
        aliases=[]
    )
    async def pause(self, ctx):
        self.assert_is_NOT_paused(ctx, 'I\'m already paused.')
        self.assert_is_playing(ctx)

        self.pause_song(ctx)
        await ctx.send('Playback paused.')

    @is_guild_msg()
    @is_in_voice_channel()
    @commands.command(
        help='This command stops all playback of the current song. This will skip the song, but playback of the next songs in the queue will not continue',
        brief='stops all playback',
        usage='',
        aliases=[]
    )
    async def stop(self, ctx):
        self.assert_is_NOT_stopped(ctx, 'I\'m already stopped.')

        self.stop_song(ctx)
        await ctx.send('Stopping playback.')

    @is_guild_msg()
    @is_in_voice_channel()
    @commands.command(
        help='This command skips playback of the current song and automatically starts the next song in the queue.',
        brief='skips over current song',
        usage='',
        aliases=[]
    )
    async def skip(self, ctx):
        self.assert_is_playing(ctx)

        self.skip_song(ctx)
        await ctx.send('Skipped the current song.')

    @is_guild_msg()
    @commands.command(
        help='This command clears the queue. This won\'t affect playback of the current song.',
        brief='clears the queue',
        usage='',
        aliases=['purge']
    )
    async def clear(self, ctx):
        await ctx.send('Clearing the queue.')
        queue = self.get_state(ctx.guild.id).queue
        await queue.purge()

    @is_guild_msg()
    @commands.command(
        help='This command adjusts the global volume for your guild. This is set to 0.5 by default, and is saved, but will reset to 0.5 if the bot crashes :/.', # TODO: persistent storage of guild options?
        brief='adjusts volume',
        usage='<volume>',
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

    @is_guild_msg()
    @commands.command(
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
    await music_cog.song_queue.purge() # TODO: update usage (hasn't been changed since multi-guilding changes)
