import os
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("appx-pro", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

def get_headers(app_id, token=None):
    headers = {"x-app-id": app_id, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    if token: headers["Authorization"] = f"Bearer {token}"
    return headers

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("🚀 **Appx Multi-Login Bot v5.0**\n\nKaam shuru karne ke liye `/login` dabbao.")

@app.on_message(filters.command("login"))
async def login_start(client, message):
    user_data[message.from_user.id] = {"step": "app_id"}
    await message.reply_text("🆔 **STEP 1:** App ka ID (x-app-id) bhejo.\n(Example: `12345`)")

@app.on_message(filters.private & ~filters.command(["start", "login"]))
async def handle_steps(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data: return

    step = user_data[user_id].get("step")
    text = message.text.strip()

    # STEP 1: Get App ID & Show Options
    if step == "app_id":
        user_data[user_id]["app_id"] = text
        user_data[user_id]["step"] = "choose_method"
        await message.reply_text(
            "✅ App ID Set!\n\n**Ab batao kaise login karna hai?**\n\n"
            "1️⃣ Bhejo `ID PASS` (Email Password)\n"
            "2️⃣ Bhejo `OTP 9876543210` (Phone for OTP)\n"
            "3️⃣ Bhejo `TOKEN [Your_Token]` (Direct Token)"
        )

    # STEP 2: Logic for 3 Methods
    elif step == "choose_method":
        app_id = user_data[user_id]["app_id"]
        
        # METHOD 3: DIRECT TOKEN
        if text.startswith("TOKEN "):
            token = text.replace("TOKEN ", "")
            user_data[user_id]["token"] = token
            await fetch_courses(message, app_id, token)

        # METHOD 2: OTP GENERATE
        elif text.startswith("OTP "):
            phone = text.replace("OTP ", "")
            user_data[user_id]["phone"] = phone
            msg = await message.reply_text("📩 OTP bhej raha hoon...")
            url = "https://api.appx.co.in/v1/auth/v2/otp/generate"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"phone": phone}, headers=get_headers(app_id)) as r:
                    res = await r.json()
            if res.get("success"):
                user_data[user_id]["step"] = "verify_otp"
                await msg.edit("✅ OTP bhej diya! Ab `VERIFY [OTP]` bhejo.")
            else: await msg.edit("❌ OTP fail! Number check karo.")

        # METHOD 1: ID/PASS
        else:
            try:
                email, pwd = text.split(" ", 1)
                msg = await message.reply_text("🔐 Logging in with ID/Pass...")
                url = "https://api.appx.co.in/v1/auth/login"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json={"email": email, "password": pwd}, headers=get_headers(app_id)) as r:
                        res = await r.json()
                if res.get("success"):
                    token = res['data']['token']
                    await fetch_courses(message, app_id, token)
                else: await msg.edit("❌ Login failed!")
            except: await message.reply_text("❌ Galat Format!")

    # STEP: VERIFY OTP
    elif step == "verify_otp" and text.startswith("VERIFY "):
        otp = text.replace("VERIFY ", "")
        app_id = user_data[user_id]["app_id"]
        phone = user_data[user_id]["phone"]
        msg = await message.reply_text("🔄 OTP Verify kar raha hoon...")
        url = "https://api.appx.co.in/v1/auth/v2/otp/verify"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"phone": phone, "otp": otp}, headers=get_headers(app_id)) as r:
                res = await r.json()
        if res.get("success"):
            await fetch_courses(message, app_id, res['data']['token'])
        else: await msg.edit("❌ Galat OTP!")

    # FINAL STEP: BATCH EXTRACTION
    elif step == "extract":
        await generate_txt(message, user_data[user_id]["app_id"], user_data[user_id]["token"], text)

async def fetch_courses(message, app_id, token):
    msg = await message.reply_text("📚 Courses fetch kar raha hoon...")
    url = "https://api.appx.co.in/v1/course/purchased"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=get_headers(app_id, token)) as r:
            courses = await r.json()
    if not courses.get("data"): return await msg.edit("📭 No courses found.")
    
    user_id = message.from_user.id
    user_data[user_id].update({"token": token, "step": "extract"})
    text = "📚 **Purchased Batches:**\n\n"
    for c in courses["data"]: text += f"🆔 `{c['id']}` → **{c['title']}**\n"
    await message.reply_text(text + "\n👉 **Batch ID bhejo TXT ke liye!**")

async def generate_txt(message, app_id, token, course_id):
    m = await message.reply_text("📥 Extracting...")
    url = f"https://api.appx.co.in/v1/course/content/{course_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=get_headers(app_id, token)) as r:
            data = await r.json()
    
    file = f"{course_id}.txt"
    with open(file, "w", encoding="utf-8") as f:
        for folder in data.get("data", []):
            f.write(f"\n📁 {folder.get('title')}\n")
            for v in folder.get("videos", []): f.write(f"{v['title']} : {v['url']}\n")
    await message.reply_document(file, caption="✅ Done")
    os.remove(file)

if __name__ == "__main__":
    app.run()
    
