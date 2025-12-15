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

import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote

# === KONFIGURASI UTAMA ===
API_ID = 20958475
API_HASH = '1cfb28ef51c138a027786e43a27a8225'

# === DAFTAR AKUN ===
# Fitur yang bisa dipakai per akun (opsional):
# "anti_view_once", "ping", "heartbeat", "scheduled_message",
# "spam_forward", "save_media", "clearch", "whois", "autopin", "downloader"
#
# Jika fitur tidak mau dipakai, cukup:
# - Hapus dari "features", atau
# - Biarkan field pendukungnya None (misal spam_triggers=None, autopin_keywords=None)

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
            "save_media",
            "clearch",
            "whois",
            "autopin",
            "downloader",  # Tambah fitur downloader
        ],
        "scheduled_targets": [
            {
                "chat_id": 7828063345,
                "text_pagi": "☀️ Gut Pagi 🌄 🌅",
                "text_malam": "🌑 🌕 Gut Malam 🌌",
            }
        ],
        "spam_triggers": ["bebih", "babe", "baby"],
        # kata kunci auto-pin khusus akun ini (private chat only)
        "autopin_keywords": ["al azet", "al_azet", "al-azet"],
    }
]

# list global client (diisi di main)
clients = []

# waktu start untuk /ping uptime
start_time_global = datetime.now()

DOWNLOAD_TIMEOUT = 10  # 10 detik timeout

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
        
        # === PATCH: cek kalau media adalah sticker ===
        if message.media and message.sticker:
            await client.send_file(
                send_to,
                message.media,
                force_document=False  # penting agar tetap sticker (termasuk .tgs animasi)
            )
            return  # selesai, jangan lanjut ke grouped_id

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



# Validasi URL
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False

def is_safe_url(url):
    suspicious_patterns = [
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'file:',
        r'ftp:'
    ]
    for pattern in suspicious_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return False
    return True

def sanitize_url(url):
    """Remove tracking parameters"""
    try:
        parsed = urlparse(url)
        # Hapus parameter tracking umum
        return url.split('?')[0] if '?' in url else url
    except:
        return url.strip()

# Detect platform dari URL
def detect_platform(url):
    url_lower = url.lower()
    
    if 'tiktok.com' in url_lower or 'vm.tiktok.com' in url_lower or 'vt.tiktok.com' in url_lower:
        return 'tiktok'
    elif 'instagram.com' in url_lower or 'instagr.am' in url_lower:
        return 'instagram'
    elif 'facebook.com' in url_lower or 'fb.watch' in url_lower or 'fb.com' in url_lower:
        return 'facebook'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    elif 'pinterest.com' in url_lower or 'pin.it' in url_lower:
        return 'pinterest'
    elif 'spotify.com' in url_lower or 'open.spotify.com' in url_lower:
        return 'spotify'
    elif 'threads.net' in url_lower:
        return 'threads'
    else:
        return None

# TikTok Downloader
async def download_tiktok(url):
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://www.tikwm.com',
                'Referer': 'https://www.tikwm.com/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            data = {
                'url': url,
                'hd': '1'
            }
            
            timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT)
            async with session.post('https://www.tikwm.com/api/', headers=headers, data=data, timeout=timeout) as response:
                if response.status != 200:
                    return None
                
                json_data = await response.json()
                res = json_data.get('data')
                
                if not res:
                    return None
                
                # Deteksi tipe konten
                if res.get('images'):
                    return {
                        'type': 'foto',
                        'platform': 'TikTok',
                        'urls': res['images'],
                        'caption': res.get('title', ''),
                        'author': res.get('author', {}).get('nickname', '')
                    }
                else:
                    video_url = res.get('hdplay') or res.get('play') or res.get('wmplay')
                    if video_url:
                        return {
                            'type': 'video',
                            'platform': 'TikTok',
                            'url': video_url,
                            'caption': res.get('title', ''),
                            'author': res.get('author', {}).get('nickname', '')
                        }
                
                return None
                
    except asyncio.TimeoutError:
        return {'error': 'Timeout - server tidak merespons dalam 10 detik'}
    except Exception as e:
        return {'error': str(e)}

# Instagram Downloader
async def download_instagram(url):
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://saveig.app',
                'Referer': 'https://saveig.app/en',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            data = {'q': url, 'lang': 'en'}
            
            timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT)
            async with session.post('https://saveig.app/api/ajaxSearch', headers=headers, data=data, timeout=timeout) as response:
                if response.status != 200:
                    return None
                
                json_data = await response.json()
                html = json_data.get('data', '')
                
                if not html:
                    return None
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Cari semua link download
                download_links = soup.find_all('a', {'class': 'abutton'})
                
                if download_links:
                    urls = []
                    for link in download_links:
                        href = link.get('href')
                        if href and href.startswith('http'):
                            urls.append(href)
                    
                    if urls:
                        return {
                            'type': 'video' if len(urls) == 1 else 'foto',
                            'platform': 'Instagram',
                            'urls': urls if len(urls) > 1 else None,
                            'url': urls[0] if len(urls) == 1 else None
                        }
                
                return None
                
    except asyncio.TimeoutError:
        return {'error': 'Timeout - server tidak merespons dalam 10 detik'}
    except Exception as e:
        return {'error': str(e)}

# Facebook Downloader
async def download_facebook(url):
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'hx-current-url': 'https://getmyfb.com/',
                'hx-request': 'true',
                'hx-target': '#target',
                'hx-trigger': 'form',
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            data = {'url': url}
            
            timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT)
            async with session.post('https://getmyfb.com/process', headers=headers, data=data, timeout=timeout) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract download links
                results = []
                download_links = soup.find_all('a', href=True)
                
                for link in download_links:
                    href = link.get('href')
                    if href and href.startswith('http'):
                        text = link.get_text().strip()
                        if 'Download' in text or 'HD' in text or 'SD' in text:
                            results.append(href)
                
                if results:
                    return {
                        'type': 'video',
                        'platform': 'Facebook',
                        'url': results[0],  # Ambil kualitas terbaik
                        'urls': results if len(results) > 1 else None
                    }
                
                return None
                
    except asyncio.TimeoutError:
        return {'error': 'Timeout - server tidak merespons dalam 10 detik'}
    except Exception as e:
        return {'error': str(e)}

# Pinterest Downloader
async def download_pinterest(url):
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://pinterestvideodownloader.com',
                'Referer': 'https://pinterestvideodownloader.com/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            data = {'url': url}
            
            timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT)
            async with session.post('https://pinterestvideodownloader.com/download.php', headers=headers, data=data, timeout=timeout) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                
                # Extract download links menggunakan regex seperti di kode TypeScript
                pattern = r'<a[^>]+href="(https?://[^"]+\.(?:jpg|png|mp4|gif))"[^>]*>(.*?)</a>'
                matches = re.finditer(pattern, html, re.IGNORECASE)
                
                videos = []
                images = []
                
                for match in matches:
                    download_url = match.group(1)
                    text = match.group(2).lower()
                    
                    if '.mp4' in download_url or 'video' in text:
                        videos.append(download_url)
                    elif '.jpg' in download_url or '.png' in download_url:
                        images.append(download_url)
                
                # Prioritas: video > image
                if videos:
                    return {
                        'type': 'video',
                        'platform': 'Pinterest',
                        'url': videos[0]
                    }
                elif images:
                    return {
                        'type': 'foto',
                        'platform': 'Pinterest',
                        'url': images[0]
                    }
                
                return None
                
    except asyncio.TimeoutError:
        return {'error': 'Timeout - server tidak merespons dalam 10 detik'}
    except Exception as e:
        return {'error': str(e)}

# Twitter/X Downloader
async def download_twitter(url):
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            api_url = f'https://twitsave.com/api/info?url={quote(url)}'
            
            timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT)
            async with session.get(api_url, headers=headers, timeout=timeout) as response:
                if response.status != 200:
                    return None
                
                json_data = await response.json()
                
                if json_data.get('downloads'):
                    downloads = json_data['downloads']
                    if downloads:
                        return {
                            'type': 'video',
                            'platform': 'Twitter/X',
                            'url': downloads[0].get('url')
                        }
                
                return None
                
    except asyncio.TimeoutError:
        return {'error': 'Timeout - server tidak merespons dalam 10 detik'}
    except Exception as e:
        return {'error': str(e)}

# Threads Downloader
async def download_threads(url):
    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Get cookies
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36'
            }
            
            timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT)
            async with session.get('https://threadster.app/', headers=headers, timeout=timeout) as response:
                cookies = response.cookies
            
            # Step 2: POST request
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            data = {'url': url}
            
            async with session.post('https://threadster.app/download', headers=headers, data=data, cookies=cookies, timeout=timeout) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                
                # Extract media links
                pattern = r'<tr><td>(.*?)</td><td><a.*?href="(.*?)".*?</a></td></tr>'
                matches = re.finditer(pattern, html)
                
                videos = []
                photos = []
                
                for match in matches:
                    resolution = match.group(1).strip()
                    media_url = match.group(2)
                    
                    if '/threadster/image?' in media_url:
                        photos.append(media_url)
                    elif '/threadster/video?' in media_url:
                        videos.append(media_url)
                
                if videos:
                    return {
                        'type': 'video',
                        'platform': 'Threads',
                        'url': videos[0]
                    }
                elif photos:
                    return {
                        'type': 'foto',
                        'platform': 'Threads',
                        'urls': photos
                    }
                
                return None
                
    except asyncio.TimeoutError:
        return {'error': 'Timeout - server tidak merespons dalam 10 detik'}
    except Exception as e:
        return {'error': str(e)}

# Main downloader handler
async def handle_download_command(event, client):
    if not event.is_private:
        return
    
    me = await client.get_me()
    if event.sender_id != me.id:
        return
    
    # Ambil URL dari command atau reply
    input_text = event.pattern_match.group(2).strip()
    
    if not input_text:
        if event.is_reply:
            reply = await event.get_reply_message()
            if reply and reply.message:
                input_text = reply.message.strip()
            else:
                await event.reply("❌ Pesan balasan tidak berisi link.")
                return
        else:
            await event.reply("❌ Kirim link sosial media seperti TikTok, Instagram, Facebook, dll.\n\n**Contoh:** `/d https://tiktok.com/...`")
            return
    
    # Validasi URL
    if not is_valid_url(input_text):
        await event.reply("❌ Link tidak valid. Pastikan URL dimulai dengan http:// atau https://")
        return
    
    if not is_safe_url(input_text):
        await event.reply("❌ Link tidak aman atau tidak didukung.")
        return
    
    # Sanitize URL
    url = sanitize_url(input_text)
    
    # Detect platform
    platform = detect_platform(url)
    
    if not platform:
        await event.reply("❌ Platform tidak didukung. Saat ini mendukung:\n• TikTok\n• Instagram\n• Facebook\n• Twitter/X\n• Pinterest\n• Threads")
        return
    
    # Loading message
    loading = await event.reply(f"⏳ Mengunduh dari **{platform.title()}**...")
    
    try:
        # Download berdasarkan platform
        result = None
        
        if platform == 'tiktok':
            result = await download_tiktok(url)
        elif platform == 'instagram':
            result = await download_instagram(url)
        elif platform == 'facebook':
            result = await download_facebook(url)
        elif platform == 'twitter':
            result = await download_twitter(url)
        elif platform == 'pinterest':
            result = await download_pinterest(url)
        elif platform == 'threads':
            result = await download_threads(url)
        
        if not result:
            await loading.edit("❌ Gagal mengunduh media. Link mungkin tidak valid atau konten private.")
            return
        
        if 'error' in result:
            await loading.edit(f"❌ Error: {result['error']}")
            return
        
        # Download dan kirim media
        caption = f"📥 **Downloaded from {result['platform']}**"
        if result.get('caption'):
            caption += f"\n\n{result['caption']}"
        if result.get('author'):
            caption += f"\n👤 {result['author']}"
        
        # Handle multiple URLs (foto album)
        if result.get('urls'):
            files = []
            for media_url in result['urls'][:10]:  # Limit 10 files
                try:
                    async with aiohttp.ClientSession() as session:
                        timeout = aiohttp.ClientTimeout(total=30)
                        async with session.get(media_url, timeout=timeout) as resp:
                            if resp.status == 200:
                                content = await resp.read()
                                
                                # Simpan temporary
                                ext = 'jpg' if result['type'] == 'foto' else 'mp4'
                                temp_file = f"temp_download_{datetime.now().timestamp()}.{ext}"
                                
                                with open(temp_file, 'wb') as f:
                                    f.write(content)
                                
                                files.append(temp_file)
                except:
                    continue
            
            if files:
                await client.send_file(event.chat_id, files, caption=caption)
                
                # Hapus files temporary
                for f in files:
                    try:
                        os.remove(f)
                    except:
                        pass
            else:
                await loading.edit("❌ Gagal mengunduh media.")
                return
        
        # Handle single URL
        elif result.get('url'):
            try:
                async with aiohttp.ClientSession() as session:
                    timeout = aiohttp.ClientTimeout(total=30)
                    async with session.get(result['url'], timeout=timeout) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            
                            # Simpan temporary
                            ext = 'jpg' if result['type'] == 'foto' else 'mp4'
                            temp_file = f"temp_download_{datetime.now().timestamp()}.{ext}"
                            
                            with open(temp_file, 'wb') as f:
                                f.write(content)
                            
                            await client.send_file(event.chat_id, temp_file, caption=caption)
                            
                            # Hapus file temporary
                            try:
                                os.remove(temp_file)
                            except:
                                pass
                        else:
                            await loading.edit("❌ Gagal mengunduh media.")
                            return
            except Exception as e:
                await loading.edit(f"❌ Error saat mengunduh: {str(e)}")
                return
        
        # Hapus loading message
        try:
            await loading.delete()
        except:
            pass
            
    except Exception as e:
        await loading.edit(f"❌ Error: {str(e)}")


# === FITUR: CLEAR CHANNEL (KHUSUS CHANNEL) ===
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


# === FITUR: WHOIS (KHUSUS PRIVATE) ===
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
        f"☎️ Nomor: {phone}\n"
    )
    
    try:
        # Ambil semua foto/video profil user
        photos = await client.get_profile_photos(user.id, limit=10)  # batasi 10 biar aman
        files = []
        for p in photos:
            fpath = await client.download_media(p)
            files.append(fpath)

        if files:
            # Kirim sebagai media group (album)
            await client.send_file(
                event.chat_id,
                files,
                caption=text,
                link_preview=False
            )
            # Hapus file lokal
            for f in files:
                try:
                    os.remove(f)
                except:
                    pass
        else:
            await event.reply(text)
    except Exception as e:
        await event.reply(f"{text}\n\n⚠ Error ambil foto profil: {e}")


# === FITUR: AUTO-PIN (KHUSUS PRIVATE) ===
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

        if "downloader" in acc["features"]:
            @client.on(events.NewMessage(pattern=r'^/(download|d)(?:\s+|$)(.*)'))
            async def download_handler(event, c=client):
                await handle_download_command(event, c)

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
