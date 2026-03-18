import os
import asyncio
import requests
from pyrogram import Client, filters

# Heroku Config Vars
API_ID = int(os.environ.get("API_ID", "33401543"))
API_HASH = os.environ.get("API_HASH", "7cdea5bbc8bd991b4a49807ce86")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("AppxMaster", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Headers (Sandeep Jyani ya kisi bhi Appx app ke liye)
def get_headers(token=None):
    headers = {
        "x-app-id": "12345", # Yahan Sandeep Jyani App ka ID aayega
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Linux; Android 11)"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "🚀 **Appx Ultimate Extractor v3.0**\n\n"
        "🔹 `/appx_p [CourseID] [Token]` - Purchase Batch\n"
        "🔹 `/appx_wp [CourseID] [Token]` - Without Purchase\n"
        "🔹 `/login` - Token nikalne ke liye"
    )

@app.on_message(filters.command("appx_p"))
async def purchase_batch(client, message):
    if len(message.command) < 3:
        return await message.reply_text("❌ Format: `/appx_p [ID] [Token]`")
    
    course_id, token = message.command[1], message.command[2]
    m = await message.reply_text("📥 Purchased links nikal raha hoon...")
    
    url = f"https://api.appx.co.in/v1/course/content/{course_id}"
    res = requests.get(url, headers=get_headers(token)).json()
    
    if res.get("success"):
        file_name = f"Appx_Batch_{course_id}.txt"
        with open(file_name, "w") as f:
            for folder in res['data']:
                f.write(f"📁 {folder['title']}\n")
                for video in folder.get('videos', []):
                    f.write(f"{video['title']}: {video['url']}\n")
        
        await app.send_document(message.chat.id, file_name, caption=f"✅ {course_id} TXT Generated!")
        os.remove(file_name)
    else:
        await m.edit("❌ Failed! Token check karo.")

# --- Fixed Startup for Python 3.14 ---
async def run_bot():
    async with app:
        print("🚀 BOT ONLINE!")
        await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())
  
