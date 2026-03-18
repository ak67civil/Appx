import os
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

# Heroku Config Vars
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("appx-api-pro", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

# Headers Helper
def get_headers(token=None):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Linux; Android 11)"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("🌐 **Appx Universal API Extractor**\n\nShuru karne ke liye `/login` dabbao.")

@app.on_message(filters.command("login"))
async def login_start(client, message):
    user_data[message.from_user.id] = {"step": "api_url"}
    await message.reply_text("🔗 **STEP 1:** App ka API Link bhejo.\n(Example: `https://ignite247api.classx.co.in`)")

@app.on_message(filters.private & ~filters.command(["start", "login"]))
async def handle_steps(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data: return

    step = user_data[user_id].get("step")
    text = message.text.strip()

    # STEP 1: Get API URL
    if step == "api_url":
        # Clean URL (Remove trailing slash)
        api_url = text.rstrip('/')
        user_data[user_id]["api_url"] = api_url
        user_data[user_id]["step"] = "token_phase"
        await message.reply_text(f"✅ API Set: `{api_url}`\n\n🔑 **STEP 2:** Apna **Token** bhejo list nikalne ke liye.")

    # STEP 2: Get Token & Fetch Courses
    elif step == "token_phase":
        token = text.replace("TOKEN ", "") # Handle both "TOKEN xyz" and "xyz"
        api_url = user_data[user_id]["api_url"]
        
        msg = await message.reply_text("📡 Server se connect kar raha hoon...")
        
        # Appx standard purchased course endpoint
        course_url = f"{api_url}/v1/course/purchased"
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.get(course_url, headers=get_headers(token)) as r:
                    if r.status != 200:
                        return await msg.edit(f"❌ Server Error: {r.status}\nShayad URL ya Token galat hai.")
                    
                    courses = await r.json()
            
            if not courses.get("data"):
                return await msg.edit("📭 Is account mein koi courses nahi mile.")

            user_data[user_id].update({"token": token, "step": "extract"})
            
            res_text = "📚 **Your Purchased Batches:**\n\n"
            for c in courses["data"]:
                res_text += f"🆔 `{c['id']}` → **{c['title']}**\n"
            
            await message.reply_text(res_text + "\n👉 **Batch ID bhejo TXT file ke liye!**")
            await msg.delete()

        except Exception as e:
            await msg.edit(f"⚠️ Connection Failed!\nError: {str(e)}")

    # STEP 3: Generate TXT File
    elif step == "extract":
        course_id = text
        token = user_data[user_id]["token"]
        api_url = user_data[user_id]["api_url"]
        
        m = await message.reply_text("📥 Extracting all links...")
        content_url = f"{api_url}/v1/course/content/{course_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(content_url, headers=get_headers(token)) as r:
                    data = await r.json()
            
            file_name = f"Batch_{course_id}.txt"
            with open(file_name, "w", encoding="utf-8") as f:
                for folder in data.get("data", []):
                    f.write(f"\n📁 {folder.get('title')}\n" + "="*20 + "\n")
                    for v in folder.get("videos", []):
                        f.write(f"{v['title']} : {v['url']}\n")
                    for p in folder.get("notes", []):
                        f.write(f"{p['title']} : {p['url']}\n")

            await message.reply_document(file_name, caption=f"✅ Extraction Done!\nBatch ID: {course_id}")
            os.remove(file_name)
            await m.delete()
        except Exception as e:
            await m.edit(f"⚠️ Extraction Error: {e}")

# Stable Startup for Python 3.14
async def main():
    async with app:
        print("🚀 UNIVERSAL BOT IS LIVE!")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
            
