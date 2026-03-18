import os
import asyncio
import aiohttp
from pyrogram import Client, filters

# Heroku Config Vars
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("appx-universal", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("🌐 **Appx Universal API Extractor**\n\nLogin karne ke liye `/login` dabbao.")

@app.on_message(filters.command("login"))
async def login_start(client, message):
    user_data[message.from_user.id] = {"step": "api_url"}
    await message.reply_text("🔗 **STEP 1:** App ka API Link bhejo.\n(Example: `https://ignite247api.classx.co.in`)")

@app.on_message(filters.private & ~filters.command(["start", "login"]))
async def handle_steps(client, message):
    user_id = message.from_user.id
    if user_id not in user_data: return
    step = user_data[user_id].get("step")
    text = message.text.strip()

    if step == "api_url":
        user_data[user_id]["api_url"] = text.rstrip('/')
        user_data[user_id]["step"] = "token_phase"
        await message.reply_text("✅ API Set! Ab apna **Token** bhejo.")

    elif step == "token_phase":
        token = text.replace("TOKEN ", "")
        api_url = user_data[user_id]["api_url"]
        m = await message.reply_text("📡 Fetching courses...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{api_url}/v1/course/purchased", headers={"Authorization": f"Bearer {token}"}) as r:
                courses = await r.json()
        
        if courses.get("success"):
            user_data[user_id].update({"token": token, "step": "extract"})
            res_text = "📚 **Batches:**\n\n"
            for c in courses["data"]: res_text += f"🆔 `{c['id']}` → {c['title']}\n"
            await message.reply_text(res_text + "\n👉 **Batch ID bhejo!**")
        else: await m.edit("❌ Failed! URL/Token check karo.")

    elif step == "extract":
        # Extract and send TXT logic here...
        await message.reply_text("⏳ Extracting links...")

# THE REAL FIX FOR RESTART/REPLY ISSUE
async def main():
    async with app:
        print("🚀 BOT IS ONLINE AND READY!")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
    
