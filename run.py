import io
import re
import string
import random
import time
import requests
import asyncio
import tgcrypto
from pyrogram import Client, filters

API_ID = 961780
API_HASH = "bbbfa43f067e1e8e2fb41f334d32a6a7"
BOT_TOKEN = "7375007973:AAEqgy2z2J2-Xii_wOhea98BmwMSdW82bHM"

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store progress information for each user
progress_data = {}

async def progress(current, total):
    print(f"{current * 100 / total:.1f}%")

# Fungsi untuk download video Doodstream
def dood_download(url, file_path):
    def dood_decode(data):
        t = string.ascii_letters + string.digits
        return data + ''.join([random.choice(t) for _ in range(10)])
    
    def append_headers(headers):
        return ''.join([f'&{key}={value}' for key, value in headers.items()])
    
    def extract_host_media_id(url):
        pattern = r'(?://|\.)((?:do*0*o*0*ds?(?:tream)?|ds2(?:play|video))\.' \
                  r'(?:com?|watch|to|s[ho]|cx|l[ai]|w[sf]|pm|re|yt|stream|pro))/(?:d|e)/([0-9a-zA-Z]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)
        else:
            raise ValueError("Invalid DoodStream URL")
    
    RAND_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    host, media_id = extract_host_media_id(url)
    
    if any(host.endswith(x) for x in ['.cx', '.wf']):
        host = 'dood.so'
    
    web_url = f'https://{host}/d/{media_id}'
    headers = {'User-Agent': RAND_UA, 'Referer': f'https://{host}/'}

    r = requests.get(web_url, headers=headers)
    if r.url != web_url:
        host = re.findall(r'(?://|\.)([^/]+)', r.url)[0]
        web_url = f'https://{host}/d/{media_id}'
    headers.update({'Referer': web_url})
    html = r.text

    match = re.search(r'<iframe\s*src="([^"]+)', html)
    if match:
        url = f'https://{host}{match.group(1)}'
        html = requests.get(url, headers=headers).text
    else:
        url = web_url.replace('/d/', '/e/')
        html = requests.get(url, headers=headers).text

    match = re.search(r'''dsplayer\.hotkeys[^']+'([^']+).+?function\s*makePlay.+?return[^?]+([^"]+)''', html, re.DOTALL)
    if match:
        token = match.group(2)
        url = f'https://{host}{match.group(1)}'
        html = requests.get(url, headers=headers).text
        if 'cloudflarestorage.' in html:
            vid_src = html.strip() + append_headers(headers)
        else:
            vid_src = dood_decode(html) + token + str(int(time.time() * 1000)) + append_headers(headers)
        
        response = requests.get(vid_src, stream=True, headers=headers)
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            print(f'Download completed')
        else:
            print(f'Failed to download file')
    else:
        print('Video Not Found')

# Fungsi baru untuk mendapatkan URL video Facebook
def Facebook(api_url, fb_url):
    headers = {
        'authorization': 'erg4t5hyj6u75u64y5ht4gf3er4gt5hy6uj7k8l9',
        'accept-encoding': 'gzip',
        'user-agent': 'okhttp/4.12.0'
    }

    # Format ulang api_url dengan fb_url
    full_url = f"{api_url}?url={fb_url}"

    response = requests.get(full_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if 'media' in data and data['media'][0]['is_video']:
            return data['media'][0]['video_url']
        else:
            return None
    else:
        return None

def get_tiktok_play_url(api_url):
    response = requests.get(api_url, headers={
        'Accept-Encoding': 'gzip',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
        'Host': 'www.tikwm.com',
        'Connection': 'Keep-Alive'
    })

    try:
        data = json.loads(response.text)
        play_url = data.get('data', {}).get('play')
        return play_url if play_url else None
    except json.JSONDecodeError:
        return None

# Function to get Instagram video URL
def get_instagram_video_url(ig_url):
    url = "https://backend.live/rapid"
    headers = {
        "x-api-key": "i094kjad090asd43094@asdj4390945",
        "content-type": "application/json; charset=utf-8",
        "accept-encoding": "gzip",
        "user-agent": "okhttp/5.0.0-alpha.10"
    }
    data = {"url": ig_url}
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("video_url", None)
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

# Function to get video URL for other platforms
def get_video_url(url, platform):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {"url": url}
    response = requests.post("https://co.wuk.sh/api/json", headers=headers, json=data)
    result = response.json()
    return result.get("url", None)

# Download and upload functions for each platform
async def handle_instagram(client, chat_id, url):
    video_url = get_instagram_video_url(url)
    await download_and_upload(client, chat_id, video_url)

async def handle_facebook(client, chat_id, url):
    api_url = 'https://vdfr.aculix.net/fb'
    video_url = Facebook(api_url, url)  # Menggunakan fungsi Facebook yang baru
    await download_and_upload(client, chat_id, video_url)

async def handle_youtube(client, chat_id, url):
    video_url = get_video_url(url, 'YouTube')
    await download_and_upload(client, chat_id, video_url)

async def handle_tiktok(client, chat_id, url):
    tikwm_api_url = f'https://www.tikwm.com/api/?url={url}'
    video_url = get_tiktok_play_url(tikwm_api_url)

    if not video_url:
        video_url = get_video_url(url, 'TikTok')

    await download_and_upload(client, chat_id, video_url)

async def handle_twitter(client, chat_id, url):
    video_url = get_video_url(url, 'Twitter')
    await download_and_upload(client, chat_id, video_url)

# Function to download and upload video
async def download_and_upload(client, chat_id, video_url):
    if video_url:
        upload_msg = await client.send_message(chat_id, "Video berhasil diunduh. Sedang mengunggah...")
        video_response = requests.get(video_url, stream=True)
        video_content = io.BytesIO(video_response.content)
        video_content.name = "video.mp4"
        await client.send_video(chat_id, video_content, supports_streaming=True, progress=progress)
        asyncio.create_task(delete_messages(client, chat_id, upload_msg.id))
    else:
        await client.send_message(chat_id, "Terjadi kesalahan saat mengambil URL video.")

# Function to delete messages after some time
async def delete_messages(client, chat_id, *message_ids):
    for message_id in message_ids:
        try:
            await client.delete_messages(chat_id, message_id)
        except Exception as e:
            print(f"Failed to delete message {message_id}: {e}")

# Handler baru untuk perintah /do
@app.on_message(filters.command(['do']))
async def handle_dood_download(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        command, *args = message.text.split(maxsplit=1)
        if len(args) == 1:
            url = args[0]
            file_path = "video.mp4"  # Lokasi file yang akan diunduh

            if user_id in progress_data:
                await client.send_message(chat_id, f"Anda masih memiliki proses unduhan/upload sebelumnya yang sedang berjalan.")
            else:
                progress_data[user_id] = True
                # Memulai unduhan
                await client.send_message(chat_id, "Memulai unduhan...")
                
                # Panggil fungsi dood_download
                dood_download(url, file_path)
                
                # Mengirim file ke Telegram setelah diunduh
                await client.send_video(chat_id, file_path, supports_streaming=True)
                del progress_data[user_id]
        else:
            await client.send_message(chat_id, "Perintah salah. Ketik /help untuk bantuan.")
    except Exception as e:
        await client.send_message(chat_id, f"Terjadi kesalahan: {str(e)}")
        if user_id in progress_data:
            del progress_data[user_id]

@app.on_message(filters.command(['start', 'help']))
async def send_welcome(client, message):
    help_message = """
📷 /ig [URL] - Unduh video Instagram
📺 /yt [URL] - Ambil video YouTube
🐦 /tw [URL] - Download video Twitter
🎵 /tt [URL] - Unduh video TikTok
📘 /fb [URL] - Unduh video Facebook
💾 /do [URL] - Unduh video dari Doodstream
"""
    await client.reply_text(f"Selamat datang! Gunakan perintah berikut:\n{help_message}")

# Menjalankan bot
app.run()
