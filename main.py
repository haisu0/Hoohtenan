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
from telethon import types

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
            "clearch",
            "whois",
            "downloader",
        ],

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
    'facebook': re.compile(r'(?:^|\.)facebook\.com|fb\.watch', re.IGNORECASE),
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
    elif platform == 'facebook':
        # Prioritas: HD > SD
        hd = next((item for item in video_data if item.get('type') == 'HD'), None)
        if hd:
            return hd['url']
        sd = next((item for item in video_data if item.get('type') == 'SD'), None)
        if sd:
            return sd['url']
    return None

async def download_tiktok(url, quality='best'):
    """Handler untuk download TikTok - updated to match parse-duration.ts"""
    try:
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://www.tikwm.com',
            'Referer': 'https://www.tikwm.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        params = {
            'url': url,
            'hd': '1' if quality == 'best' else '0'
        }
        
        response = requests.post('https://www.tikwm.com/api/', headers=headers, params=params, timeout=15)
        response.raise_for_status()
        
        json_data = response.json()
        res = json_data.get('data')
        
        if not res:
            return {'success': False, 'message': 'Gagal mengambil data dari TikTok'}
        
        # Format data sesuai parse-duration.ts
        data = []
        if not res.get('size') and not res.get('wm_size') and not res.get('hd_size'):
            # TikTok slideshow/images
            for img_url in res.get('images', []):
                data.append({'type': 'photo', 'url': img_url})
        else:
            # TikTok video
            if res.get('wmplay'):
                data.append({'type': 'watermark', 'url': res['wmplay']})
            if res.get('play'):
                data.append({'type': 'nowatermark', 'url': res['play']})
            if res.get('hdplay'):
                data.append({'type': 'nowatermark_hd', 'url': res['hdplay']})
        
        result = {
            'success': True,
            'platform': 'TikTok',
            'type': 'images' if res.get('images') else 'video',
            'data': data,
            'images': res.get('images', []),
            'video': {
                'watermark': res.get('wmplay', ''),
                'nowatermark': res.get('play', ''),
                'nowatermark_hd': res.get('hdplay', '')
            },
            'author': {
                'id': res.get('author', {}).get('id', ''),
                'username': res.get('author', {}).get('unique_id', ''),
                'nickname': res.get('author', {}).get('nickname', ''),
                'avatar': res.get('author', {}).get('avatar', ''),
            },
            'title': res.get('title', ''),
            'duration': res.get('duration', 0),
            'cover': res.get('cover', ''),
            'music_info': {
                'id': res.get('music_info', {}).get('id', ''),
                'title': res.get('music_info', {}).get('title', ''),
                'author': res.get('music_info', {}).get('author', ''),
                'album': res.get('music_info', {}).get('album'),
                'url': res.get('music') or res.get('music_info', {}).get('play', ''),
            },
            'stats': {
                'views': res.get('play_count', 0),
                'likes': res.get('digg_count', 0),
                'comments': res.get('comment_count', 0),
                'shares': res.get('share_count', 0),
                'downloads': res.get('download_count', 0),
            }
        }
        
        return result
        
    except Exception as e:
        return {'success': False, 'message': f'Error TikTok: {str(e)}'}

async def download_instagram(url, quality='best'):
    """Handler untuk download Instagram - updated to return better data"""
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
            
            # Skip invalid URLs
            if not href.startswith('http') or href == '/en/home':
                continue
            
            if 'thumbnail' in title:
                thumb = href
            elif 'video' in title or 'mp4' in title:
                videos.append({'type': 'video', 'url': href})
            elif 'foto' in title or 'image' in title or 'photo' in title or 'jpg' in title:
                images.append({'type': 'photo', 'url': href})
        
        # Determine media type
        has_videos = len(videos) > 0
        has_images = len(images) > 0
        
        if has_videos and has_images:
            media_type = 'mixed'
        elif has_videos:
            media_type = 'video'
        elif has_images:
            media_type = 'images'
        else:
            media_type = 'unknown'
        
        result = {
            'success': True,
            'platform': 'Instagram',
            'type': media_type,
            'data': videos + images,  # Combined list
            'videos': videos,
            'images': images,
            'thumb': thumb
        }
        
        return result
        
    except Exception as e:
        return {'success': False, 'message': f'Error Instagram: {str(e)}'}
        
async def download_facebook(url, quality='best'):
    """Handler untuk download Facebook - adapted from JS code"""
    try:
        headers = {
            'hx-current-url': 'https://getmyfb.com/',
            'hx-request': 'true',
            'hx-target': '#private-video-downloader' if 'share' in url else '#target',
            'hx-trigger': 'form',
            'hx-post': '/process',
            'hx-swap': 'innerHTML',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        data = {
            'id': unquote(url),
            'locale': 'en'
        }
        
        response = requests.post('https://getmyfb.com/process', headers=headers, data=data, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        caption = soup.select_one('.results-item-text')
        caption = caption.text.strip() if caption else ""
        
        preview = soup.select_one('.results-item-image')
        preview = preview['src'] if preview else ""
        
        results = []
        for item in soup.select('.results-list-item'):
            link = item.select_one('a')
            if link:
                title = link.get('title', '')
                href = link.get('href', '')
                quality_type = 'HD' if 'HD' in title else 'SD'
                results.append({
                    'quality': int(title.split()[0]) if title.split()[0].isdigit() else 0,
                    'type': quality_type,
                    'url': href
                })
        
        result = {
            'success': True,
            'platform': 'Facebook',
            'caption': caption,
            'preview': preview,
            'results': results
        }
        
        return result
        
    except Exception as e:
        return {'success': False, 'message': f'Error Facebook: {str(e)}'}

async def handle_downloader(event, client):
    """Handler utama untuk command /d dan /download"""
    if not event.is_private:
        return
    
    me = await client.get_me()
    if event.sender_id != me.id:
        return
    
    input_text = event.pattern_match.group(2).strip() if event.pattern_match.group(2) else ''
    reply = await event.get_reply_message() if event.is_reply else None

    target_chat = event.chat_id
    links_text = ''

    # Parsing input_text: split menjadi target_chat dan links_text
    parts = input_text.split()
    if parts and (re.match(r'^@?[a-zA-Z0-9_]+$', parts[0]) or re.match(r'^-?\d+$', parts[0])):
        target_chat_raw = parts[0]
        target_chat = int(target_chat_raw) if target_chat_raw.lstrip("-").isdigit() else target_chat_raw
        links_text = ' '.join(parts[1:])  # Sisanya sebagai links_text

    # Jika links_text kosong, ambil dari reply jika ada
    if not links_text and reply and reply.message:
        links_text = reply.message.strip()

    # Jika masih kosong, error
    if not links_text:
        await event.reply("❌ Tidak ada link yang diberikan. Gunakan /d link, /d chatid link, atau reply pesan berisi link.")
        return

    # Ekstrak semua URL dari teks
    url_pattern = re.compile(r'https?://[^\s]+')
    urls = url_pattern.findall(links_text)
    valid_urls = [sanitize_url(url) for url in urls if is_valid_url(url)]
    if not valid_urls:
        await event.reply("❌ Tidak ada link valid.")
        return

    loading = await event.reply(f"⏳ Memproses {len(valid_urls)} link...")

    for url in valid_urls:
        platform = detect_platform(url)
        if not platform:
            await event.reply(f"❌ Platform tidak didukung untuk link: {url}")
            continue

        try:
            if platform == 'tiktok':
                result = await download_tiktok(url)
            elif platform == 'instagram':
                result = await download_instagram(url)
            elif platform == 'facebook':
                result = await download_facebook(url)
            else:
                continue

            if not result.get('success'):
                await event.reply(f"❌ {result.get('message', 'Gagal mengunduh')} untuk {url}")
                continue

            # Kirim hasil ke target_chat
            await send_download_result(client, target_chat, result, platform)

        except Exception as e:
            await event.reply(f"❌ Error memproses {url}: {str(e)}")

    try:
        await loading.delete()
    except:
        pass

async def send_download_result(client, target_chat, result, platform):
    """Fungsi untuk mengirim hasil download ke target_chat"""
    try:
        if platform == 'tiktok':
            if result['type'] == 'video':
                # Get best quality video
                video_url = get_best_video_url(result['video'], 'tiktok')
                
                if not video_url:
                    await client.send_message(target_chat, f"❌ Tidak ada URL video yang valid untuk TikTok")
                    return
                
                caption = (
                    f"📹 **TikTok Video**\n\n"
                    f"👤 **Author:** @{result['author']['username']}\n"
                    f"📝 **Title:** {result['title'][:100]}{'...' if len(result['title']) > 100 else ''}\n"
                    f"⏱ **Duration:** {result['duration']}s\n"
                    f"👁 **Views:** {result['stats']['views']:,}\n"
                    f"❤️ **Likes:** {result['stats']['likes']:,}\n"
                    f"💬 **Comments:** {result['stats']['comments']:,}"
                )
                
                # Download and send video
                try:
                    video_res = requests.get(video_url, timeout=60, stream=True)
                    if video_res.status_code == 200:
                        video_filename = f"tiktok_{int(datetime.now().timestamp())}.mp4"
                        with open(video_filename, 'wb') as f:
                            for chunk in video_res.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        await client.send_file(target_chat, video_filename, caption=caption)
                        os.remove(video_filename)
                    else:
                        await client.send_message(target_chat, f"{caption}\n\n🔗 [Download Video]({video_url})")
                except Exception as e:
                    await client.send_message(target_chat, f"{caption}\n\n🔗 [Download Video]({video_url})\n\n⚠️ Error: {str(e)}")
                
                # Download and send audio/music if available
                music_url = result.get('music_info', {}).get('url')
                if music_url:
                    try:
                        music_caption = (
                            f"🎵 **TikTok Audio**\n\n"
                            f"🎼 **Title:** {result['music_info']['title']}\n"
                            f"👤 **Artist:** {result['music_info']['author']}"
                        )
                        
                        audio_res = requests.get(music_url, timeout=30, stream=True)
                        if audio_res.status_code == 200:
                            audio_filename = f"tiktok_audio_{int(datetime.now().timestamp())}.mp3"
                            with open(audio_filename, 'wb') as f:
                                for chunk in audio_res.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            
                            await client.send_file(
                                target_chat, 
                                audio_filename, 
                                caption=music_caption,
                                voice_note=False,
                                attributes=[types.DocumentAttributeAudio(
                                    duration=result['duration'],
                                    title=result['music_info']['title'],
                                    performer=result['music_info']['author']
                                )]
                            )
                            os.remove(audio_filename)
                    except Exception as e:
                        pass  # Silent fail for audio
                        
            elif result['type'] == 'images':
                total_images = len(result['images'])
                caption = (
                    f"🖼 **TikTok Slideshow** ({total_images} foto)\n\n"
                    f"👤 **Author:** @{result['author']['username']}\n"
                    f"📝 **Title:** {result['title'][:100]}{'...' if len(result['title']) > 100 else ''}\n"
                    f"👁 **Views:** {result['stats']['views']:,}"
                )
                
                # Download semua gambar
                all_files = []
                for idx, img_url in enumerate(result['images'], 1):
                    try:
                        img_res = requests.get(img_url, timeout=20)
                        if img_res.status_code == 200:
                            filename = f"tiktok_img_{int(datetime.now().timestamp())}_{idx}.jpg"
                            with open(filename, 'wb') as f:
                                f.write(img_res.content)
                            all_files.append(filename)
                    except:
                        pass
                
                if all_files:
                    # Split files menjadi chunks of 10
                    for i in range(0, len(all_files), 10):
                        chunk = all_files[i:i+10]
                        is_last_chunk = (i + 10 >= len(all_files))
                        
                        # Caption hanya di chunk terakhir
                        chunk_caption = caption if is_last_chunk else None
                        
                        await client.send_file(target_chat, chunk, caption=chunk_caption)
                    
                    # Hapus semua file
                    for f in all_files:
                        try:
                            os.remove(f)
                        except:
                            pass
                else:
                    await client.send_message(target_chat, f"{caption}\n\n⚠️ Gagal mengunduh gambar")
                
                # Send audio for slideshow too
                music_url = result.get('music_info', {}).get('url')
                if music_url:
                    try:
                        music_caption = (
                            f"🎵 **TikTok Audio**\n\n"
                            f"🎼 **Title:** {result['music_info']['title']}\n"
                            f"👤 **Artist:** {result['music_info']['author']}"
                        )
                        
                        audio_res = requests.get(music_url, timeout=30, stream=True)
                        if audio_res.status_code == 200:
                            audio_filename = f"tiktok_audio_{int(datetime.now().timestamp())}.mp3"
                            with open(audio_filename, 'wb') as f:
                                for chunk in audio_res.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            
                            await client.send_file(
                                target_chat, 
                                audio_filename, 
                                caption=music_caption,
                                voice_note=False,
                                attributes=[types.DocumentAttributeAudio(
                                    duration=result.get('duration', 0),
                                    title=result['music_info']['title'],
                                    performer=result['music_info']['author']
                                )]
                            )
                            os.remove(audio_filename)
                    except Exception as e:
                        pass  # Silent fail for audio
        
        elif platform == 'instagram':
            if result['type'] == 'video':
                video_items = result['videos']
                total_videos = len(video_items)
                
                if total_videos == 1:
                    # Single video - send directly
                    video_url = video_items[0]['url']
                    caption = f"📹 **Instagram Video**"
                    
                    try:
                        video_res = requests.get(video_url, timeout=60, stream=True)
                        if video_res.status_code == 200:
                            video_filename = f"instagram_{int(datetime.now().timestamp())}.mp4"
                            with open(video_filename, 'wb') as f:
                                for chunk in video_res.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            
                            await client.send_file(target_chat, video_filename, caption=caption)
                            os.remove(video_filename)
                        else:
                            await client.send_message(target_chat, f"{caption}\n\n🔗 [Download]({video_url})")
                    except Exception as e:
                        await client.send_message(target_chat, f"{caption}\n\n🔗 [Download]({video_url})")
                else:
                    # Multiple videos - download semua
                    all_files = []
                    for idx, video_item in enumerate(video_items, 1):
                        try:
                            video_url = video_item['url']
                            video_res = requests.get(video_url, timeout=60, stream=True)
                            if video_res.status_code == 200:
                                filename = f"instagram_video_{int(datetime.now().timestamp())}_{idx}.mp4"
                                with open(filename, 'wb') as f:
                                    for chunk in video_res.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                all_files.append(filename)
                        except:
                            pass
                    
                    if all_files:
                        # Split files menjadi chunks of 10
                        for i in range(0, len(all_files), 10):
                            chunk = all_files[i:i+10]
                            is_last_chunk = (i + 10 >= len(all_files))
                            
                            # Caption hanya di chunk terakhir
                            chunk_caption = f"📹 **Instagram Videos** ({len(all_files)} videos)" if is_last_chunk else None
                            
                            await client.send_file(target_chat, chunk, caption=chunk_caption)
                        
                        # Hapus semua file
                        for f in all_files:
                            try:
                                os.remove(f)
                            except:
                                pass
                    else:
                        # Fallback to links
                        for idx, video_item in enumerate(video_items[:5], 1):
                            await client.send_message(target_chat, f"📹 **Instagram Video {idx}**\n\n🔗 [Download]({video_item['url']})")
                            
            elif result['type'] == 'images':
                image_items = result['images']
                total_images = len(image_items)
                
                if total_images == 1:
                    # Single image
                    img_url = image_items[0]['url']
                    caption = f"🖼 **Instagram Image**"
                    
                    try:
                        img_res = requests.get(img_url, timeout=20)
                        if img_res.status_code == 200:
                            filename = f"instagram_{int(datetime.now().timestamp())}.jpg"
                            with open(filename, 'wb') as f:
                                f.write(img_res.content)
                            
                            await client.send_file(target_chat, filename, caption=caption)
                            os.remove(filename)
                        else:
                            await client.send_message(target_chat, f"{caption}\n\n🔗 [Download]({img_url})")
                    except:
                        await client.send_message(target_chat, f"{caption}\n\n🔗 [Download]({img_url})")
                else:
                    # Multiple images - download semua
                    all_files = []
                    for idx, img_item in enumerate(image_items, 1):
                        try:
                            img_url = img_item['url']
                            img_res = requests.get(img_url, timeout=20)
                            if img_res.status_code == 200:
                                filename = f"instagram_img_{int(datetime.now().timestamp())}_{idx}.jpg"
                                with open(filename, 'wb') as f:
                                    f.write(img_res.content)
                                all_files.append(filename)
                        except:
                            pass
                    
                    if all_files:
                        # Split files menjadi chunks of 10
                        for i in range(0, len(all_files), 10):
                            chunk = all_files[i:i+10]
                            is_last_chunk = (i + 10 >= len(all_files))
                            
                            # Caption hanya di chunk terakhir
                            chunk_caption = f"🖼 **Instagram Images** ({len(all_files)} photos)" if is_last_chunk else None
                            
                            await client.send_file(target_chat, chunk, caption=chunk_caption)
                        
                        # Hapus semua file
                        for f in all_files:
                            try:
                                os.remove(f)
                            except:
                                pass
                    else:
                        # Fallback to links
                        for idx, img_item in enumerate(image_items[:10], 1):
                            await client.send_message(target_chat, f"🖼 **Instagram Image {idx}**\n\n🔗 [Download]({img_item['url']})")
                            
            elif result['type'] == 'mixed':
                all_media = result['data']
                total_media = len(all_media)
                
                # Download semua media
                all_files = []
                for idx, media_item in enumerate(all_media, 1):
                    try:
                        media_url = media_item['url']
                        media_type = media_item['type']
                        
                        media_res = requests.get(media_url, timeout=60, stream=True)
                        if media_res.status_code == 200:
                            ext = 'mp4' if media_type == 'video' else 'jpg'
                            filename = f"instagram_mixed_{int(datetime.now().timestamp())}_{idx}.{ext}"
                            
                            with open(filename, 'wb') as f:
                                if media_type == 'video':
                                    for chunk in media_res.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                else:
                                    f.write(media_res.content)
                            
                            all_files.append(filename)
                    except:
                        pass
                
                if all_files:
                    # Hitung total video dan foto
                    video_count = len([m for m in all_media[:len(all_files)] if m['type'] == 'video'])
                    photo_count = len(all_files) - video_count
                    caption = f"📸 **Instagram Media** ({photo_count} photos, {video_count} videos)"
                    
                    # Split files menjadi chunks of 10
                    for i in range(0, len(all_files), 10):
                        chunk = all_files[i:i+10]
                        is_last_chunk = (i + 10 >= len(all_files))
                        
                        # Caption hanya di chunk terakhir
                        chunk_caption = caption if is_last_chunk else None
                        
                        await client.send_file(target_chat, chunk, caption=chunk_caption)
                    
                    # Hapus semua file
                    for f in all_files:
                        try:
                            os.remove(f)
                        except:
                            pass
                else:
                    # Fallback to links
                    for idx, media_item in enumerate(all_media[:5], 1):
                        media_type_emoji = "📹" if media_item['type'] == 'video' else "🖼"
                        media_type_text = "Video" if media_item['type'] == 'video' else "Image"
                        await client.send_message(target_chat, f"{media_type_emoji} **Instagram {media_type_text} {idx}**\n\n🔗 [Download]({media_item['url']})")
            else:
                await client.send_message(target_chat, "❌ Tidak ada media yang ditemukan")
                
        elif platform == 'facebook':  # Tambah Facebook
            if result['results']:
                # Pilih kualitas terbaik
                best_url = get_best_video_url(result['results'], 'facebook')
                
                if best_url:
                    caption = f"📹 **Facebook Video**\n\n{result['caption']}"
                    
                    try:
                        video_res = requests.get(best_url, timeout=60, stream=True)
                        if video_res.status_code == 200:
                            video_filename = f"facebook_{int(datetime.now().timestamp())}.mp4"
                            with open(video_filename, 'wb') as f:
                                for chunk in video_res.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            
                            try:
                                await client.send_file(target_chat, video_filename, caption=caption)
                                os.remove(video_filename)
                            except Exception as e:
                                await client.send_message(event.chat_id, f"❌ Gagal kirim video ke {target_chat}: {str(e)}")
                                os.remove(video_filename)
                                return
                        else:
                            try:
                                await client.send_message(target_chat, f"{caption}\n\n🔗 [Download]({best_url})")
                            except Exception as e:
                                await client.send_message(event.chat_id, f"❌ Gagal kirim pesan ke {target_chat}: {str(e)}")
                                return
                    except Exception as e:
                        try:
                            await client.send_message(target_chat, f"{caption}\n\n🔗 [Download]({best_url})\n\n⚠️ Error: {str(e)}")
                        except Exception as e2:
                            await client.send_message(event.chat_id, f"❌ Gagal kirim pesan ke {target_chat}: {str(e2)}")
                            return
                else:
                    try:
                        await client.send_message(target_chat, "❌ Tidak ada video yang ditemukan")
                    except Exception as e:
                        await client.send_message(event.chat_id, f"❌ Gagal kirim pesan ke {target_chat}: {str(e)}")
                        return
            else:
                try:
                    await client.send_message(target_chat, "❌ Tidak ada media yang ditemukan")
                except Exception as e:
                    await client.send_message(event.chat_id, f"❌ Gagal kirim pesan ke {target_chat}: {str(e)}")
                    return
        
    except Exception as e:
        await client.send_message(target_chat, f"❌ Error mengirim hasil: {str(e)}")

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

        # === PING ===
        if "ping" in acc["features"]:
            @client.on(events.NewMessage(pattern=r"^/ping$"))
            async def ping(event, c=client):
                await ping_handler(event, c)

        # === HEARTBEAT ===
        if "heartbeat" in acc["features"]:
            asyncio.create_task(heartbeat(client, acc["log_admin"], acc["log_channel"], akun_nama))

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
