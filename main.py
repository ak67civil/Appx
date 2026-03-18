import os
import requests
from pyrogram import Client, filters

# Configs
API_ID = int(os.environ.get("API_ID", "33401543"))
API_HASH = os.environ.get("API_HASH", "7cdea5bbc8bd991b4a49807ce86")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client(
    "AppxMaster",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def get_headers(token=None):
    headers = {
        "x-app-id": "12345", # Sandeep Jyani App ID (Change if needed)
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Linux; Android 11)"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("💪 **Dekh Bhai, Tera Bot Zinda Ho Gaya!**\n\nAb commands use kar sakta hai.")

@app.on_message(filters.command("appx_p"))
async def purchase_batch(client, message):
    if len(message.command) < 3:
        return await message.reply_text("❌ Format: `/appx_p [ID] [Token]`")
    
    course_id, token = message.command[1], message.command[2]
    m = await message.reply_text("📥 Purchased links nikal raha hoon...")
    
    url = f"https://api.appx.co.in/v1/course/content/{course_id}"
    try:
        res = requests.get(url, headers=get_headers(token)).json()
        if res.get("success"):
            file_name = f"Appx_Batch_{course_id}.txt"
            with open(file_name, "w") as f:
                for folder in res['data']:
                    f.write(f"📁 {folder['title']}\n")
                    for video in folder.get('videos', []):
                        f.write(f"{video['title']}: {video['url']}\n")
            
            await app.send_document(message.chat.id, file_name, caption=f"✅ {course_id} TXT Generated!")
            os.remove(file_name)
            await m.delete()
        else:
            await m.edit("❌ Failed! Token check karo.")
    except Exception as e:
        await m.edit(f"⚠️ Error: {str(e)}")

# Sabse simple tareeka jo crash nahi hota:
if __name__ == "__main__":
    print("🚀 BOT STARTING...")
    app.run()
    
