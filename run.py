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

# Dictionary to store progress information for each user
progress_data = {}

async def progress(current, total):
    print(f"{current * 100 / total:.1f}%")

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
    video_url = get_video_url(url, 'Facebook')
    await download_and_upload(client, chat_id, video_url)

async def handle_youtube(client, chat_id, url):
    video_url = get_video_url(url, 'YouTube')
    await download_and_upload(client, chat_id, video_url)

async def handle_tiktok(client, chat_id, url):
    # Menggunakan TikWM API untuk mendapatkan play URL
    tikwm_api_url = f'https://www.tikwm.com/api/?url={url}'
    video_url = get_tiktok_play_url(tikwm_api_url)

    if not video_url:  # Jika TikWM gagal, coba gunakan API default
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

# Run the bot
app.run()
