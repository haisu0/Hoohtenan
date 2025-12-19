# ========== BAGIAN 1 ==========
# IMPORT, KONFIG, ACCOUNTS, SETUP DASAR

import asyncio
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from telethon import TelegramClient, events, types
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread
from telethon.tl.functions.users import GetFullUserRequest

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode

# === KONFIGURASI UTAMA ===
API_ID = 20958475
API_HASH = '1cfb28ef51c138a027786e43a27a8225'

# === DAFTAR AKUN ===
ACCOUNTS = [
    {
        "session": "ISI_SESSION_KAMU",
        "log_channel": -1003402358031,
        "log_admin": 1488611909,
        "features": [
            "downloader",
        ],
    }
]

clients = []
start_time_global = datetime.now()

# =========================================================
# ===================== DOWNLOADER ========================
# =========================================================

URL_REGEX = re.compile(r'(https?://[^\s]+)', re.IGNORECASE)

PLATFORM_PATTERNS = {
    'tiktok': re.compile(r'tiktok\.com', re.I),
    'instagram': re.compile(r'instagram\.com|instagr\.am', re.I),
}

def sanitize_url(url):
    try:
        parsed = urlparse(url)
        q = parse_qs(parsed.query)
        for k in ["utm_source", "utm_medium", "utm_campaign", "fbclid", "gclid"]:
            q.pop(k, None)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}" + (
            f"?{urlencode(q, doseq=True)}" if q else ""
        )
    except:
        return url

def detect_platform(url):
    for p, r in PLATFORM_PATTERNS.items():
        if r.search(url):
            return p
    return None

# ================= TIKTOK =================
async def download_tiktok(url):
    try:
        res = requests.post(
            "https://www.tikwm.com/api/",
            params={"url": url, "hd": 1},
            timeout=15
        ).json()["data"]

        return {
            "success": True,
            "platform": "tiktok",
            "type": "images" if res.get("images") else "video",
            "video": {
                "hd": res.get("hdplay"),
                "nowm": res.get("play"),
                "wm": res.get("wmplay"),
            },
            "images": res.get("images", []),
            "title": res.get("title", ""),
            "author": res.get("author", {}).get("unique_id", ""),
            "music": res.get("music")
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

# ================= INSTAGRAM =================
async def download_instagram(url):
    try:
        html = requests.post(
            "https://yt1s.io/api/ajaxSearch",
            data={"q": url, "lang": "en"},
            timeout=15
        ).json()["data"]

        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a", href=True)

        media = []
        for a in links:
            h = a["href"]
            if h.startswith("http"):
                media.append({
                    "url": h,
                    "type": "video" if ".mp4" in h else "image"
                })

        return {"success": True, "platform": "instagram", "media": media}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ================= SEND RESULT =================
async def send_result(client, target_chat, result):
    if result["platform"] == "tiktok":
        if result["type"] == "video":
            url = result["video"]["hd"] or result["video"]["nowm"]
            await client.send_file(target_chat, url,
                caption=f"🎵 TikTok\n👤 @{result['author']}\n📝 {result['title']}"
            )
        else:
            await client.send_file(
                target_chat,
                result["images"],
                caption=f"🖼 TikTok Slideshow\n👤 @{result['author']}"
            )

    elif result["platform"] == "instagram":
        for m in result["media"]:
            await client.send_file(target_chat, m["url"])

# ================= SINGLE JOB =================
async def handle_single_download(client, target_chat, url):
    clean = sanitize_url(url)
    platform = detect_platform(clean)

    if platform == "tiktok":
        result = await download_tiktok(clean)
    elif platform == "instagram":
        result = await download_instagram(clean)
    else:
        await client.send_message(target_chat, f"❌ Tidak didukung:\n{clean}")
        return

    if not result["success"]:
        await client.send_message(target_chat, f"❌ Gagal:\n{clean}")
        return

    await send_result(client, target_chat, result)

# ================= COMMAND HANDLER =================
async def handle_downloader(event, client):
    if not event.is_private:
        return

    me = await client.get_me()
    if event.sender_id != me.id:
        return

    text = event.pattern_match.group(2).strip() if event.pattern_match.group(2) else ""
    reply = await event.get_reply_message() if event.is_reply else None

    target_chat = event.chat_id
    links_part = text

    # MODE: /d 123456789
    if re.fullmatch(r'-?\d+|@[\w_]+', text):
        target_chat = int(text) if text.lstrip("-").isdigit() else text
        if reply and reply.message:
            links_part = reply.message
        else:
            await event.reply("❌ Harus reply pesan berisi link.")
            return

    if not links_part and reply:
        links_part = reply.message

    urls = URL_REGEX.findall(links_part or "")
    if not urls:
        await event.reply("❌ Tidak ada link.")
        return

    loading = await event.reply(f"⏳ Memproses {len(urls)} link...")

    for url in urls:
        await handle_single_download(client, target_chat, url)

    await loading.delete()

# =========================================================
# ======================= MAIN ============================
# =========================================================

async def main():
    for acc in ACCOUNTS:
        client = TelegramClient(StringSession(acc["session"]), API_ID, API_HASH)
        await client.start()

        if "downloader" in acc["features"]:
            @client.on(events.NewMessage(pattern=r'^/(d|download)(?:\s+|$)(.*)'))
            async def _(e, c=client):
                await handle_downloader(e, c)

        clients.append(client)

    await asyncio.gather(*(c.run_until_disconnected() for c in clients))

asyncio.run(main())
