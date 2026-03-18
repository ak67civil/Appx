import os
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("appx-master", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

def get_headers(app_id, token=None):
    headers = {
        "x-app-id": app_id,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Linux; Android 11)"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("🚀 **Appx Multi-Extractor v4.0**\n\nKaam shuru karne ke liye `/login` dabbao.")

@app.on_message(filters.command("login"))
async def login_start(client, message):
    user_data[message.from_user.id] = {"step": "app_id"}
    await message.reply_text("🆔 **Step 1:** App ka ID (x-app-id) bhejo.\n(Example: `12345`)")

@app.on_message(filters.private & ~filters.command(["start", "login"]))
async def handle_login_steps(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data: return

    step = user_data[user_id].get("step")

    # STEP 1: Get App ID
    if step == "app_id":
        user_data[user_id]["app_id"] = message.text.strip()
        user_data[user_id]["step"] = "credentials"
        await message.reply_text("📧 **Step 2:** Email aur Password bhejo space dekar.\nExample: `example@gmail.com pass123`")

    # STEP 2: Login with Email/Pass
    elif step == "credentials":
        try:
            email, password = message.text.split(" ", 1)
        except:
            return await message.reply_text("❌ Galat format! Email aur Password ke beech space rakho.")

        msg = await message.reply_text("🔐 **Logging in...**")
        app_id = user_data[user_id]["app_id"]
        
        login_url = "https://api.appx.co.in/v1/auth/login"
        payload = {"email": email, "password": password}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(login_url, json=payload, headers=get_headers(app_id)) as resp:
                    data = await resp.json()

            if not data.get("success"):
                return await msg.edit(f"❌ Login Failed: {data.get('message', 'Wrong details')}")

            token = data['data']['token']
            user_data[user_id]["token"] = token
            await msg.edit(f"✅ **Login Success!**\n\n🔑 **Your Token:** `{token}`\n\n📚 Courses fetch kar raha hoon...")

            # STEP 3: Fetch Courses
            course_url = "https://api.appx.co.in/v1/course/purchased"
            async with aiohttp.ClientSession() as session:
                async with session.get(course_url, headers=get_headers(app_id, token)) as resp:
                    courses = await resp.json()

            if not courses.get("data"):
                return await message.reply_text("📭 Is account mein koi purchased course nahi mila.")

            text = "📚 **Your Purchased Batches:**\n\n"
            for c in courses["data"]:
                text += f"🆔 `{c['id']}` → **{c['title']}**\n"

            user_data[user_id]["step"] = "extract"
            await message.reply_text(text + "\n👉 **Batch ID bhejo TXT file ke liye!**")

        except Exception as e:
            await msg.edit(f"⚠️ Error: {str(e)}")

    # STEP 4: Generate TXT
    elif step == "extract":
        course_id = message.text.strip()
        token = user_data[user_id]["token"]
        app_id = user_data[user_id]["app_id"]
        
        m = await message.reply_text("📥 **Extracting Content...**")
        content_url = f"https://api.appx.co.in/v1/course/content/{course_id}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(content_url, headers=get_headers(app_id, token)) as resp:
                    data = await resp.json()

            file_name = f"Batch_{course_id}.txt"
            with open(file_name, "w", encoding="utf-8") as f:
                for folder in data.get("data", []):
                    f.write(f"\n📁 FOLDER: {folder.get('title')}\n" + "="*20 + "\n")
                    for v in folder.get("videos", []):
                        f.write(f"{v.get('title')} : {v.get('url')}\n")
                    for pdf in folder.get("notes", []):
                        f.write(f"{pdf.get('title')} : {pdf.get('url')}\n")

            await message.reply_document(file_name, caption=f"✅ **Extraction Done!**\nCourse ID: {course_id}")
            os.remove(file_name)
            await m.delete()
            del user_data[user_id]
        except Exception as e:
            await m.edit(f"⚠️ Error: {e}")

# --- Fixed Startup for Python 3.14 ---
if __name__ == "__main__":
    print("🚀 BOT IS STARTING...")
    app.run()
