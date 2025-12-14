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
from datetime import datetime
from zoneinfo import ZoneInfo


# === KONFIGURASI ===
API_ID = 20958475
API_HASH = '1cfb28ef51c138a027786e43a27a8225'

# Daftar akun
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

# Buat client list
clients = []
for acc in ACCOUNTS:
    client = TelegramClient(StringSession(acc["session"]), API_ID, API_HASH)
    clients.append((client, acc.get("log_channel"), acc.get("log_admin")))

# === ANTI VIEW-ONCE ===
async def anti_view_once_and_ttl(event, client, log_channel, log_admin):
    if not event.is_private:
        return

    msg = event.message
    ttl = getattr(msg.media, "ttl_seconds", None)
    if not msg.media or not ttl:
        return

    try:
        sender = await msg.get_sender()
        sender_name = sender.first_name or "Unknown"
        sender_username = f"@{sender.username}" if sender.username else "-"
        sender_id = sender.id

        chat = await event.get_chat()
        chat_title = getattr(chat, "title", "Private Chat")
        chat_id = chat.id

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

        folder = "111AntiViewOnce"
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
            await client.send_message(log_admin, f"⚠ Error anti-viewonce: `{e}`")

# Attach handler anti view-once
for client, log_channel, log_admin in clients:
    @client.on(events.NewMessage(incoming=True))
    async def handler(event, c=client, lc=log_channel, la=log_admin):
        await anti_view_once_and_ttl(event, c, lc, la)



# ✅✅✅ === FITUR BARU: AUTO FORWARD 10X (WORD BOUNDARY MATCH) === ✅✅✅

TRIGGER_LIST = [
    "bebih",
    "babe",
    "baby",
]

async def auto_forward_spam(event, client):
    if not event.is_private:
        return

    msg = event.message.message.lower().strip()

    # cek kata utuh (word boundary)
    for trigger in TRIGGER_LIST:
        pattern = rf"\b{re.escape(trigger)}\b"
        if re.search(pattern, msg):
            sender = await event.get_sender()
            sender_id = sender.id

            for _ in range(10):
                try:
                    await client.forward_messages(sender_id, event.message)
                    await asyncio.sleep(0.3)
                except Exception as e:
                    print(f"Error forward: {e}")
                    break
            break

# Attach handler fitur baru
for client, log_channel, log_admin in clients:
    @client.on(events.NewMessage(incoming=True))
    async def spam_handler(event, c=client):
        await auto_forward_spam(event, c)



# === /PING LENGKAP ===
start_time_global = datetime.now()

for client, log_channel, log_admin in clients:
    @client.on(events.NewMessage(pattern=r"^/ping$"))
    async def ping(event, c=client):
        if not event.is_private:   # ✅ Tambahan filter hanya di handler ping
            return
        try:
            start = datetime.now()
            msg = await event.reply("Pinging...")
            end = datetime.now()
            ms = (end - start).microseconds // 1000

            uptime = datetime.now() - start_time_global
            uptime_str = str(uptime).split('.')[0]

            me = await c.get_me()
            akun_nama = me.first_name or "Akun"

            text = (
                f"🏓 **Pong!** `{ms}ms`\n\n"
                f"👤 **Akun:** {akun_nama}\n"
                f"⏱ **Uptime:** `{uptime_str}`\n"
                f"📡 **Status:** Online\n"
                f"🕒 **Server:** {datetime.now(ZoneInfo('Asia/Jakarta')).strftime('%H:%M:%S')}"
            )

            await msg.edit(text)
        except Exception as e:
            await event.reply(f"⚠ Error /ping: `{e}`")

# === HEARTBEAT ===
async def heartbeat(client, log_admin, log_channel, akun_nama):
    last_msg_id = None
    start_time = datetime.now()

    while True:
        try:
            uptime = datetime.now() - start_time
            uptime_str = str(uptime).split('.')[0]

            if last_msg_id:
                try:
                    if log_admin:
                        await client.delete_messages(log_admin, last_msg_id)
                except:
                    pass

            text = (
                f"✅ **Heartbeat Aktif**\n"
                f"👤 {akun_nama}\n"
                f"⏱ Uptime: `{uptime_str}`\n"
                f"🕒 {datetime.now(ZoneInfo('Asia/Jakarta')).strftime('%H:%M:%S')}"
            )

            msg = None
            if log_admin:
                msg = await client.send_message(log_admin, text)

            if msg:
                last_msg_id = msg.id

        except Exception as e:
            err = f"⚠ Heartbeat Error: `{e}`"
            if log_admin:
                await client.send_message(log_admin, err)

        await asyncio.sleep(300)

# === RAILWAY WEB SERVER ===
app = Flask('')

@app.route('/')
def home():
    return "Ubot aktif di Railway!", 200

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# === AUTO RESTART LOOP ===
async def run_clients_forever():
    while True:
        tasks = []
        for client, _, _ in clients:
            tasks.append(asyncio.create_task(client.run_until_disconnected()))

        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        print("⚠ Client disconnect, restart 5 detik...")
        await asyncio.sleep(5)

# === MAIN ===
async def main():
    keep_alive()

    for client, _, _ in clients:
        await client.start()

    for index, (client, log_channel, log_admin) in enumerate(clients, start=1):
        akun_nama = f"Akun {index}"
        text = (
            f"♻️ **Ubot Restart (Railway)**\n"
            f"👤 {akun_nama}\n"
            f"🕒 Waktu: {datetime.now(ZoneInfo('Asia/Jakarta')).strftime('%H:%M:%S || %d-%m-%Y')}"
        )
        if log_admin:
            await client.send_message(log_admin, text)

    for index, (client, log_channel, log_admin) in enumerate(clients, start=1):
        asyncio.create_task(heartbeat(client, log_admin, log_channel, f"Akun {index}"))

    print(f"✅ Ubot aktif dengan {len(clients)} akun.")

    await run_clients_forever()

asyncio.run(main())
