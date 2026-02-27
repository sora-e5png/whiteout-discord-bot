import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import sys
import discord
import sqlite3
import asyncio
from discord.ext import commands
from colorama import Fore, Style, init

# =========================
# DUMMY WEB SERVER FOR RENDER FREE PLAN
# =========================

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# =========================
# BOT SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True

class CustomBot(commands.Bot):
    async def on_error(self, event_name, *args, **kwargs):
        if event_name == "on_interaction":
            error = sys.exc_info()[1]
            if isinstance(error, discord.NotFound) and error.code == 10062:
                return
        await super().on_error(event_name, *args, **kwargs)

    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.NotFound) and error.code == 10062:
            return
        await super().on_command_error(ctx, error)

bot = CustomBot(command_prefix='/', intents=intents)

init(autoreset=True)

# =========================
# TOKEN FROM RENDER ENVIRONMENT
# =========================

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("ERROR: TOKEN not found in environment variables.")
    exit(1)

# =========================
# DATABASE SETUP
# =========================

if not os.path.exists('db'):
    os.makedirs('db')
    print(Fore.GREEN + "db folder created" + Style.RESET_ALL)

databases = {
    "conn_alliance": "db/alliance.sqlite",
    "conn_giftcode": "db/giftcode.sqlite",
    "conn_changes": "db/changes.sqlite",
    "conn_users": "db/users.sqlite",
    "conn_settings": "db/settings.sqlite",
}

connections = {name: sqlite3.connect(path) for name, path in databases.items()}

def create_tables():
    with connections["conn_changes"] as conn_changes:
        conn_changes.execute('''CREATE TABLE IF NOT EXISTS nickname_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            fid INTEGER, 
            old_nickname TEXT, 
            new_nickname TEXT, 
            change_date TEXT
        )''')
        conn_changes.execute('''CREATE TABLE IF NOT EXISTS furnace_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            fid INTEGER, 
            old_furnace_lv INTEGER, 
            new_furnace_lv INTEGER, 
            change_date TEXT
        )''')

    with connections["conn_settings"] as conn_settings:
        conn_settings.execute('''CREATE TABLE IF NOT EXISTS botsettings (
            id INTEGER PRIMARY KEY, 
            channelid INTEGER, 
            giftcodestatus TEXT 
        )''')

    with connections["conn_users"] as conn_users:
        conn_users.execute('''CREATE TABLE IF NOT EXISTS users (
            fid INTEGER PRIMARY KEY, 
            nickname TEXT, 
            furnace_lv INTEGER DEFAULT 0, 
            kid INTEGER, 
            stove_lv_content TEXT, 
            alliance TEXT
        )''')

    with connections["conn_giftcode"] as conn_giftcode:
        conn_giftcode.execute('''CREATE TABLE IF NOT EXISTS gift_codes (
            giftcode TEXT PRIMARY KEY, 
            date TEXT
        )''')

    with connections["conn_alliance"] as conn_alliance:
        conn_alliance.execute('''CREATE TABLE IF NOT EXISTS alliancesettings (
            alliance_id INTEGER PRIMARY KEY, 
            channel_id INTEGER, 
            interval INTEGER
        )''')

    print(Fore.GREEN + "All tables checked." + Style.RESET_ALL)

create_tables()

# =========================
# LOAD COGS
# =========================

async def load_cogs():
    if os.path.exists("./cogs"):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await bot.load_extension(f"cogs.{filename[:-3]}")

@bot.event
async def on_ready():
    print(f"{Fore.GREEN}Logged in as {bot.user}{Style.RESET_ALL}")
    await bot.tree.sync()

# =========================
# START BOT
# =========================

async def main():
    await load_cogs()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
