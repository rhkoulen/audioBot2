from yt_dlp import YoutubeDL
from .validate import is_url
import os
import asyncio
from itertools import count

MUSIC_CACHE = os.path.abspath('music_cache')
GLOBAL_TOKEN_GEN = count(0)

def get_token():
    return next(GLOBAL_TOKEN_GEN) # I tried making my own, but this is clean and atomic. Shoutout itertools

class SongQueueEntry:
    def __init__(self, title, uploader, filepath):
        self.title = title
        self.uploader = uploader
        self.filepath = filepath # absolute path to the mp3 (should be in MUSIC_CACHE)

    def cleanup(self):
        try: os.remove(self.filepath)
        except FileNotFoundError: print('CRITICAL: cleanup just attempted to remove a file that was not found.')

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

class GuildMusicState:
    def __init__(self):
        self.queue = SongQueue()
        self.current_playback = None # should hold a SongQueueEntry
        self.volume = 0.5




async def download_from_query(query:str) -> SongQueueEntry:
    return await asyncio.to_thread(_download_wrapped, query)

def _download_wrapped(query:str) -> SongQueueEntry:
    # TODO: how can I speed up rate-limiting? is there a downloader option that lets me multi-connect? will my network card shit itself if I have too many connections?
    if not is_url(query):
        query = f'ytsearch1: {query}'
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(MUSIC_CACHE, f'%(title)s_{get_token()}.%(ext)s'),
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True, # please be quiet
        'no_warnings': True, # please be quiet
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if 'entries' in info: info = info['entries'][0] # snip off the first result

        filename = os.path.splitext(ydl.prepare_filename(info))[0] + '.mp3' # apparently prepare_filename returns the intermediate extension in some submodules, instead of the requested mp3
        title = info.get('title')
        uploader = info.get('uploader')
    return SongQueueEntry(title, uploader, filename)
