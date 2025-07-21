from discord.ext import commands
# from SQL.helper import Helper
import asyncio
import discord
import json
import os
# import sqlite3
import logging
import sys
# Add project root to sys.path so imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load config
try:
    with open("Keys/config.json", "r") as f:
        config = json.load(f)
        TOKEN = config.get("DiscordToken")
        SERVER_ID = int(config.get("ServerID", 0))
        if not TOKEN:
            print("❌ Discord token is missing or invalid in config.json.")
            exit()
except Exception as e:
    print(f"❌ Error reading config.json: {e}")
    exit()

# Check for SQL database
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# db_path = os.path.join(project_root, "SQL", "helper.db")

# if not os.path.isfile(db_path):
#     print("❌ helper.db is missing.")
#     exit()

# try:
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()
#     cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;")
#     print("SQL database loaded successfully.")
#     conn.close()
# except Exception as e:
#     print(f"❌ Failed to access helper.db: {e}")
#     exit()

# Logging setup
logging.basicConfig(level=logging.INFO)

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True
# Instantiate the helper
# helper = Helper(db_path=db_path)
# print("helper dbpath: " + db_path)

class MyBot(commands.Bot):
    def __init__(self):  
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        for filename in os.listdir("./Commands"):
            if filename.endswith("_commands.py"):
                await self.load_extension(f"Commands.{filename[:-3]}")

    async def on_ready(self):
        synced = await self.tree.sync()
        await self.change_presence(activity=discord.Game(name="with my dingaling"))
        print(f"✅ Logged in as {self.user} ({self.user.id})\n"
              f"{len(synced)} cogs synced globally.")
    

bot = MyBot()

## Async main entry point
async def main():
    async with bot:
        await bot.start(TOKEN)

# Run main
if __name__ == "__main__":
    asyncio.run(main())