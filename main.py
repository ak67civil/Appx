import os
import aiohttp
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("universal-pro-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }

# -------- START --------
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("🔥 Universal Extractor Bot Ready!\n\n/login se start karo")

# -------- LOGIN --------
@app.on_message(filters.command("login"))
async def login(client, message):
    user_data[message.from_user.id] = {"step": "api"}
    await message.reply_text("🔗 API URL bhejo\nExample:\nhttps://api.appx.co.in")

# -------- AUTO DETECT FUNCTION --------
def extract_courses(json_data):
    if isinstance(json_data, list):
        return json_data
    return (
        json_data.get("data")
        or json_data.get("courses")
        or json_data.get("result")
        or []
    )

def extract_folders(json_data):
    if isinstance(json_data, list):
        return json_data
    return (
        json_data.get("data")
        or json_data.get("folders")
        or json_data.get("sections")
        or []
    )

# -------- HANDLER --------
@app.on_message(filters.private & ~filters.command(["start", "login"]))
async def handler(client, message):
    user_id = message.from_user.id

    if user_id not in user_data:
        return

    step = user_data[user_id]["step"]
    text = message.text.strip()

    # STEP 1: API
    if step == "api":
        user_data[user_id]["api"] = text.rstrip("/")
        user_data[user_id]["step"] = "token"
        await message.reply_text("🔑 Token bhejo (Bearer token)")

    # STEP 2: TOKEN
    elif step == "token":
        token = text.replace("Bearer ", "").strip()
        api = user_data[user_id]["api"]

        msg = await message.reply_text("📡 Courses fetch ho rahe hai...")

        endpoints = [
            "/v1/course/purchased",
            "/course/purchased",
            "/my-courses",
            "/user/courses"
        ]

        data = None

        try:
            async with aiohttp.ClientSession() as session:
                for ep in endpoints:
                    try:
                        async with session.get(api + ep, headers=get_headers(token)) as res:

                            # Ignore HTML
                            if "application/json" not in res.headers.get("Content-Type", ""):
                                continue

                            json_data = await res.json()

                            courses = extract_courses(json_data)

                            if courses:
                                data = courses
                                break

                    except:
                        continue

            if not data:
                return await msg.edit("❌ API ya token invalid ya unsupported")

            user_data[user_id]["token"] = token
            user_data[user_id]["step"] = "course"

            text_msg = "📚 Batches:\n\n"

            for c in data:
                cid = c.get("id") or c.get("_id") or "N/A"
                title = c.get("title") or c.get("name") or "No Name"
                text_msg += f"{cid} → {title}\n"

            await msg.edit(text_msg + "\n\n👉 Batch ID bhejo")

        except Exception as e:
            await msg.edit(f"⚠️ Error: {e}")

    # STEP 3: COURSE EXTRACT
    elif step == "course":
        course_id = text
        api = user_data[user_id]["api"]
        token = user_data[user_id]["token"]

        msg = await message.reply_text("⏳ Extract ho raha hai...")

        endpoints = [
            f"/v1/course/content/{course_id}",
            f"/course/content/{course_id}",
            f"/course/{course_id}"
        ]

        data = None

        try:
            async with aiohttp.ClientSession() as session:
                for ep in endpoints:
                    try:
                        async with session.get(api + ep, headers=get_headers(token)) as res:

                            if "application/json" not in res.headers.get("Content-Type", ""):
                                continue

                            json_data = await res.json()

                            folders = extract_folders(json_data)

                            if folders:
                                data = folders
                                break

                    except:
                        continue

            if not data:
                return await msg.edit("❌ Course fetch failed")

            file = f"{course_id}.txt"

            with open(file, "w", encoding="utf-8") as f:
                for folder in data:
                    title = folder.get("title") or folder.get("name") or "Folder"
                    f.write(f"\n📁 {title}\n")

                    videos = folder.get("videos") or folder.get("contents") or []
                    for v in videos:
                        v_title = v.get("title") or v.get("name")
                        v_url = v.get("url") or v.get("video_url")
                        if v_url:
                            f.write(f"{v_title} : {v_url}\n")

                    notes = folder.get("notes") or folder.get("pdfs") or []
                    for pdf in notes:
                        p_title = pdf.get("title") or pdf.get("name")
                        p_url = pdf.get("url")
                        if p_url:
                            f.write(f"{p_title} : {p_url}\n")

                    tests = folder.get("tests") or []
                    for t in tests:
                        t_title = t.get("title") or t.get("name")
                        t_url = t.get("url")
                        if t_url:
                            f.write(f"{t_title} : {t_url}\n")

            await message.reply_document(file, caption="✅ Extraction Complete")
            os.remove(file)

            await msg.delete()
            del user_data[user_id]

        except Exception as e:
            await msg.edit(f"⚠️ Error: {e}")

# -------- RUN --------
print("🚀 BOT RUNNING...")
app.run()
