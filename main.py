import os
import asyncio
import requests
from pyrogram import Client, filters

# Heroku Config Vars
API_ID = int(os.environ.get("API_ID", "33401543"))
API_HASH = os.environ.get("API_HASH", "7cdea5bbc8bd991b4a49807ce86")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client(
    "AppxMaster",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# Headers (Sandeep Jyani ya kisi bhi Appx app ke liye)
def get_headers(token=None):
    headers = {
        "x-app-id": "12345", # Yahan apna App ID dalna
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Linux; Android 11)"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("🚀 **Appx Bot Online!**\n\nAb crash nahi hoga, loop fix kar diya hai.")

# --- THE REAL FIX FOR PYTHON 3.14 ---
async def main():
    async with app:
        print("🚀 BOT STARTED SUCCESSFULLY!")
        await asyncio.Future() # Bot ko online rakhne ke liye

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
        
