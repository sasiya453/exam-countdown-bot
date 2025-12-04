from http.server import BaseHTTPRequestHandler
import os
import datetime
import pytz
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import random
import json

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHAT_ID') # This is for the daily broadcast

# Target Date: 2026 August 10
TARGET_DATE = datetime.datetime(2026, 8, 10, 0, 0, 0) 
EXAM_NAME = "2026 A/L"

QUOTES = [
    "The secret of getting ahead is getting started.",
    "It always seems impossible until it is done.",
    "Don't watch the clock; do what it does. Keep going.",
    "Dream big and dare to fail."
]

def get_time_details():
    lk_timezone = pytz.timezone('Asia/Colombo')
    now = datetime.datetime.now(lk_timezone)
    target = TARGET_DATE.astimezone(lk_timezone)
    
    diff = target - now
    days_left = diff.days
    weeks = days_left // 7
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    return days_left, weeks, hours, minutes, now

def create_image(days_left):
    try:
        img = Image.open(os.path.join(os.getcwd(), 'assets', 'background.jpg'))
        draw = ImageDraw.Draw(img)
        font_path = os.path.join(os.getcwd(), 'assets', 'font.ttf')
        font_large = ImageFont.truetype(font_path, 150) 
        font_small = ImageFont.truetype(font_path, 40)
        
        text_days = str(days_left)
        # You might need to adjust these coordinates (300, 350)
        draw.text((300, 350), text_days, font=font_large, fill="white")
        draw.text((350, 500), "DAYS LEFT", font=font_small, fill="black")
        
        bio = io.BytesIO()
        bio.name = 'status.jpg'
        img.save(bio, 'JPEG')
        bio.seek(0)
        return bio
    except Exception as e:
        print(f"Error: {e}")
        return None

def send_telegram_message(chat_id, image_bio, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = {'photo': image_bio}
    data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'HTML'}
    requests.post(url, files=files, data=data)

def generate_caption(days, weeks, hours, mins, now):
    quote = random.choice(QUOTES)
    date_str = now.strftime("%Y-%m-%d")
    return f"""
☁️ <b>Good Morning</b> ✨

🏆 <b>Daily Quote:</b>
<i>"{quote}"</i>

🎖 <b>{EXAM_NAME} විභාගයට තව,</b>

<b>සති {weeks}</b>
<b>දින {days} යි</b>
<b>පැය {hours} යි</b>
<b>මිනිත්තු {mins} යි</b>

📅 <b>අද {date_str}</b>
"""

class handler(BaseHTTPRequestHandler):
    # 1. This handles the Vercel CRON (Daily Timer)
    def do_GET(self):
        days, weeks, hours, mins, now = get_time_details()
        caption = generate_caption(days, weeks, hours, mins, now)
        image = create_image(days)
        
        if image and CHANNEL_ID:
            send_telegram_message(CHANNEL_ID, image, caption)
            self.send_response(200)
            self.wfile.write("Daily Broadcast Sent".encode('utf-8'))
        else:
            self.send_response(500)
            self.wfile.write("Error".encode('utf-8'))

    # 2. This handles USER COMMANDS (Webhook)
    def do_POST(self):
        try:
            content_len = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_len)
            update = json.loads(post_body)

            # Check if it's a message
            if 'message' in update:
                chat_id = update['message']['chat']['id']
                text = update['message'].get('text', '')

                # Listen for the command "/stat"
                if '/stat' in text:
                    days, weeks, hours, mins, now = get_time_details()
                    caption = generate_caption(days, weeks, hours, mins, now)
                    image = create_image(days)
                    
                    if image:
                        # Reset image pointer for reuse if needed, or recreate
                        image.seek(0) 
                        send_telegram_message(chat_id, image, caption)

            self.send_response(200)
            self.wfile.write("OK".encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.wfile.write(str(e).encode('utf-8'))
