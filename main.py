import os
import aiohttp
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("pro-extractor", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

def get_headers(token, api):
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "origin": api,
        "referer": api + "/"
    }

# -------- START --------
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "🔥 PRO Extractor Bot\n\n"
        "/login_token → Token se login\n"
        "/login_id → ID Password se login"
    )

# -------- LOGIN TOKEN --------
@app.on_message(filters.command("login_token"))
async def login_token(client, message):
    user_data[message.from_user.id] = {"step": "api_token"}
    await message.reply_text("🔗 API URL bhejo")

# -------- LOGIN ID --------
@app.on_message(filters.command("login_id"))
async def login_id(client, message):
    user_data[message.from_user.id] = {"step": "api_id"}
    await message.reply_text("🔗 API URL bhejo")

# -------- HANDLER --------
@app.on_message(filters.private)
async def handler(client, message):
    user_id = message.from_user.id
    if user_id not in user_data:
        return

    step = user_data[user_id]["step"]
    text = message.text.strip()

    # TOKEN FLOW
    if step == "api_token":
        user_data[user_id]["api"] = text
        user_data[user_id]["step"] = "token"
        await message.reply_text("🔑 Token bhejo")

    elif step == "token":
        user_data[user_id]["token"] = text.replace("Bearer ", "")
        user_data[user_id]["step"] = "ready"
        await message.reply_text("✅ Login success! Ab /courses likh")

    # ID PASSWORD FLOW
    elif step == "api_id":
        user_data[user_id]["api"] = text
        user_data[user_id]["step"] = "email"
        await message.reply_text("📧 Email bhejo")

    elif step == "email":
        user_data[user_id]["email"] = text
        user_data[user_id]["step"] = "password"
        await message.reply_text("🔒 Password bhejo")

    elif step == "password":
        api = user_data[user_id]["api"]
        email = user_data[user_id]["email"]
        password = text

        msg = await message.reply_text("🔐 Login ho raha hai...")

        # ⚠️ IMPORTANT: Ye endpoint change karna padega app ke hisaab se
        login_url = f"{api}/v1/auth/login"

        payload = {
            "email": email,
            "password": password
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(login_url, json=payload) as r:
                    
                    if "application/json" not in r.headers.get("Content-Type", ""):
                        return await msg.edit("❌ Login failed (HTML response)")

                    data = await r.json()

            # ⚠️ Different apps me token ka key alag hota hai
            token = (
                data.get("token")
                or data.get("access_token")
                or data.get("data", {}).get("token")
            )

            if not token:
                return await msg.edit("❌ Login failed! Endpoint change karna padega")

            user_data[user_id]["token"] = token
            user_data[user_id]["step"] = "ready"

            await msg.edit("✅ Login success! Ab /courses likh")

        except Exception as e:
            await msg.edit(f"⚠️ Error: {e}")

# -------- COURSES --------
@app.on_message(filters.command("courses"))
async def courses(client, message):
    user_id = message.from_user.id
    if user_id not in user_data or user_data[user_id].get("step") != "ready":
        return await message.reply_text("❌ Pehle login karo")

    api = user_data[user_id]["api"]
    token = user_data[user_id]["token"]

    msg = await message.reply_text("📡 Fetching courses...")

    endpoints = [
        "/v1/course/purchased",
        "/v2/course/purchased",
        "/course/purchased",
        "/my-courses"
    ]

    async with aiohttp.ClientSession() as session:
        for ep in endpoints:
            try:
                async with session.get(api + ep, headers=get_headers(token, api)) as r:

                    if "application/json" not in r.headers.get("Content-Type", ""):
                        continue

                    data = await r.json()

                    courses = data.get("data") or data.get("courses")

                    if courses:
                        text = "📚 Courses:\n\n"
                        for c in courses:
                            text += f"{c.get('id')} → {c.get('title')}\n"

                        return await msg.edit(text)

            except:
                continue

    await msg.edit("❌ Courses fetch failed")

# -------- RUN --------
print("🚀 BOT RUNNING")
app.run()
