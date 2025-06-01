from .audio import SongQueueEntry, SongState
from typing import Dict, List

import discord
from discord.ext import commands

EMBED_COLOR = discord.Color.teal()



def format_song(song:SongQueueEntry):
    return f'{song.title} — ({format_secs(song.duration)})'

def format_secs(seconds:int):
    if seconds < 0:
        return 'Unknown'
    elif seconds < 3600:
        return f'{seconds // 60:02}:{seconds % 60:02}'
    else:
        return f'{seconds // 3600}:{(seconds % 3600) // 60:02}:{seconds % 60:02}'

class QueueEmbed(discord.ui.View):
    def __init__(self, ctx, song_list, playback_state, current_song, entries_per_page=10):
        assert isinstance(song_list, list)
        super().__init__(timeout=60)
        self.ctx = ctx
        self.song_list = song_list
        self.playback_state = playback_state
        self.current_song = current_song
        self.entries_per_page = entries_per_page
        self.total_pages = (len(song_list) + entries_per_page - 1) // entries_per_page
        self.current_page = 0

    def format_page(self, page_index):
        first_song_ind = page_index * self.entries_per_page
        page_entries = self.song_list[first_song_ind:first_song_ind + self.entries_per_page]

        message = ''
        if page_index == 0 and self.current_song != None:
            if self.playback_state == SongState.STOPPED:
                message += f'⏹️ NOTHING PLAYING ⏹️\n'
            elif self.playback_state == SongState.PAUSED:
                message += f'⏸️ PAUSED ⏸️ {format_song(self.current_song)}\n'
            else:
                message += f'▶️ PLAYING ▶️ {format_song(self.current_song)}\n'
        for i, song in enumerate(page_entries):
            message += f'**{first_song_ind + i + 1}.** {format_song(song)}\n'

        embed = discord.Embed(
            title='Music Queue',
            description=message,
            color=EMBED_COLOR
        )
        embed.set_footer(text=f'Page {page_index + 1}/{self.total_pages}')
        return embed

    async def update_message(self, interaction:discord.Interaction):
        embed = self.format_page(self.current_page)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='<', style=discord.ButtonStyle.gray)
    async def previous(self, interaction, _):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(label='>', style=discord.ButtonStyle.gray)
    async def next(self, interaction, _):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

def help_embed(ctx:commands.Context, command:commands.Command):
    def get_help(ctx:commands.Context, command:commands.Command):
        if command.help:
            return command.help
        elif command.brief:
            return command.brief
        else:
            return 'No description available.'
    def get_aliases(ctx:commands.Context, command:commands.Command):
        if command.aliases:
            return ', '.join(command.aliases)
        else:
            return 'No command aliases.'
    def get_signature(ctx:commands.Context, command:commands.Command):
        if command.signature:
            return f'`{ctx.clean_prefix}{command.qualified_name} {command.signature}`'
        else:
            return f'`{ctx.clean_prefix}{command.qualified_name}`'

    embed = discord.Embed(
        title=f'Help for `{command.name}`',
        description=get_help(ctx, command),
        color=EMBED_COLOR
    )
    embed.add_field(name='Aliases', value=get_aliases(ctx, command), inline=False)
    embed.add_field(name='Usage', value=get_signature(ctx, command), inline=False)
    return embed

def help_all_embed(ctx:commands.Context, mappings:Dict[commands.Cog, List[commands.Command]]):
    def get_signature(command:commands.Command):
        if command.signature:
            return f'{ctx.clean_prefix}{command.qualified_name} {command.signature}'
        else:
            return f'{ctx.clean_prefix}{command.qualified_name}'
    def get_brief(command:commands.Command):
        if command.brief:
            return command.brief
        else:
            return 'No brief available.'
    def pretty_cmd_list(cmd_list:List[commands.Command]):
        max_len = -1
        for cmd in cmd_list:
            if len(get_signature(cmd)) > max_len:
                max_len = len(get_signature(cmd))

        message = '```'
        for cmd in cmd_list:
            message += f'{get_signature(cmd).ljust(max_len)} | {get_brief(cmd)}'
            message += '\n'
        message += '```'
        return message

    embed = discord.Embed(
        title='Available Commands',
        description=f'Use `{ctx.clean_prefix}help <command>` for more details on a specific command.',
        color=EMBED_COLOR
    )
    for cog, cmd_list in mappings.items():
        embed.add_field(name=cog.qualified_name, value=pretty_cmd_list(cmd_list), inline=False)
    embed.set_footer(text=f'<required arg> (optional arg)')
    return embed
