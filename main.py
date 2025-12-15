import asyncio
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# === KONFIGURASI ===
API_ID = 20958475
API_HASH = '1cfb28ef51c138a027786e43a27a8225'

# Daftar akun dengan fitur masing-masing
ACCOUNTS = [
    {
        "session": "1BVtsOIIBu4Z0S11NsMdWP8Ua-p8C4gFEBAyD0TGmshXRvGQNBYavPrKNFgcEXWz-sDT_w9HLML-9nMrSWTqAAfqvx4Y6157p30Gqy09ViCrgzKyfo7IEdhK7Tqnjlt5lSYwuhfalN4R4GtgjBoY7FQBH7EIYozqwxFp8U93PYdsqWKQdG_bhBqZ2I02dqOqOqc_feGpBFrTwLPLld_tPjIuvBk02zgUGV3E3vYdmdGx8gPFveGbSLLHJdHoFH-E-K_paygXWXVjFopilIAKl9fuw36Wjrd-ijV0OpRIfEEff3sH8jFoGQfdthUaZiLlcr4V373-eeh-LOAc8W-CxBhKDfDne0P0=",
        "log_channel": -1003402358031,
        "log_admin": 1488611909,
        "features": [
            "anti_view_once",
            "ping",
            "heartbeat",
            "scheduled_message",
            "spam_forward",
            "save_media"
        ],
        "scheduled_targets": [
            {"chat_id": 7828063345, "text_pagi": "☀️ Gut Pagi 🌄 🌅", "text_malam": "🌑 🌕 Gut Malam 🌌"}
        ],
        "spam_triggers": ["bebih", "babe", "baby"]
    },
    {
        "session": "1BVtsOGkBu2ip64VAo2MvXJI_g-QkEaYJDaPN2vdLJ1DYy2XU2b-g2s6E_8589ISE61oRvN_sHi_eCRqH4McgMdvkvwJin6XvF1lTQNOHRvnOEcJxiuXZO92nnZmSeo1ntevPs8DPbvqjQ7tRH7mLNpdmGdAzKMtUqjmF0H0S0VGZKImS8k_wvdv2ZwJIUM5kxWDExRX_W__t6rTxNPJ_Umv45-w3DeqwlSpXGhuiLC6MqWwJ03f6YLAhO6hk6UuuLMY7xBd1NEtAsCnXwzJFhAXeO6k_qaffZO5zToPPLdGKSOsZKnZosn3YWMUXzMcFhPmaWIIuMDMJkhPV1lQMkF4LUUxpX90=",
        "log_channel": None,
        "log_admin": 7828063345,
        "features": [
            "anti_view_once",
            "ping",
            "heartbeat",
            "scheduled_message",
        ],
        "scheduled_targets": [
            {"chat_id": 1488611909, "text_pagi": "☀️ Selamat Pagi 🌄 🌅", "text_malam": "🌑 🌕 Selamat Malam 🌌"}
        ],
        "spam_triggers": None
    }
]

clients = []

# === FITUR: ANTI VIEW-ONCE ===
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
            f"📥 **Status:** Berhasil disalin ✅"
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


# === FITUR: AUTO FORWARD SPAM ===
async def auto_forward_spam(event, client, triggers):
    if not event.is_private or not triggers:
        return
    msg = event.message.message.lower().strip()
    for trigger in triggers:
        pattern = rf"\b{re.escape(trigger)}\b"
        if re.search(pattern, msg):
            sender = await event.get_sender()
            sender_id = sender.id
            for _ in range(10):
                try:
                    await client.forward_messages(sender_id, event.message)
                    await asyncio.sleep(0.3)
                except:
                    break
            break


# === FITUR: PING ===
start_time_global = datetime.now()

async def ping_handler(event, client):
    if not event.is_private:
        return
    try:
        start = datetime.now()
        msg = await event.reply("Pinging...")
        end = datetime.now()
        ms = (end - start).microseconds // 1000
        uptime = datetime.now() - start_time_global
        uptime_str = str(uptime).split('.')[0]
        me = await client.get_me()
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


# === FITUR: HEARTBEAT ===
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
            if log_admin:
                await client.send_message(log_admin, f"⚠ Heartbeat Error: `{e}`")

        await asyncio.sleep(300)


# === FITUR: SCHEDULED MESSAGE ===
async def scheduled_message(client, targets, akun_nama):
    last_sent_date_pagi = None
    last_sent_date_malam = None

    while True:
        now = datetime.now(ZoneInfo("Asia/Jakarta"))
        today = now.date()

        if now.hour == 6 and now.minute == 0:
            if last_sent_date_pagi != today:
                for target in targets:
                    try:
                        await client.send_message(target["chat_id"], target["text_pagi"])
                    except:
                        pass
                last_sent_date_pagi = today

        if now.hour == 22 and now.minute == 0:
            if last_sent_date_malam != today:
                for target in targets:
                    try:
                        await client.send_message(target["chat_id"], target["text_malam"])
                    except:
                        pass
                last_sent_date_malam = today

        await asyncio.sleep(20)


# === FITUR SAVE MEDIA ===

link_regex = re.compile(
    r'(?:https?://)?t\.me/(c/\d+|[a-zA-Z0-9_]+)/(\d+)(?:\?.*?)?',
    re.IGNORECASE
)

async def process_link(event, client, chat_part, msg_id, target_chat=None):
    if not event.is_private:
        return
    
    me = await client.get_me()
    if event.sender_id != me.id:
        return
    
    from telethon.errors import (
        RPCError,
        ChannelPrivateError,
        ChannelInvalidError,
        MessageIdInvalidError,
        UserNotParticipantError
    )

    try:
        if chat_part.startswith("c/"):
            internal_id = chat_part[2:]
            chat_id = int(f"-100{internal_id}")
            try:
                await client.get_permissions(chat_id, 'me')
            except:
                await event.reply(f"🚫 Ubot belum join channel `{chat_part}`.")
                return
        else:
            try:
                entity = await client.get_entity(chat_part)
                chat_id = entity.id
            except:
                await event.reply(f"❌ Channel/grup `{chat_part}` tidak ditemukan.")
                return

        message = await client.get_messages(chat_id, ids=msg_id)
        if not message:
            await event.reply(f"❌ Pesan {msg_id} tidak ditemukan.")
            return

        send_to = target_chat or event.chat_id

        grouped_id = message.grouped_id
        if grouped_id:
            all_msgs = await client.get_messages(chat_id, limit=200)
            same_group = [m for m in all_msgs if m.grouped_id == grouped_id]
            same_group.sort(key=lambda m: m.id)

            files = []
            first_caption = None
            first_buttons = None

            for m in same_group:
                if first_caption is None and (m.message or m.raw_text):
                    first_caption = m.message or m.raw_text

                if first_buttons is None:
                    first_buttons = getattr(m, "buttons", None)

                if m.media:
                    fpath = await client.download_media(m.media)
                    files.append(fpath)
                else:
                    if m.message:
                        await client.send_message(send_to, m.message)

            if files:
                await client.send_file(
                    send_to,
                    files,
                    caption=first_caption or "",
                    buttons=first_buttons,
                    link_preview=False
                )
                for f in files:
                    try:
                        os.remove(f)
                    except:
                        pass

        else:
            buttons = getattr(message, "buttons", None)
            text = message.message or ""

            if message.media:
                fpath = await client.download_media(message.media)
                await client.send_file(
                    send_to,
                    fpath,
                    caption=text,
                    buttons=buttons,
                    link_preview=False
                )
                try:
                    os.remove(fpath)
                except:
                    pass
            else:
                await client.send_message(send_to, text, buttons=buttons)

    except Exception as e:
        await event.reply(f"🚨 Error: `{e}`")


async def handle_save_command(event, client):
    if not event.is_private:
        return
    
    me = await client.get_me()
    if event.sender_id != me.id:
        return
        
    input_text = event.pattern_match.group(2).strip()

    if not input_text:
        if event.is_reply:
            reply = await event.get_reply_message()
            if reply and reply.message:
                input_text = reply.message.strip()
            else:
                await event.reply("❌ Pesan balasan tidak berisi teks.")
                return
        else:
            await event.reply("❌ Kirim link seperti `https://t.me/c/xxx/yyy`.")
            return

    parts = input_text.split(maxsplit=1)
    target_chat_raw = None
    links_part = input_text

    if len(parts) == 2:
        possible_target = parts[0]
        if re.match(r'^@?[a-zA-Z0-9_]+$', possible_target) or re.match(r'^-?\d+$', possible_target):
            target_chat_raw = possible_target
            links_part = parts[1]

    if target_chat_raw:
        target_chat = int(target_chat_raw) if target_chat_raw.lstrip("-").isdigit() else target_chat_raw
    else:
        target_chat = None

    matches = link_regex.findall(links_part)
    if not matches:
        await event.reply("❌ Tidak ada link valid.")
        return

    loading = await event.reply(f"⏳ Memproses {len(matches)} link...")

    for chat_part, msg_id in matches:
        await process_link(event, client, chat_part, int(msg_id), target_chat)

    try:
        await loading.delete()
    except:
        pass


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

    for index, acc in enumerate(ACCOUNTS, start=1):
        client = TelegramClient(StringSession(acc["session"]), API_ID, API_HASH)
        await client.start()
        akun_nama = f"Akun {index}"

        # Anti view-once
        if "anti_view_once" in acc["features"]:
            @client.on(events.NewMessage(incoming=True))
            async def handler(event, c=client, lc=acc["log_channel"], la=acc["log_admin"]):
                await anti_view_once_and_ttl(event, c, lc, la)

        # Spam forward
        if "spam_forward" in acc["features"] and acc.get("spam_triggers"):
            @client.on(events.NewMessage(incoming=True))
            async def spam_handler(event, c=client, triggers=acc["spam_triggers"]):
                await auto_forward_spam(event, c, triggers)

        # Ping
        if "ping" in acc["features"]:
            @client.on(events.NewMessage(pattern=r"^/ping$"))
            async def ping(event, c=client):
                await ping_handler(event, c)

        # Heartbeat
        if "heartbeat" in acc["features"]:
            asyncio.create_task(heartbeat(client, acc["log_admin"], acc["log_channel"], akun_nama))

        # Scheduled message
        if "scheduled_message" in acc["features"] and acc.get("scheduled_targets"):
            asyncio.create_task(scheduled_message(client, acc["scheduled_targets"], akun_nama))

        # SAVE MEDIA INLINE
        if "save_media" in acc["features"]:
            @client.on(events.NewMessage(pattern=r'^/(save|s)(?:\s+|$)(.*)'))
            async def save_handler(event, c=client):
                await handle_save_command(event, c)

        # Info restart
        text = (
            f"♻️ **Ubot Restart (Railway)**\n"
            f"👤 {akun_nama}\n"
            f"🕒 {datetime.now(ZoneInfo('Asia/Jakarta')).strftime('%H:%M:%S || %d-%m-%Y')}"
        )
        if acc["log_admin"]:
            await client.send_message(acc["log_admin"], text)

        clients.append((client, acc.get("log_channel"), acc.get("log_admin")))

    print(f"✅ Ubot aktif dengan {len(clients)} akun.")
    await run_clients_forever()


asyncio.run(main())
