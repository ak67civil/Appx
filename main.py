import os
import aiohttp
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client(
    "AppxBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def get_headers(token=None):
    headers = {
        "x-app-id": "12345",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("✅ Bot Running Successfully!")


@app.on_message(filters.command("appx_p"))
async def purchase_batch(client, message):

    if len(message.command) < 3:
        return await message.reply_text("❌ Usage: /appx_p course_id token")

    course_id = message.command[1]
    token = message.command[2]

    msg = await message.reply_text("📥 Fetching data...")

    url = f"https://api.appx.co.in/v1/course/content/{course_id}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=get_headers(token)) as res:
                data = await res.json()

        if not data.get("success"):
            return await msg.edit("❌ Invalid token or course ID")

        file_name = f"batch_{course_id}.txt"

        with open(file_name, "w", encoding="utf-8") as f:
            for folder in data.get("data", []):
                f.write(f"📁 {folder.get('title')}\n")

                for video in folder.get("videos", []):
                    f.write(f"{video.get('title')} : {video.get('url')}\n")

        await message.reply_document(file_name, caption="✅ Done")
        os.remove(file_name)
        await msg.delete()

    except Exception as e:
        await msg.edit(f"⚠️ Error: {e}")


app.run()
