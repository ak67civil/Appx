import os
import aiohttp
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client(
    "appx-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def headers(token):
    return {
        "x-app-id": "12345",
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0"
    }

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("🔥 Appx Bot Ready!")

@app.on_message(filters.command("appx"))
async def appx(client, message):

    if len(message.command) < 3:
        return await message.reply_text("❌ Use: /appx course_id token")

    course_id = message.command[1]
    token = message.command[2]

    msg = await message.reply_text("📥 Fetching...")

    url = f"https://api.appx.co.in/v1/course/content/{course_id}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers(token)) as res:
                data = await res.json()

        if not data.get("success"):
            return await msg.edit("❌ Invalid token")

        file = f"{course_id}.txt"

        with open(file, "w", encoding="utf-8") as f:
            for folder in data.get("data", []):
                f.write(f"\n📁 {folder.get('title')}\n")

                for v in folder.get("videos", []):
                    f.write(f"{v.get('title')} : {v.get('url')}\n")

        await message.reply_document(file)
        os.remove(file)
        await msg.delete()

    except Exception as e:
        await msg.edit(f"⚠️ Error: {e}")

app.run()
