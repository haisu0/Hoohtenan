# ========== BAGIAN 1 ==========
# IMPORT, KONFIG, ACCOUNTS, SETUP DASAR

import asyncio
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread
from telethon.tl.functions.users import GetFullUserRequest

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, unquote

# === KONFIGURASI UTAMA ===
API_ID = 20958475
API_HASH = '1cfb28ef51c138a027786e43a27a8225'

# === DAFTAR AKUN ===
ACCOUNTS = [
    {
        "session": "1BVtsOKgBu0l1em7gQclC80PlZMCFDCWGlXjysPPWeWndxqSKqoYiimx6h2uthMnQwq83qGUHZwh2fGAAuMzyrh3szU9OcRyXMEBMHivlZNQE_MU3CwjG1C46nvvK6KOwz2qBLdP9d-eRs2V4jpHJQLoZGSwiHP6Mn8Wx4wFDFg8WvBR4UKNOKtaACnDt_wpP3GIzLhXJdBomgKzwJs9MHoRZJ9a6sbhudrmLhpNdBwjdkYUR_y_ot68fBC16Sbm8lybeZ3Wzx_HPN6JZDGbu1-bVJbj_p28pSR5EWYYhqqPL1wZn10sw86-At3MSnSKSxg1PYyoDH1IuZ5UUR_4NlUSq5fr3urE=",
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
        ]
    },
    {
        "session": "1BVtsOMQBuzWf5RY6-41ijhTQc8RGVQWG4G1fb2KcM6Wt2cYgWKLwrIQgAiicn3EQyJzKqMeMz1dAC3CitORNE6IS-jbJiSqJfyUL_RRewtTED_FXc3ZaH1gCtCBg7RVIqEw-GH_9rROORb2mGsNoC524GZGnyfiJydaJjnWHC9DV7cEsTUFLObBpva2U5Ft3Y_HiHg3OWC_3NH6Sgv9Kh3MTKyQfAK6x9akpHIvmhtESXyszSU66wLu6mvmTmQ7yaA2570DOmeDGq60sV7sHF4M6cClNqHvZ9j5Xu6ODh4NICPrgmvgwyz1A8-dopiG9E-K3Bjga_UOI8wcogHW4DDVCStR5yHA=",
        "log_channel": None,
        "log_admin": 7828063345,
        "features": [
            "anti_view_once",
            "ping",
            "heartbeat",
            "whois",
        ]
    }
]

# list global client (diisi di main)
clients = []

# waktu start untuk /ping uptime
start_time_global = datetime.now()

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
        
        if message.media and message.sticker:
            await client.send_file(
                send_to,
                message.media,
                force_document=False
            )
            return

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


# === FITUR: CLEAR CHANNEL ===
async def clearch_handler(event, client):
    chat = await event.get_chat()

    if not getattr(chat, "broadcast", False):
        await event.reply("❌ /clearch hanya bisa dipakai di **channel**, bukan grup.")
        return

    perms = await client.get_permissions(chat, 'me')
    if not perms.is_admin or not perms.delete_messages:
        await event.reply("❌ Ubot tidak punya izin **delete messages** di channel ini.")
        return

    await event.reply("🧹 Menghapus semua pesan di channel...")

    async for msg in client.iter_messages(chat.id):
        try:
            await msg.delete()
        except:
            pass

    await client.send_message(chat.id, "✅ Semua pesan berhasil dihapus.")


# === FITUR: WHOIS ===
async def whois_handler(event, client):
    if not event.is_private:
        return

    if not event.is_reply:
        await event.reply("❌ Reply pesan user yang ingin kamu cek.")
        return

    reply = await event.get_reply_message()
    user = await client.get_entity(reply.sender_id)

    try:
        full = await client(GetFullUserRequest(user.id))
        bio = full.full_user.about or "-"
    except Exception as e:
        bio = f"⚠ Tidak bisa ambil bio: {e}"

    phone = getattr(user, "phone", None)
    phone = f"+{phone}" if phone and not phone.startswith("+") else (phone or "-")

    text = (
        f"👤 **WHOIS USER**\n\n"
        f"🆔 ID: `{user.id}`\n"
        f"👥 Nama: {user.first_name or '-'} {user.last_name or ''}\n"
        f"🔗 Username: @{user.username if user.username else '-'}\n"
        f"📖 Bio: {bio}\n"
        f"⭐ Premium: {'Ya' if getattr(user, 'premium', False) else 'Tidak'}\n"
        f"🤖 Bot: {'Ya' if user.bot else 'Tidak'}\n"
    )
    
    try:
        photos = await client.get_profile_photos(user.id, limit=10)
        files = []
        for p in photos:
            fpath = await client.download_media(p)
            files.append(fpath)

        if files:
            await client.send_file(
                event.chat_id,
                files,
                caption=text,
                link_preview=False
            )
            for f in files:
                try:
                    os.remove(f)
                except:
                    pass
        else:
            await event.reply(text)
    except Exception as e:
        await event.reply(f"{text}\n\n⚠ Error ambil foto profil: {e}")


# === FITUR: AUTO-PIN ===
async def autopin_handler(event, client, keywords):
    if not event.is_private:
        return

    if not keywords:
        return

    text = (event.message.message or "").lower()

    if any(word.lower() in text for word in keywords):
        try:
            await client.pin_message(event.chat_id, event.message.id)
        except:
            pass


# === FITUR: DOWNLOADER ===

def is_valid_url(url):
    """Validasi apakah string adalah URL yang valid"""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False

def sanitize_url(url):
    """Membersihkan URL dari tracking parameters"""
    try:
        parsed = urlparse(url)
        tracking_params = ["utm_source", "utm_medium", "utm_campaign", "fbclid", "gclid", "_gl"]
        query_params = parse_qs(parsed.query)
        for param in tracking_params:
            query_params.pop(param, None)
        
        clean_query = urlencode(query_params, doseq=True)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if clean_query:
            clean_url += f"?{clean_query}"
        return clean_url.strip()
    except:
        return url.strip()

PLATFORM_PATTERNS = {
    'tiktok': re.compile(r'(?:^|\.)tiktok\.com', re.IGNORECASE),
    'instagram': re.compile(r'(?:^|\.)instagram\.com|instagr\.am', re.IGNORECASE),
}

def detect_platform(url):
    """Deteksi platform dari URL dengan regex yang lebih akurat"""
    for platform, pattern in PLATFORM_PATTERNS.items():
        if pattern.search(url):
            return platform
    return None

def get_best_video_url(video_data, platform='tiktok'):
    """Memilih URL video dengan kualitas terbaik berdasarkan prioritas"""
    if platform == 'tiktok':
        # Prioritas: nowatermark_hd > nowatermark > watermark
        if video_data.get('nowatermark_hd'):
            return video_data['nowatermark_hd']
        elif video_data.get('nowatermark'):
            return video_data['nowatermark']
        elif video_data.get('watermark'):
            return video_data['watermark']
    return None

async def download_tiktok(url, quality='best'):
    """Handler untuk download TikTok"""
    try:
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://www.tikwm.com',
            'Referer': 'https://www.tikwm.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        data = {
            'url': url,
            'hd': '1' if quality == 'best' else '0'
        }
        
        response = requests.post('https://www.tikwm.com/api/', headers=headers, data=data, timeout=15)
        response.raise_for_status()
        
        json_data = response.json()
        res = json_data.get('data')
        
        if not res:
            return {'success': False, 'message': 'Gagal mengambil data dari TikTok'}
        
        result = {
            'success': True,
            'platform': 'TikTok',
            'type': '',
            'video': {},
            'images': [],
            'author': {
                'username': res.get('author', {}).get('unique_id', ''),
                'nickname': res.get('author', {}).get('nickname', ''),
            },
            'title': res.get('title', ''),
            'stats': {
                'views': res.get('play_count', 0),
                'likes': res.get('digg_count', 0),
                'comments': res.get('comment_count', 0),
            }
        }
        
        if res.get('images'):
            result['type'] = 'images'
            result['images'] = res['images']
        else:
            result['type'] = 'video'
            result['video'] = {
                'watermark': res.get('wmplay', ''),
                'nowatermark': res.get('play', ''),
                'nowatermark_hd': res.get('hdplay', '')
            }
        
        return result
        
    except Exception as e:
        return {'success': False, 'message': f'Error TikTok: {str(e)}'}

async def download_instagram(url, quality='best'):
    """Handler untuk download Instagram"""
    try:
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://yt1s.io',
            'Referer': 'https://yt1s.io/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        data = {
            'q': url,
            'w': '',
            'p': 'home',
            'lang': 'en'
        }
        
        response = requests.post('https://yt1s.io/api/ajaxSearch', headers=headers, data=data, timeout=15)
        response.raise_for_status()
        
        json_data = response.json()
        html = json_data.get('data', '')
        
        if not html:
            return {'success': False, 'message': 'Tidak ada data dari Instagram'}
        
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=True, title=True)
        
        videos = []
        images = []
        thumb = ''
        
        for link in links:
            href = link['href']
            title = link['title'].lower()
            
            if 'thumbnail' in title and href.startswith('http'):
                thumb = href
            elif 'video' in title and href.startswith('http') and href != '/en/home':
                videos.append(href)
            elif ('foto' in title or 'image' in title) and href.startswith('http'):
                images.append(href)
        
        result = {
            'success': True,
            'platform': 'Instagram',
            'type': 'video' if videos else 'images' if images else 'unknown',
            'video': videos,
            'images': images,
            'thumb': thumb
        }
        
        return result
        
    except Exception as e:
        return {'success': False, 'message': f'Error Instagram: {str(e)}'}

async def handle_downloader(event, client):
    """Handler utama untuk command /d dan /download"""
    if not event.is_private:
        return
    
    me = await client.get_me()
    if event.sender_id != me.id:
        return
    
    input_text = event.pattern_match.group(2).strip() if event.pattern_match.group(2) else ''
    
    if not input_text:
        if event.is_reply:
            reply = await event.get_reply_message()
            if reply and reply.message:
                input_text = reply.message.strip()
            else:
                await event.reply("❌ Pesan balasan tidak berisi link.")
                return
        else:
            await event.reply(
                "❌ **Cara pakai:**\n"
                "`/d <link>` atau `/download <link>`\n"
                "atau reply pesan yang berisi link\n\n"
                "**Platform support:**\n"
                "• TikTok\n"
                "• Instagram"
            )
            return
    
    if not is_valid_url(input_text):
        await event.reply("❌ Input bukan link yang valid!")
        return
    
    clean_url = sanitize_url(input_text)
    platform = detect_platform(clean_url)
    
    if not platform:
        await event.reply("❌ Platform tidak didukung. Gunakan link dari TikTok, Instagram.")
        return
    
    loading = await event.reply(f"⏳ Mengunduh dari **{platform.title()}**...")
    
    try:
        if platform == 'tiktok':
            result = await download_tiktok(clean_url)
        elif platform == 'instagram':
            result = await download_instagram(clean_url)
        else:
            await loading.edit("❌ Platform belum didukung")
            return
        
        try:
            await loading.delete()
        except:
            pass
        
        if not result.get('success'):
            await event.reply(f"❌ {result.get('message', 'Gagal mengunduh')}")
            return
        
        if result['type'] == 'video':
            if platform == 'tiktok':
                # Get best quality video
                video_url = get_best_video_url(result['video'], 'tiktok')
                caption = (
                    f"📹 **TikTok Video**\n\n"
                    f"👤 @{result['author']['username']}\n"
                    f"📝 {result['title'][:100]}...\n"
                    f"👁 {result['stats']['views']:,} views"
                )
                
                try:
                    # Try to download and send directly
                    video_res = requests.get(video_url, timeout=30, stream=True)
                    if video_res.status_code == 200:
                        filename = f"tiktok_{datetime.now().timestamp()}.mp4"
                        with open(filename, 'wb') as f:
                            for chunk in video_res.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        await client.send_file(event.chat_id, filename, caption=caption)
                        os.remove(filename)
                    else:
                        await event.reply(f"{caption}\n\n🔗 [Download]({video_url})")
                except:
                    await event.reply(f"{caption}\n\n🔗 [Download]({video_url})")
                    
            elif platform == 'instagram':
                if len(result['video']) > 1:
                    files = []
                    for idx, video_url in enumerate(result['video'][:10], 1):
                        try:
                            video_res = requests.get(video_url, timeout=30, stream=True)
                            if video_res.status_code == 200:
                                filename = f"instagram_{idx}_{datetime.now().timestamp()}.mp4"
                                with open(filename, 'wb') as f:
                                    for chunk in video_res.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                files.append(filename)
                        except:
                            pass
                    
                    if files:
                        await client.send_file(
                            event.chat_id,
                            files,
                            caption=f"📹 **Instagram Videos** ({len(files)} videos)"
                        )
                        for f in files:
                            try:
                                os.remove(f)
                            except:
                                pass
                    else:
                        for idx, video_url in enumerate(result['video'][:5], 1):
                            await event.reply(f"📹 **Instagram Video {idx}**\n\n🔗 [Download]({video_url})")
                else:
                    video_url = result['video'][0]
                    await event.reply(f"📹 **Instagram Video**\n\n🔗 [Download]({video_url})")
                            
        elif result['type'] == 'images':
            if platform == 'tiktok':
                caption = (
                    f"🖼 **TikTok Images** ({len(result['images'])} foto)\n\n"
                    f"👤 @{result['author']['username']}\n"
                    f"📝 {result['title'][:100]}..."
                )
                files = []
                for img_url in result['images'][:10]:
                    try:
                        img_res = requests.get(img_url, timeout=15)
                        if img_res.status_code == 200:
                            filename = f"tiktok_{datetime.now().timestamp()}_{len(files)}.jpg"
                            with open(filename, 'wb') as f:
                                f.write(img_res.content)
                            files.append(filename)
                    except:
                        pass
                
                if files:
                    await client.send_file(event.chat_id, files, caption=caption)
                    for f in files:
                        try:
                            os.remove(f)
                        except:
                            pass
                            
            elif platform == 'instagram':
                if len(result['images']) > 1:
                    files = []
                    for idx, img_url in enumerate(result['images'][:10], 1):
                        try:
                            img_res = requests.get(img_url, timeout=15)
                            if img_res.status_code == 200:
                                filename = f"instagram_{idx}_{datetime.now().timestamp()}.jpg"
                                with open(filename, 'wb') as f:
                                    f.write(img_res.content)
                                files.append(filename)
                        except:
                            pass
                    
                    if files:
                        await client.send_file(
                            event.chat_id,
                            files,
                            caption=f"🖼 **Instagram Images** ({len(files)} photos)"
                        )
                        for f in files:
                            try:
                                os.remove(f)
                            except:
                                pass
                    else:
                        for idx, img_url in enumerate(result['images'][:10], 1):
                            await event.reply(f"🖼 **Instagram Image {idx}**\n\n🔗 [Download]({img_url})")
                else:
                    await event.reply(f"🖼 **Instagram Image**\n\n🔗 [Download]({result['images'][0]})")
        
        elif result['type'] == 'audio':
            title = result.get('metadata', {}).get('title', 'Unknown')
            artist = result.get('metadata', {}).get('artist', 'Unknown')
            caption = f"🎵 **Spotify Audio**\n\n🎵 {title}\n👤 {artist}\n\n🔗 [Download]({result['url']})"
            await event.reply(caption)
        
        else:
            if 'url' in result:
                await event.reply(f"📥 **{platform.title()}**\n\n🔗 [Download]({result['url']})")
            else:
                await event.reply("✅ Media berhasil diproses!")
        
    except Exception as e:
        try:
            await loading.delete()
        except:
            pass
        await event.reply(f"🚨 Error: `{str(e)}`")

# ========== BAGIAN 3 ==========
# WEB SERVER, RESTART LOOP, MAIN + HANDLER

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

        # === ANTI VIEW-ONCE ===
        if "anti_view_once" in acc["features"]:
            @client.on(events.NewMessage(incoming=True))
            async def handler(event, c=client, lc=acc["log_channel"], la=acc["log_admin"]):
                await anti_view_once_and_ttl(event, c, lc, la)

        # === SPAM FORWARD ===
        if "spam_forward" in acc["features"] and acc.get("spam_triggers"):
            @client.on(events.NewMessage(incoming=True))
            async def spam_handler(event, c=client, triggers=acc["spam_triggers"]):
                await auto_forward_spam(event, c, triggers)

        # === PING ===
        if "ping" in acc["features"]:
            @client.on(events.NewMessage(pattern=r"^/ping$"))
            async def ping(event, c=client):
                await ping_handler(event, c)

        # === HEARTBEAT ===
        if "heartbeat" in acc["features"]:
            asyncio.create_task(heartbeat(client, acc["log_admin"], acc["log_channel"], akun_nama))

        # === SCHEDULED MESSAGE ===
        if "scheduled_message" in acc["features"] and acc.get("scheduled_targets"):
            asyncio.create_task(scheduled_message(client, acc["scheduled_targets"], akun_nama))

        # === SAVE MEDIA / COLONG MEDIA ===
        if "save_media" in acc["features"]:
            @client.on(events.NewMessage(pattern=r'^/(save|s)(?:\s+|$)(.*)'))
            async def save_handler(event, c=client):
                await handle_save_command(event, c)

        # === DOWNLOADER ===
        if "downloader" in acc["features"]:
            @client.on(events.NewMessage(pattern=r'^/(d|download)(?:\s+|$)(.*)'))
            async def downloader_handler(event, c=client):
                await handle_downloader(event, c)

        # === CLEAR CHANNEL (KHUSUS CHANNEL) ===
        if "clearch" in acc["features"]:
            @client.on(events.NewMessage(pattern=r"^/clearch$"))
            async def clearch(event, c=client):
                await clearch_handler(event, c)

        # === WHOIS (KHUSUS PRIVATE) ===
        if "whois" in acc["features"]:
            @client.on(events.NewMessage(pattern=r"^/whois$"))
            async def whois(event, c=client):
                await whois_handler(event, c)

        # === AUTO-PIN (KHUSUS PRIVATE) ===
        if "autopin" in acc["features"]:
            @client.on(events.NewMessage(incoming=True))
            async def autopin(event, c=client, kw=acc.get("autopin_keywords", [])):
                await autopin_handler(event, c, kw)

        # === INFO RESTART ===
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
