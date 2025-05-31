from .audio import SongQueue, SongQueueEntry
import os
import asyncio

import discord
from discord.ext import commands



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
    def __init__(self, ctx, song_list, current_song, is_paused, entries_per_page=10):
        assert isinstance(song_list, list)
        super().__init__(timeout=60)
        self.ctx = ctx
        self.song_list = song_list
        self.current_song = current_song
        self.is_paused = is_paused
        self.entries_per_page = entries_per_page
        self.total_pages = (len(song_list) + entries_per_page - 1) // entries_per_page
        self.current_page = 0

    def format_page(self, page_index):
        first_song_ind = page_index * self.entries_per_page
        page_entries = self.song_list[first_song_ind:first_song_ind + self.entries_per_page]

        message = ''
        if page_index == 0 and self.current_song != None:
            if self.is_paused:
                message += f'⏸️ PAUSED ⏸️ {format_song(self.current_song)}\n'
            else:
                message += f'▶️ PLAYING ▶️ {format_song(self.current_song)}\n'
        for i, song in enumerate(page_entries):
            message += f'**{first_song_ind + i + 1}.** {format_song(song)}\n'

        embed = discord.Embed(
            title="Music Queue",
            description=message,
            color=discord.Color.dark_theme()
        )
        embed.set_footer(text=f"Page {page_index + 1}/{self.total_pages}")
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
