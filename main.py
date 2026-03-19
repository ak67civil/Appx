import os
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

# Heroku Config
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("classplus-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

def get_headers(api_key="877665"): # Common CP API Key
    return {
        "api-key": api_key,
        "device-id": "android_123456",
        "Content-Type": "application/json",
        "User-Agent": "Mobile-Android"
    }

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("🎓 **ClassPlus Multi-Batch Extractor**\n\nLogin ke liye `/cp_login` dabbao.")

@app.on_message(filters.command("cp_login"))
async def cp_login(client, message):
    user_id = message.from_user.id
    user_data[user_id] = {"step": "org_code"}
    await message.reply_text("🏢 **STEP 1:** Org Code bhejo (e.g., `abcd`)")

@app.on_message(filters.private & ~filters.command(["start", "cp_login"]))
async def handle_cp_steps(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data: return
    
    step = user_data[user_id].get("step")
    text = message.text.strip()

    # STEP 1: Org Code
    if step == "org_code":
        user_data[user_id]["org"] = text.upper()
        user_data[user_id]["step"] = "phone"
        await message.reply_text(f"✅ Org Code: `{text.upper()}`\n\n📱 **STEP 2:** Phone Number bhejo (91XXXXXXXXXX)")

    # STEP 2: Send OTP
    elif step == "phone":
        user_data[user_id]["phone"] = text
        m = await message.reply_text("📩 OTP bhej raha hoon...")
        
        url = f"https://api.classplusapp.com/v2/otp/generate?mobileNumber={text}&orgCode={user_data[user_id]['org']}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=get_headers()) as r:
                res = await r.json()
        
        if res.get("success"):
            user_data[user_id]["step"] = "otp_verify"
            user_data[user_id]["session_id"] = res['data']['sessionId']
            await m.edit("✅ OTP bhej diya! Ab **OTP bhejo**.")
        else:
            await m.edit(f"❌ Error: {res.get('message', 'Failed to send OTP')}")

    # STEP 3: Verify OTP & Get Token
    elif step == "otp_verify":
        m = await message.reply_text("🔄 Verify kar raha hoon...")
        payload = {
            "otp": text,
            "mobileNumber": user_data[user_id]["phone"],
            "sessionId": user_data[user_id]["session_id"],
            "orgCode": user_data[user_id]["org"]
        }
        
        url = "https://api.classplusapp.com/v2/otp/verify"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=get_headers()) as r:
                res = await r.json()
        
        if res.get("success"):
            token = res['data']['token']
            user_data[user_id]["token"] = token
            await m.edit(f"✅ **Login Success!**\n🔑 Token: `{token}`\n\n📚 Batches fetch kar raha hoon...")
            await fetch_cp_batches(message, token)
        else:
            await m.edit("❌ Galat OTP! Phir se try karo.")

async def fetch_cp_batches(message, token):
    headers = get_headers()
    headers["x-access-token"] = token
    url = "https://api.classplusapp.com/v2/batches/list"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            res = await r.json()
            
    if res.get("success"):
        batches = res['data']['batches']
        text = "📚 **Your Batches:**\n\n"
        for b in batches:
            text += f"🆔 `{b['id']}` → **{b['name']}**\n"
        await message.reply_text(text + "\n👉 **Batch ID bhejo content nikalne ke liye!**")
    else:
        await message.reply_text("📭 Koi batches nahi mile.")

# Startup Fix for Python 3.14
async def main():
    async with app:
        print("🚀 CLASSPLUS BOT ONLINE!")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
    
