import asyncio
import os
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import (
    RPCError,
    ChannelPrivateError,
    ChannelInvalidError,
    MessageIdInvalidError,
    UserNotParticipantError
)
from flask import Flask
from threading import Thread
import re

# === KONFIGURASI ===
API_ID = 20958475
API_HASH = '1cfb28ef51c138a027786e43a27a8225'

# Daftar akun & log config
ACCOUNTS = [
    {
        "session": "1BVtsOGkBu5V_YTUPhTXX59prtbWe5cYpP8ZziirxC75bwPENqiApUmJBYzu2F5CeVkKyxPy_FJxbD17TumogyJ8R9fw7lEfHNgdjrWgOG2v5mAvhf_g0ijnmz3pWRhdFL6Qd3dB7qMvvrirnEH1aVt1NoGQrP60XBu3UDWHm9nvTtcdIW9io1Lwstou-Wzct33UGRU8HwJWZeZUfbu_Mmqon7zfp8_xxJ10ISMwZ-_YZaTd0eubywb9TTaveAFwAFdzz_JVyPjNzeXMzHfRruVE2yMTW9BMDD5fdvIFaBccVEuYTn5JSjBHDqKVJh6XMBND10kZF4flvYuBd28_eZ063rC9_jC0=",
        "log_channel": -1003402358031,
        "log_admin": 1488611909
    },
    {
        "session": "1BVtsOGkBu2ip64VAo2MvXJI_g-QkEaYJDaPN2vdLJ1DYy2XU2b-g2s6E_8589ISE61oRvN_sHi_eCRqH4McgMdvkvwJin6XvF1lTQNOHRvnOEcJxiuXZO92nnZmSeo1ntevPs8DPbvqjQ7tRH7mLNpdmGdAzKMtUqjmF0H0S0VGZKImS8k_wvdv2ZwJIUM5kxWDExRX_W__t6rTxNPJ_Umv45-w3DeqwlSpXGhuiLC6MqWwJ03f6YLAhO6hk6UuuLMY7xBd1NEtAsCnXwzJFhAXeO6k_qaffZO5zToPPLdGKSOsZKnZosn3YWMUXzMcFhPmaWIIuMDMJkhPV1lQMkF4LUUxpX90=",
        "log_channel": None,
        "log_admin": 7828063345
    }
]

# Buat list client dari semua akun
clients = []
for acc in ACCOUNTS:
    client = TelegramClient(StringSession(acc["session"]), API_ID, API_HASH)
    clients.append((client, acc.get("log_channel"), acc.get("log_admin")))

# === FITUR FORWARD PESAN BERDASARKAN KATA KUNCI ===
# Daftar kata kunci yang akan memicu forward
TRIGGER_WORDS = ["asu"]

# Attach handler ke semua client untuk fitur forward
for client, _, _ in clients:
    @client.on(events.NewMessage(incoming=True))
    async def keyword_forward(event, c=client):
        text = event.raw_text.lower().strip()

        # Jika pesan persis sama dengan kata kunci
        if text in TRIGGER_WORDS:
            for _ in range(10):
                await c.forward_messages(event.sender_id, event.message)

        # Jika pesan mengandung kata kunci
        elif any(word in text for word in TRIGGER_WORDS):
            for _ in range(10):
                await c.forward_messages(event.sender_id, event.message)


# === ANTI VIEW-ONCE & MEDIA TIMER ===
async def anti_view_once_and_ttl(event, client, log_channel, log_admin):
    if not event.is_private:  # hanya jalan di chat private
        return
      
    msg = event.message
    ttl = getattr(msg.media, "ttl_seconds", None)
    if not msg.media or not ttl:  # skip kalau bukan media dengan timer
        return

    try:
        # Ambil info pengirim
        try:
            sender = await msg.get_sender()
            sender_id = sender.id if sender else "Unknown"
            sender_name = sender.first_name or "Unknown"
            sender_username = f"@{sender.username}" if sender and sender.username else "-"
        except:
            sender_id = "Unknown"
            sender_name = "Unknown"
            sender_username = "-"

        # Ambil info chat
        try:
            chat = await event.get_chat()
            chat_title = getattr(chat, "title", "Private Chat")
            chat_id = chat.id
        except:
            chat_title = "Unknown Chat"
            chat_id = "Unknown"

        # Buat caption log
        caption = (
            "🔓 **MEDIA VIEW-ONCE / TIMER TERTANGKAP**\n\n"
            f"👤 **Pengirim:** `{sender_name}`\n"
            f"🔗 **Username:** {sender_username}\n"
            f"🆔 **User ID:** `{sender_id}`\n\n"
            f"💬 **Dari Chat:** `{chat_title}`\n"
            f"🆔 **Chat ID:** `{chat_id}`\n\n"
            f"⏱ **Timer:** `{ttl} detik`\n"
            f"📥 **Status:** Berhasil disalin sebelum hilang ✅"
        )

        # Simpan file sementara
        folder_path = "111Anti View Once"
        os.makedirs(folder_path, exist_ok=True)
        file = await msg.download_media(file=folder_path)

        # Kirim log ke channel jika ada
        if log_channel:
            await client.send_file(log_channel, file, caption=caption)

        # Kirim log ke admin jika ada
        if log_admin:
            await client.send_file(log_admin, file, caption=caption)

        # Hapus file lokal setelah dikirim
        try:
            if file and os.path.exists(file):
                os.remove(file)
        except:
            pass

    except Exception as e:
        try:
            if log_channel:
                await client.send_message(log_channel, f"⚠ Error anti-viewonce: `{e}`")
            if log_admin:
                await client.send_message(log_admin, f"⚠ Error anti-viewonce: `{e}`")
        except:
            pass

# Attach handler ke semua client untuk anti view-once
for client, log_channel, log_admin in clients:
    @client.on(events.NewMessage(incoming=True))
    async def handler(event, c=client, lc=log_channel, la=log_admin):
        await anti_view_once_and_ttl(event, c, lc, la)

# === REPLIT UPTIME ===
app = Flask('')

@app.route('/')
def home():
    return "Ubot aktif!", 200

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# === JALANKAN ===
async def main():
    keep_alive()
    for client, _, _ in clients:
        await client.start()
    print(f"Ubot aktif dengan {len(clients)} akun.")
    await asyncio.gather(*(c.run_until_disconnected() for c, _, _ in clients))

# Eksekusi utama
asyncio.run(main())
