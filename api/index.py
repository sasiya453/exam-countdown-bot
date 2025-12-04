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
# Get these from Vercel Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
DAILY_GROUP_ID = os.environ.get('GROUP_ID') # Your specific Group ID for daily updates

# Exam Date: August 10, 2026
TARGET_DATE = datetime.datetime(2026, 8, 10, 0, 0, 0) 
EXAM_NAME = "2026 A/L"

QUOTES = [
    "The secret of getting ahead is getting started.",
    "It always seems impossible until it is done.",
    "Don't watch the clock; do what it does. Keep going.",
    "Dream big and dare to fail.",
    "Success is the sum of small efforts, repeated day in and day out."
]

# --- HELPER FUNCTIONS ---

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
        # Load Image and Font
        img_path = os.path.join(os.getcwd(), 'assets', 'background.jpg')
        font_path = os.path.join(os.getcwd(), 'assets', 'font.ttf')
        
        img = Image.open(img_path)
        draw = ImageDraw.Draw(img)
        
        # Configure Fonts (Adjust sizes as needed)
        font_large = ImageFont.truetype(font_path, 150) 
        font_small = ImageFont.truetype(font_path, 40)
        
        # Draw "Days Left" Number
        # Centering logic (Adjust 300, 350 to fit your specific background)
        text_days = str(days_left)
        draw.text((300, 350), text_days, font=font_large, fill="white")
        
        # Draw "DAYS LEFT" text below number
        draw.text((350, 500), "DAYS LEFT", font=font_small, fill="black")
        
        # Save to memory buffer
        bio = io.BytesIO()
        bio.name = 'status.jpg'
        img.save(bio, 'JPEG')
        bio.seek(0)
        return bio
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

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

def send_photo(chat_id, image_bio, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = {'photo': image_bio}
    data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'HTML'}
    requests.post(url, files=files, data=data)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    requests.post(url, data=data)

# --- REQUEST HANDLER ---

class handler(BaseHTTPRequestHandler):
    
    # 1. HANDLE CRON JOB (Daily Auto-Send)
    def do_GET(self):
        try:
            days, weeks, hours, mins, now = get_time_details()
            image = create_image(days)
            caption = generate_caption(days, weeks, hours, mins, now)
            
            if image and DAILY_GROUP_ID:
                send_photo(DAILY_GROUP_ID, image, caption)
                self.send_response(200)
                self.wfile.write("Daily Update Sent Successfully".encode('utf-8'))
            else:
                self.send_response(500)
                self.wfile.write("Configuration Error or Image Failed".encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.wfile.write(str(e).encode('utf-8'))

    # 2. HANDLE WEBHOOK (User Commands: /start, /countdown)
    def do_POST(self):
        try:
            content_len = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_len)
            update = json.loads(post_body)

            if 'message' in update:
                chat_id = update['message']['chat']['id']
                text = update['message'].get('text', '').lower() # Convert to lowercase for easier checking

                # COMMAND: /start
                if '/start' in text:
                    welcome_msg = (
                        "👋 <b>Welcome to the A/L 2026 Countdown Bot!</b>\n\n"
                        "I am here to keep you motivated.\n"
                        "Use /countdown to see how much time is left!"
                    )
                    send_message(chat_id, welcome_msg)

                # COMMAND: /countdown
                elif '/countdown' in text:
                    days, weeks, hours, mins, now = get_time_details()
                    image = create_image(days)
                    caption = generate_caption(days, weeks, hours, mins, now)
                    
                    if image:
                        send_photo(chat_id, image, caption)

            self.send_response(200)
            self.wfile.write("OK".encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.wfile.write(str(e).encode('utf-8'))
