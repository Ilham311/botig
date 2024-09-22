import io
import requests
import asyncio
import json
import tgcrypto
from pyrogram import Client, filters

API_ID = 961780
API_HASH = "bbbfa43f067e1e8e2fb41f334d32a6a7"
BOT_TOKEN = "7375007973:AAEqgy2z2J2-Xii_wOhea98BmwMSdW82bHM"

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

progress_data = {}

async def progress(current, total):
    print(f"{current * 100 / total:.1f}%")

# Fungsi untuk API Twitter
def twitter_api(twitter_url):
    u = "https://twitter-downloader-download-twitter-videos-gifs-and-images.p.rapidapi.com/status"
    q = {"url": twitter_url}
    h = {
        "x-rapidapi-key": "4f281a1be0msh5baa41ebeeda439p1d1139jsn3c26d05da8dd",
        "x-rapidapi-host": "twitter-downloader-download-twitter-videos-gifs-and-images.p.rapidapi.com",
        "accept-encoding": "gzip",
        "user-agent": "okhttp/4.10.0"
    }

    r = requests.get(u, headers=h, params=q)

    if r.status_code == 200:
        d = r.json()
        for v in d['media']['video']['videoVariants']:
            if v['content_type'] == "video/mp4":
                return v['url']
    return None

# Fungsi untuk mendapatkan URL video Instagram
def get_instagram_media(instagram_url):
    api_url = "https://auto-download-all-in-one.p.rapidapi.com/v1/social/autolink"
    headers = {
        "x-rapidapi-key": "da2822c5a9msh3665ef1bee3ad2cp1ab549jsn457a3b017e06",
        "x-rapidapi-host": "auto-download-all-in-one.p.rapidapi.com",
        "content-type": "application/json; charset=UTF-8",
        "accept-encoding": "gzip",
        "user-agent": "okhttp/3.14.9"
    }
    data = {"url": instagram_url}
    response = requests.post(api_url, json=data, headers=headers)
    return response.json()

# Fungsi untuk mendapatkan URL video Facebook
def get_facebook_video_url(fb_url):
    api_url = "https://vdfr.aculix.net/fb"
    headers = {
        'authorization': 'erg4t5hyj6u75u64y5ht4gf3er4gt5hy6uj7k8l9',
        'accept-encoding': 'gzip',
        'user-agent': 'okhttp/4.12.0'
    }
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

# Fungsi untuk mendapatkan URL video TikTok
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

# Fungsi untuk mendapatkan URL video YouTube atau platform lainnya
def get_video_url(url, platform):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {"url": url}
    response = requests.post("https://co.wuk.sh/api/json", headers=headers, json=data)
    result = response.json()
    return result.get("url", None)

# Download dan upload untuk Instagram
async def handle_instagram(client, chat_id, url):
    media_data = get_instagram_media(url)
    if media_data and not media_data.get('error'):
        video_url = media_data['medias'][0]['url']
        await download_and_upload(client, chat_id, video_url)
    else:
        await client.send_message(chat_id, "Gagal mendapatkan video dari Instagram.")

# Download dan upload untuk Facebook
async def handle_facebook(client, chat_id, url):
    video_url = get_facebook_video_url(url)
    await download_and_upload(client, chat_id, video_url)

# Download dan upload untuk YouTube
async def handle_youtube(client, chat_id, url):
    video_url = get_video_url(url, 'YouTube')
    await download_and_upload(client, chat_id, video_url)

# Download dan upload untuk TikTok
async def handle_tiktok(client, chat_id, url):
    tikwm_api_url = f'https://www.tikwm.com/api/?url={url}'
    video_url = get_tiktok_play_url(tikwm_api_url)
    if not video_url:
        video_url = get_video_url(url, 'TikTok')
    await download_and_upload(client, chat_id, video_url)

# Download dan upload untuk Twitter
async def handle_twitter(client, chat_id, url):
    video_url = twitter_api(url)
    await download_and_upload(client, chat_id, video_url)

# Fungsi untuk mengunduh dan mengunggah video
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

# Fungsi untuk menghapus pesan setelah beberapa waktu
async def delete_messages(client, chat_id, *message_ids):
    for message_id in message_ids:
        try:
            await client.delete_messages(chat_id, message_id)
        except Exception as e:
            print(f"Failed to delete message {message_id}: {e}")

# Menangani perintah unduh dan unggah
@app.on_message(filters.command(['ig', 'yt', 'tw', 'tt', 'fb']))
async def download_and_upload_command(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        command, *args = message.text.split(maxsplit=1)
        if len(args) == 1:
            url = args[0]
            if user_id in progress_data:
                await client.send_message(chat_id, f"Anda masih memiliki proses unduhan/upload sebelumnya yang sedang berjalan.")
            else:
                progress_data[user_id] = True
                platform_handlers = {
                    '/ig': handle_instagram,
                    '/fb': handle_facebook,
                    '/yt': handle_youtube,
                    '/tt': handle_tiktok,
                    '/tw': handle_twitter
                }
                handler = platform_handlers.get(command)
                if handler:
                    await handler(client, chat_id, url)
                else:
                    await client.send_message(chat_id, "Perintah salah. Ketik /help untuk bantuan.")
                del progress_data[user_id]
        else:
            await client.send_message(chat_id, "Perintah salah. Ketik /help untuk bantuan.")
    except Exception as e:
        await client.send_message(chat_id, f"Terjadi kesalahan: {str(e)}")
        if user_id in progress_data:
            del progress_data[user_id]

# Menangani perintah /start dan /help
@app.on_message(filters.command(['start', 'help']))
async def send_welcome(client, message):
    help_message = """
📷 /ig [URL] - Unduh video Instagram
📺 /yt [URL] - Ambil video YouTube
🐦 /tw [URL] - Download video Twitter
🎵 /tt [URL] - Unduh video TikTok
📘 /fb [URL] - Unduh video Facebook
"""
    await client.reply_text(f"Selamat datang! Gunakan perintah berikut:\n{help_message}")

# Menjalankan bot
app.run()
