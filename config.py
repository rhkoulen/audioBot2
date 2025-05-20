from discord import Intents
from dotenv import load_dotenv
from os import getenv

PREFIX = '>'

_base = Intents.default() # all intents except privileged ones
_base.message_content = True
INTENTS = _base

load_dotenv()
TOKEN = getenv('DISCORD_BOT_KEY')
