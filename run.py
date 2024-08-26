import io
import requests
import asyncio
from pyrogram import Client, filters

API_ID = 961780  # Ganti dengan API ID kamu
API_HASH = "bbbfa43f067e1e8e2fb41f334d32a6a7"  # Ganti dengan API Hash kamu
BOT_TOKEN = "7375007973:AAEDZnqXwCGmJ-fmCkT0PuHzdRLFYsKcIAg"

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store progress information for each user
progress_data = {}

# Function to get Instagram video URL
def get_instagram_video_url(ig_url):
    api_url = "https://instagram-scraper-api2.p.rapidapi.com/v1/post_info"
    querystring = {"code_or_id_or_url": ig_url}
    
    headers = {
        "user-agent": "Dart/3.4 (dart:io)",
        "accept": "application/json",
        "x-rapidapi-key": "e72d7fe905mshb603635026144d7p1c183djsna65326362225",
        "accept-encoding": "gzip",
        "host": "instagram-scraper-api2.p.rapidapi.com"
    }

    try:
        response = requests.get(api_url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        
        video_url = data.get("video_url")
        if not video_url:
            for key, value in data.items():
                if isinstance(value, dict):
                    video_url = value.get("video_url")
                    if video_url:
                        break
        
        return video_url

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

# Progress function for tracking download/upload progress
async def progress(current, total):
    print(f"{current * 100 / total:.1f}%")

# Function to download and upload video
async def download_and_upload_video(client, chat_id, user_id, platform, url):
    try:
        progress_data[user_id] = True
        msg_download = await client.send_message(chat_id, f"Sedang mengunduh video dari {platform}...")

        if platform == 'Instagram':
            video_url = get_instagram_video_url(url)
        else:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            data = {
                "url": url
            }
            response = requests.post("https://co.wuk.sh/api/json", headers=headers, json=data)
            result = response.json()
            video_url = result.get("url", None)

        if video_url:
            upload_msg = await client.send_message(chat_id, "Video berhasil diunduh. Sedang mengunggah...")

            # Download video directly to memory without saving to a temporary file
            video_response = requests.get(video_url, stream=True)
            video_content = io.BytesIO(video_response.content)

            # Set the .name attribute for in-memory uploads
            video_content.name = "video.mp4"

            # Upload the video directly with progress tracking
            await client.send_video(chat_id, video_content, supports_streaming=True, progress=progress)

            # Schedule deletion of messages after 10 seconds
            asyncio.create_task(delete_messages(client, chat_id, msg_download.id, upload_msg.id))

        else:
            await client.send_message(chat_id, "Terjadi kesalahan saat mengambil URL video.")

        # Clear progress for the user
        del progress_data[user_id]

    except Exception as e:
        await client.send_message(chat_id, f"Terjadi kesalahan: {str(e)}")
        # Clear progress for the user in case of an error
        if user_id in progress_data:
            del progress_data[user_id]

# Function to delete messages after some time
async def delete_messages(client, chat_id, *message_ids):
    for message_id in message_ids:
        try:
            await client.delete_messages(chat_id, message_id)
        except Exception as e:
            print(f"Failed to delete message {message_id}: {e}")

@app.on_message(filters.command(['ig', 'yt', 'tw', 'tt', 'fb']))
async def download_and_upload(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        command, *args = message.text.split(maxsplit=1)

        if len(args) == 1:
            platform = {
                '/ig': 'Instagram',
                '/yt': 'YouTube',
                '/tw': 'Twitter',
                '/tt': 'TikTok',
                '/fb': 'Facebook'
            }.get(command)

            if platform:
                url = args[0]

                # Check progress for the user
                if user_id in progress_data:
                    await client.send_message(chat_id, f"Anda masih memiliki proses unduhan/upload sebelumnya yang sedang berjalan.")
                else:
                    await download_and_upload_video(client, chat_id, user_id, platform, url)

            else:
                await client.send_message(chat_id, "Perintah salah. Ketik /help untuk bantuan.")

        else:
            await client.send_message(chat_id, "Perintah salah. Ketik /help untuk bantuan.")

    except Exception as e:
        await client.send_message(chat_id, f"Terjadi kesalahan: Report @ilham_maulana1")
        # Clear progress for the user in case of an error
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
