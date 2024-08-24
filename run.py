import telebot
import requests
import io
import tempfile
import threading
import time

TOKEN_BOT = "5219568853:AAGHeoGpVXMCHxqK20kYsp5nGSHFEOQt4eQ"
bot = telebot.TeleBot(TOKEN_BOT)

CHANNEL_USERNAME = "@BypasserID"

# Dictionary to store progress information for each user
progress_data = {}

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
            # Telusuri lebih dalam jika video_url tidak ditemukan di level atas
            for key, value in data.items():
                if isinstance(value, dict):
                    video_url = value.get("video_url")
                    if video_url:
                        break
        
        return video_url

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

def get_facebook_video_url(fb_url):
    url = 'https://aiovideodownloader.com/api/facebook'
    params = {'url': fb_url}
    headers = {
        'Host': 'aiovideodownloader.com',
        'accept-encoding': 'gzip',
        'user-agent': 'okhttp/4.9.2',
        'if-none-match': '"nm0oji8s3o1st"'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'hd' in data:
            return data['hd']
        elif 'sd' in data:
            return data['sd']
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except ValueError as e:
        print(f"JSON decoding error: {e}")
        print(f"Response content: {response.text}")
        return None

def download_and_upload_video(chat_id, user_id, platform, url):
    try:
        progress_data[user_id] = True
        msg_download = bot.send_message(chat_id, f"Sedang mengunduh video dari {platform}...")

        if platform == 'Instagram':
            video_url = get_instagram_video_url(url)
        elif platform == 'Facebook':
            video_url = get_facebook_video_url(url)
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
            upload_msg = bot.send_message(chat_id, "Video berhasil diunduh. Sedang mengunggah...")

            # Download video directly to memory without saving to a temporary file
            video_response = requests.get(video_url, stream=False)
            video_content = io.BytesIO(video_response.content)

            # Upload the video directly
            bot.send_video(chat_id, video_content, timeout=40, supports_streaming=True)

            # Schedule deletion of messages after 10 seconds
            threading.Timer(10.0, delete_messages, args=(chat_id, msg_download.message_id, upload_msg.message_id)).start()

        else:
            bot.send_message(chat_id, "Terjadi kesalahan saat mengambil URL video.")

        # Clear progress for the user
        del progress_data[user_id]

    except Exception as e:
        bot.send_message(chat_id, f"Terjadi kesalahan: {str(e)}")
        # Clear progress for the user in case of an error
        if user_id in progress_data:
            del progress_data[user_id]

def delete_messages(chat_id, *message_ids):
    for message_id in message_ids:
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"Failed to delete message {message_id}: {e}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    is_member = bot.get_chat_member(CHANNEL_USERNAME, user_id).status in ['member', 'administrator']

    if is_member:
        help_message = """
📷 /ig [URL] - Unduh video Instagram
📺 /yt [URL] - Ambil video YouTube
🐦 /tw [URL] - Download video Twitter
🎵 /tt [URL] - Unduh video TikTok
📘 /fb [URL] - Unduh video Facebook
"""
        bot.reply_to(message, f"Selamat datang! Gunakan perintah berikut:\n{help_message}")
    else:
        bot.reply_to(message, f"Maaf, Anda harus bergabung dengan saluran {CHANNEL_USERNAME} terlebih dahulu untuk menggunakan bot ini.")

@bot.message_handler(commands=['ig', 'yt', 'tw', 'tt', 'fb'])
def download_and_upload(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    is_member = bot.get_chat_member(CHANNEL_USERNAME, user_id).status in ['member', 'administrator']

    if message.chat.type == 'private' or message.chat.id == -1001438313485:
        if is_member:
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
                            bot.send_message(chat_id, f"Anda masih memiliki proses unduhan/upload sebelumnya yang sedang berjalan.")
                        else:
                            download_and_upload_video(chat_id, user_id, platform, url)

                    else:
                        bot.send_message(chat_id, "Perintah salah. Ketik /help untuk bantuan.")

                else:
                    bot.send_message(chat_id, "Perintah salah. Ketik /help untuk bantuan.")

            except Exception as e:
                bot.send_message(chat_id, f"Terjadi kesalahan: Report @ilham_maulana1")
                # Clear progress for the user in case of an error
                if user_id in progress_data:
                    del progress_data[user_id]
        else:
            bot.send_message(chat_id, f"Maaf, Anda harus bergabung dengan saluran {CHANNEL_USERNAME} terlebih dahulu untuk menggunakan bot ini.")
    else:
        bot.reply_to(message, "Maaf, bot ini tidak dapat digunakan di grup.")

while True:
    try:
        bot.polling()
    except Exception as e:
        print(f"Bot crash: {str(e)}")
        time.sleep(3)  # Delay for 3 seconds before attempting to restart
