import os
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("appx-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

def headers(token):
    return {
        "x-app-id": "12345",
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0"
    }

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("🔥 Appx Bot Ready!\n\nUse /appx")

# STEP 1 → ask token
@app.on_message(filters.command("appx"))
async def appx_start(client, message):
    user_data[message.from_user.id] = {}
    await message.reply_text("🔑 Token bhej (Bearer token)")

# STEP 2 → receive token
@app.on_message(filters.private & ~filters.command(["start","appx"]))
async def handle_steps(client, message: Message):
    user_id = message.from_user.id

    if user_id not in user_data:
        return

    # Token phase
    if "token" not in user_data[user_id]:
        token = message.text.strip()
        user_data[user_id]["token"] = token

        msg = await message.reply_text("🔍 Checking account...")

        url = "https://api.appx.co.in/v1/user/profile"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers(token)) as res:
                    data = await res.json()

            if not data.get("success"):
                return await msg.edit("❌ Invalid token")

            await msg.edit("✅ Login success!\n📚 Courses fetch kar raha hu...")

            # Fetch courses
            url2 = "https://api.appx.co.in/v1/course/purchased"

            async with aiohttp.ClientSession() as session:
                async with session.get(url2, headers=headers(token)) as res:
                    courses = await res.json()

            text = "📚 **Your Batches:**\n\n"

            for c in courses.get("data", []):
                text += f"{c.get('id')} → {c.get('title')}\n"

            user_data[user_id]["step"] = "course"
            await message.reply_text(text + "\n\n👉 Course ID bhej")

        except Exception as e:
            await message.reply_text(f"⚠️ Error: {e}")

    # STEP 3 → course id
    elif user_data[user_id].get("step") == "course":
        course_id = message.text.strip()
        token = user_data[user_id]["token"]

        msg = await message.reply_text("📥 Fetching content...")

        url = f"https://api.appx.co.in/v1/course/content/{course_id}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers(token)) as res:
                    data = await res.json()

            if not data.get("success"):
                return await msg.edit("❌ Invalid Course ID")

            file = f"{course_id}.txt"

            with open(file, "w", encoding="utf-8") as f:
                for folder in data.get("data", []):
                    f.write(f"\n📁 {folder.get('title')}\n")

                    for v in folder.get("videos", []):
                        f.write(f"{v.get('title')} : {v.get('url')}\n")

                    for pdf in folder.get("notes", []):
                        f.write(f"{pdf.get('title')} : {pdf.get('url')}\n")

                    for test in folder.get("tests", []):
                        f.write(f"{test.get('title')} : {test.get('url')}\n")

            await message.reply_document(file, caption="✅ Done")
            os.remove(file)
            await msg.delete()

            del user_data[user_id]

        except Exception as e:
            await msg.edit(f"⚠️ Error: {e}")

app.run()
