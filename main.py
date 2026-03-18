import os
import aiohttp
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("appx-universal", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("🌐 Appx Universal Bot\n\n/login karke start karo")

@app.on_message(filters.command("login"))
async def login_start(client, message):
    user_data[message.from_user.id] = {"step": "api_url"}
    await message.reply_text("🔗 API URL bhejo\nExample:\nhttps://ignite247api.classx.co.in")

@app.on_message(filters.private & ~filters.command(["start", "login"]))
async def handle_steps(client, message):
    user_id = message.from_user.id

    if user_id not in user_data:
        return

    step = user_data[user_id]["step"]
    text = message.text.strip()

    # STEP 1: API URL
    if step == "api_url":
        user_data[user_id]["api_url"] = text.rstrip('/')
        user_data[user_id]["step"] = "token"
        await message.reply_text("🔑 Ab apna Bearer Token bhejo")

    # STEP 2: TOKEN
    elif step == "token":
        token = text.replace("Bearer ", "").strip()
        api_url = user_data[user_id]["api_url"]

        msg = await message.reply_text("📡 Courses fetch ho rahe hai...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{api_url}/v1/course/purchased",
                    headers=get_headers(token)
                ) as res:
                    data = await res.json()

            if not data.get("success"):
                return await msg.edit("❌ Invalid Token ya API")

            user_data[user_id]["token"] = token
            user_data[user_id]["step"] = "course"

            text_msg = "📚 Batches:\n\n"

            for c in data.get("data", []):
                text_msg += f"{c.get('id')} → {c.get('title')}\n"

            await msg.edit(text_msg + "\n\n👉 Batch ID bhejo")

        except Exception as e:
            await msg.edit(f"⚠️ Error: {e}")

    # STEP 3: EXTRACT
    elif step == "course":
        course_id = text
        api_url = user_data[user_id]["api_url"]
        token = user_data[user_id]["token"]

        msg = await message.reply_text("⏳ Extract ho raha hai...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{api_url}/v1/course/content/{course_id}",
                    headers=get_headers(token)
                ) as res:
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

# SIMPLE RUN (NO asyncio.run)
print("🚀 BOT STARTED")
app.run()
