from yt_dlp import YoutubeDL
from .validate import is_url
from enum import Enum
import os
import asyncio

MUSIC_CACHE = os.path.abspath('music_cache')

class SongQueueEntry:
    def __init__(self, title, uploader, filepath):
        self.title = title
        self.uploader = uploader
        self.filepath = filepath # absolute path to the mp3 (should be in MUSIC_CACHE)

    def cleanup(self):
        os.remove(self.filepath)

class SongQueue:
    def __init__(self):
        self._queue = [] # a list of SongQueueEntry objects
        self._lock = asyncio.Lock() # to prevent chatters all typing a kajillion commands at once from causing race conditions (also to give me some asyncio experience)

    def _ind_is_valid(self, ind:int):
        return (ind >= 0) and (ind < len(self._queue))

    async def peek(self, index:int):
        async with self._lock:
            assert self._ind_is_valid(index)
            return self._queue[index]

    async def peek_all(self):
        async with self._lock:
            return self._queue

    async def length(self):
        async with self._lock:
            return len(self._queue)

    async def enqueue(self, entry:SongQueueEntry):
        assert isinstance(entry, SongQueueEntry)
        async with self._lock:
            self._queue.append(entry)

    async def dequeue(self):
        return await self.soft_remove(0)

    async def soft_remove(self, index:int):
        async with self._lock:
            assert self._ind_is_valid(index)
            item = self._queue.pop(index)
        return item

    async def hard_remove(self, index:int):
        item = await self.soft_remove(index)
        item.cleanup()
        return item

    async def purge(self):
        async with self._lock:
            queue_copy = self._queue[:]
            self._queue.clear()
        for entry in queue_copy:
            entry.cleanup()
        for entry in os.listdir(MUSIC_CACHE): # hopefully, nothing is ever dropped, but this will catch the slack
            if entry == '.gitignore': continue
            try: os.remove(os.path.join(MUSIC_CACHE, entry))
            except Exception: pass

async def download_from_query(query:str) -> SongQueueEntry:
    return await asyncio.to_thread(_download_wrapped, query)

def _download_wrapped(query:str) -> SongQueueEntry:
    if not is_url(query):
        query = f'ytsearch1: {query}'
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(MUSIC_CACHE, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True, # suppresses stdout yapping
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if 'entries' in info: info = info['entries'][0] # snip off the first result

        filename = os.path.splitext(ydl.prepare_filename(info))[0] + '.mp3' # apparently prepare_filename returns the intermediate extension in some submodules, instead of the requested mp3
        title = info.get('title')
        uploader = info.get('uploader')
    return SongQueueEntry(title, uploader, filename)
