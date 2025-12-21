# ===============================
# IMPORT
# ===============================
import asyncio
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from urllib.parse import urlparse, parse_qs, urlencode
from bs4 import BeautifulSoup

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import (
    DeletePhotosRequest,
    UploadProfilePhotoRequest
)
from telethon.tl.types import (
    InputPhoto,
    DocumentAttributeAudio
)

# ===============================
# KONFIGURASI
# ===============================
API_ID = 20958475
API_HASH = "1cfb28ef51c138a027786e43a27a8225"

ACCOUNTS = [
    {
        "session": "ISI_SESSION_KAMU",
        "log_channel": -1003402358031,
        "log_admin": 1488611909,
        "features": [
            "anti_view_once",
            "ping",
            "heartbeat",
            "save_media",
            "clearch",
            "whois",
            "downloader",
            "clone",
            "revert",
        ],
    }
]

start_time_global = datetime.now()
clients = []

# ===============================
# REQUEST SESSION (AMAN)
# ===============================
http = requests.Session()
http.headers.update({
    "User-Agent": "Mozilla/5.0"
})

# ===============================
# STORAGE PROFIL PER CLIENT
# ===============================
original_profiles = {}

def get_profile_store(client):
    return original_profiles.setdefault(id(client), {
        "first_name": None,
        "last_name": None,
        "bio": None,
        "photos": []
    })

# ===============================
# ANTI VIEW ONCE
# ===============================
async def anti_view_once_and_ttl(event, client, log_channel, log_admin):
    if not event.is_private:
        return

    msg = event.message
    ttl = getattr(msg.media, "ttl_seconds", None)
    if not msg.media or not ttl:
        return

    try:
        sender = await msg.get_sender()
        caption = (
            "🔓 **MEDIA VIEW-ONCE**\n\n"
            f"👤 {sender.first_name}\n"
            f"🆔 `{sender.id}`\n"
            f"⏱ `{ttl}s`"
        )

        folder = "AntiViewOnce"
        os.makedirs(folder, exist_ok=True)
        file = await msg.download_media(file=folder)

        if log_channel:
            await client.send_file(log_channel, file, caption=caption)
        if log_admin:
            await client.send_file(log_admin, file, caption=caption)

        if file and os.path.exists(file):
            os.remove(file)

    except Exception as e:
        if log_admin:
            await client.send_message(log_admin, f"⚠ {e}")

# ===============================
# PING
# ===============================
async def ping_handler(event, client):
    start = datetime.now()
    msg = await event.reply("Pinging...")
    ms = (datetime.now() - start).microseconds // 1000
    uptime = str(datetime.now() - start_time_global).split(".")[0]

    await msg.edit(
        f"🏓 `{ms}ms`\n"
        f"⏱ `{uptime}`\n"
        f"🕒 {datetime.now(ZoneInfo('Asia/Jakarta')).strftime('%H:%M:%S')}"
    )

# ===============================
# HEARTBEAT
# ===============================
async def heartbeat(client, admin_id, akun):
    while True:
        try:
            await client.send_message(
                admin_id,
                f"✅ **Heartbeat**\n{akun}\n"
                f"{datetime.now(ZoneInfo('Asia/Jakarta')).strftime('%H:%M:%S')}"
            )
        except:
            pass
        await asyncio.sleep(300)

# ===============================
# WHOIS
# ===============================
async def whois_handler(event, client):
    if not event.is_reply:
        await event.reply("❌ Reply user")
        return

    reply = await event.get_reply_message()
    user = await client.get_entity(reply.sender_id)
    full = await client(GetFullUserRequest(user.id))

    text = (
        f"👤 **WHOIS**\n\n"
        f"🆔 `{user.id}`\n"
        f"👥 {user.first_name or ''} {user.last_name or ''}\n"
        f"🔗 @{user.username or '-'}\n"
        f"📖 {full.full_user.about or '-'}"
    )

    photos = await client.get_profile_photos(user.id, limit=5)
    if photos:
        files = [await client.download_media(p) for p in photos]
        await client.send_file(event.chat_id, files, caption=text)
        for f in files:
            os.remove(f)
    else:
        await event.reply(text)

# ===============================
# CLONE
# ===============================
async def clone_handler(event, client):
    if not event.is_reply:
        await event.reply("❌ Reply user")
        return

    store = get_profile_store(client)
    me = await client.get_me()
    full_me = await client(GetFullUserRequest(me.id))

    store["first_name"] = me.first_name
    store["last_name"] = me.last_name
    store["bio"] = full_me.full_user.about
    store["photos"].clear()

    old_photos = await client.get_profile_photos("me", limit=10)
    for p in old_photos:
        f = await client.download_media(p)
        store["photos"].append(f)

    reply = await event.get_reply_message()
    target = await client(GetFullUserRequest(reply.sender_id))

    await client(UpdateProfileRequest(
        first_name=target.user.first_name,
        last_name=target.user.last_name,
        about=target.full_user.about
    ))

    if old_photos:
        await client(DeletePhotosRequest([
            InputPhoto(p.id, p.access_hash, p.file_reference)
            for p in old_photos
        ]))

    target_photos = list(reversed(
        await client.get_profile_photos(reply.sender_id, limit=10)
    ))

    for tp in target_photos:
        f = await client.download_media(tp)
        up = await client.upload_file(f)
        await client(UploadProfilePhotoRequest(file=up))
        os.remove(f)

    await event.reply("✅ Clone selesai")

# ===============================
# REVERT
# ===============================
async def revert_handler(event, client):
    store = get_profile_store(client)
    if not store["first_name"]:
        await event.reply("❌ Tidak ada data")
        return

    await client(UpdateProfileRequest(
        first_name=store["first_name"],
        last_name=store["last_name"],
        about=store["bio"] or ""
    ))

    cur = await client.get_profile_photos("me")
    if cur:
        await client(DeletePhotosRequest([
            InputPhoto(p.id, p.access_hash, p.file_reference)
            for p in cur
        ]))

    for f in store["photos"]:
        up = await client.upload_file(f)
        await client(UploadProfilePhotoRequest(file=up))
        os.remove(f)

    store["photos"].clear()
    await event.reply("✅ Revert sukses")

# ===============================
# REGISTER HANDLERS (ANTI CLOSURE BUG)
# ===============================
def register_handlers(client, acc, akun_nama):

    if "anti_view_once" in acc["features"]:
        @client.on(events.NewMessage(incoming=True))
        async def _(e):
            await anti_view_once_and_ttl(
                e, client, acc["log_channel"], acc["log_admin"]
            )

    if "ping" in acc["features"]:
        @client.on(events.NewMessage(pattern="^/ping$"))
        async def _(e):
            await ping_handler(e, client)

    if "whois" in acc["features"]:
        @client.on(events.NewMessage(pattern="^/whois$"))
        async def _(e):
            await whois_handler(e, client)

    if "clone" in acc["features"]:
        @client.on(events.NewMessage(pattern="^/clone$"))
        async def _(e):
            await clone_handler(e, client)

    if "revert" in acc["features"]:
        @client.on(events.NewMessage(pattern="^/revert$"))
        async def _(e):
            await revert_handler(e, client)

    if "heartbeat" in acc["features"] and acc["log_admin"]:
        asyncio.create_task(
            heartbeat(client, acc["log_admin"], akun_nama)
        )

# ===============================
# MAIN
# ===============================
async def main():
    for i, acc in enumerate(ACCOUNTS, 1):
        client = TelegramClient(
            StringSession(acc["session"]),
            API_ID,
            API_HASH,
            connection_retries=3,
            retry_delay=2,
            timeout=10
        )

        await client.start()
        akun = f"Akun {i}"

        register_handlers(client, acc, akun)

        if acc["log_admin"]:
            await client.send_message(
                acc["log_admin"],
                f"♻️ **Ubot Online**\n{akun}\n"
                f"{datetime.now(ZoneInfo('Asia/Jakarta')).strftime('%H:%M:%S')}"
            )

        clients.append(client)

    await asyncio.gather(
        *(c.run_until_disconnected() for c in clients)
    )

# ===============================
# ENTRY POINT (AMAN)
# ===============================
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(main())
