import os
import asyncio
import aiohttp
from pyrogram import Client, filters

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("cp-pro", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

def headers(api_key="877665", token=None):
    h = {
        "api-key": api_key,
        "device-id": "android_123",
        "User-Agent": "Mobile-Android",
        "Content-Type": "application/json"
    }
    if token:
        h["x-access-token"] = token
    return h

# START
@app.on_message(filters.command("start"))
async def start(client, msg):
    await msg.reply_text("🎓 ClassPlus Bot\n\nLogin: /cp_login")

# LOGIN START
@app.on_message(filters.command("cp_login"))
async def login(client, msg):
    user_data[msg.from_user.id] = {"step": "org"}
    await msg.reply_text("Org Code bhejo")

# FLOW
@app.on_message(filters.private & ~filters.command(["start","cp_login"]))
async def flow(client, msg):
    uid = msg.from_user.id
    if uid not in user_data:
        return

    step = user_data[uid]["step"]
    text = msg.text.strip()

    # ORG
    if step == "org":
        user_data[uid]["org"] = text
        user_data[uid]["step"] = "phone"
        await msg.reply_text("Phone bhejo (91xxxxxxxxxx)")

    # PHONE
    elif step == "phone":
        user_data[uid]["phone"] = text
        url = f"https://api.classplusapp.com/v2/otp/generate?mobileNumber={text}&orgCode={user_data[uid]['org']}"

        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers=headers()) as r:
                try:
                    data = await r.json()
                except:
                    return await msg.reply_text("❌ API error")

        if data.get("success"):
            user_data[uid]["session"] = data["data"]["sessionId"]
            user_data[uid]["step"] = "otp"
            await msg.reply_text("OTP bhejo")
        else:
            await msg.reply_text("❌ OTP send fail")

    # OTP
    elif step == "otp":
        payload = {
            "otp": text,
            "mobileNumber": user_data[uid]["phone"],
            "sessionId": user_data[uid]["session"],
            "orgCode": user_data[uid]["org"]
        }

        async with aiohttp.ClientSession() as s:
            async with s.post("https://api.classplusapp.com/v2/otp/verify", json=payload, headers=headers()) as r:
                try:
                    data = await r.json()
                except:
                    return await msg.reply_text("❌ Verify error")

        if data.get("success"):
            token = data["data"]["token"]
            user_data[uid]["token"] = token
            user_data[uid]["step"] = "batch"

            await msg.reply_text("✅ Login Success\nFetching batches...")
            await fetch_batches(msg, token)
        else:
            await msg.reply_text("❌ OTP wrong")

    # BATCH SELECT
    elif step == "batch":
        await extract_batch(msg, text)

# FETCH BATCHES
async def fetch_batches(msg, token):
    async with aiohttp.ClientSession() as s:
        async with s.get("https://api.classplusapp.com/v2/batches/list", headers=headers(token=token)) as r:
            try:
                data = await r.json()
            except:
                return await msg.reply_text("❌ Batch API error")

    if not data.get("success"):
        return await msg.reply_text("❌ No batches")

    txt = "📚 Batches:\n\n"
    for b in data["data"]["batches"]:
        txt += f"{b['id']} → {b['name']}\n"

    await msg.reply_text(txt + "\nBatch ID bhejo")

# EXTRACT
async def extract_batch(msg, batch_id):
    uid = msg.from_user.id
    token = user_data[uid]["token"]

    url = f"https://api.classplusapp.com/v2/course/content/get?courseId={batch_id}"

    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers(token=token)) as r:
            try:
                data = await r.json()
            except:
                return await msg.reply_text("❌ Extract error")

    if not data.get("success"):
        return await msg.reply_text("❌ No content")

    file = f"{batch_id}.txt"

    with open(file, "w", encoding="utf-8") as f:
        for item in data["data"]:
            f.write(f"{item.get('name')} : {item.get('url')}\n")

    await msg.reply_document(file)
    os.remove(file)

# RUN
async def main():
    async with app:
        print("🚀 CP BOT LIVE")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
    
