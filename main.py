import os
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# CONFIG
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("appx-pro-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# User session store
user_data = {}

# ---------- START ----------
@app.on_message(filters.command("start"))
async def start(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Appx Login", callback_data="appx_login")]
    ])
    await message.reply_text(
        "🔥 **WELCOME TO APPX PRO BOT**\n\nClick below to continue:",
        reply_markup=buttons
    )

# ---------- BUTTON ----------
@app.on_callback_query()
async def callbacks(client, callback_query):
    user_id = callback_query.from_user.id

    if callback_query.data == "appx_login":
        user_data[user_id] = {"step": "api"}
        await callback_query.message.reply_text(
            "🔗 **STEP 1:** API URL bhejo\n\nExample:\n`https://ignite247api.classx.co.in`"
        )

# ---------- MESSAGE FLOW ----------
@app.on_message(filters.private & ~filters.command(["start"]))
async def handle(client, message):
    user_id = message.from_user.id
    if user_id not in user_data:
        return

    step = user_data[user_id]["step"]
    text = message.text.strip()

    # STEP 1: API
    if step == "api":
        user_data[user_id]["api"] = text.rstrip("/")
        user_data[user_id]["step"] = "token"
        await message.reply_text("🔑 **STEP 2:** Token bhejo (Bearer token)")

    # STEP 2: TOKEN CHECK
    elif step == "token":
        api = user_data[user_id]["api"]
        token = text.replace("Bearer ", "").strip()

        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "Mozilla/5.0"
        }

        m = await message.reply_text("🔍 Checking account...")

        endpoints = [
            "/v1/course/purchased",
            "/v2/course/purchased",
            "/v3/course/purchased"
        ]

        success = False

        async with aiohttp.ClientSession() as session:
            for ep in endpoints:
                try:
                    async with session.get(api + ep, headers=headers, timeout=10) as r:
                        if r.status == 200:
                            try:
                                data = await r.json()
                            except:
                                continue

                            if data.get("data"):
                                user_data[user_id].update({
                                    "token": token,
                                    "step": "batch",
                                    "version": ep.split("/")[1]
                                })

                                txt = "📚 **YOUR BATCHES:**\n\n"
                                for c in data["data"]:
                                    txt += f"🆔 `{c['id']}` → {c['title']}\n"

                                await m.edit(txt + "\n\n👉 Batch ID bhejo")
                                success = True
                                break

                except Exception:
                    continue

        if not success:
            await m.edit("❌ Token ya API invalid")

    # STEP 3: EXTRACT
    elif step == "batch":
        api = user_data[user_id]["api"]
        token = user_data[user_id]["token"]
        version = user_data[user_id]["version"]
        course_id = text

        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "Mozilla/5.0"
        }

        m = await message.reply_text("📥 Extracting data...")

        try:
            url = f"{api}/{version}/course/content/{course_id}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as r:
                    if r.status != 200:
                        return await m.edit("❌ Failed to fetch")

                    try:
                        data = await r.json()
                    except:
                        return await m.edit("❌ JSON error (API blocked)")

            if not data.get("data"):
                return await m.edit("❌ No data found")

            file_name = f"batch_{course_id}.txt"

            with open(file_name, "w", encoding="utf-8") as f:
                for folder in data["data"]:
                    f.write(f"\n📁 {folder.get('title')}\n" + "-"*20 + "\n")

                    for v in folder.get("videos", []):
                        f.write(f"🎬 {v.get('title')} : {v.get('url')}\n")

                    for n in folder.get("notes", []):
                        f.write(f"📄 {n.get('title')} : {n.get('url')}\n")

            await message.reply_document(file_name, caption="✅ Done")
            os.remove(file_name)
            await m.delete()

        except Exception as e:
            await m.edit(f"⚠️ Error: {str(e)}")

# ---------- RUN ----------
async def main():
    async with app:
        print("🚀 BOT RUNNING...")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
    
