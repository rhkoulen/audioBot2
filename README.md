### Overview
Currently, this bot does nothing useful.

### Getting Started
1. Create a bot account.
    - Open the [Discord developer portal](https://discord.com/developers/applications).
    - Create a New Application.
    - In `Installation>Install Link`, choose None.
    - In `Bot>Authorization Flow`, disable Public Bot. (if you let your bot be public, someone can easily add your bot to a new server and DDoS your host machine, since this application is quite bad)
    - In `Bot>Privileged Gateway Intents`, enable Message Content Intent.
    - In `Bot>Build-a-Bot`, generate a token, copy it, and add it to `.env.temp`. Remove the `.temp` extension from that filename.
2. Add the bot to your server.
    - In `OAuth2>OAuth2 URL Generator>Scopes`, choose 'Bot'.
    - In `OAuth2>OAuth2 URL Generator>Bot Permissions`, choose 'Administrator'. Or, if you're uncomfortable with that, pick a subset that seems right. I really haven't tested what permissions are required.
    - Navigate to the URL, then add the bot to the server you want.
3. Build the venv on your host.
    - Download [python3.13](https://www.python.org/downloads/release/python-3130/).
    - Navigate to this local repository.
    - `python3.13 -m venv bot-venv`
    - `source bot-venv/bin/activate` (UNIX) or `bot-venv\Scripts\activate.bat` (Windows)
    - `pip install -r requirements.txt`
4. Run the bot on your host.
    - `python main.py`