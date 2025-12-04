from http.server import BaseHTTPRequestHandler
import os
import datetime
import pytz
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import random

# --- CONFIGURATION ---
# YOU MUST SET THESE IN VERCEL SETTINGS LATER
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID') 

# Set your Exam Date (Year, Month, Day)
TARGET_DATE = datetime.datetime(2026, 8, 1, 0, 0, 0) 
EXAM_NAME = "2026 A/L"

# Daily Quotes List
QUOTES = [
    "The secret of getting ahead is getting started.",
    "It always seems impossible until it is done.",
    "Don't watch the clock; do what it does. Keep going.",
    "Dream big and dare to fail."
]

def get_time_left():
    lk_timezone = pytz.timezone('Asia/Colombo')
    now = datetime.datetime.now(lk_timezone)
    target = TARGET_DATE.astimezone(lk_timezone)
    
    # Calculate difference
    diff = target - now
    days_left = diff.days
    
    # Calculate weeks, hours, minutes
    weeks = days_left // 7
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    return days_left, weeks, hours, minutes, now

def create_image(days_left):
    # Load assets
    try:
        # We use relative paths for Vercel
        img = Image.open(os.path.join(os.getcwd(), 'assets', 'background.jpg'))
        draw = ImageDraw.Draw(img)
        
        # Load Font (Adjust size '150' based on your image size)
        font_path = os.path.join(os.getcwd(), 'assets', 'font.ttf')
        font_large = ImageFont.truetype(font_path, 150) 
        font_small = ImageFont.truetype(font_path, 40)
        
        # Draw "240" (Center it roughly - adjust coordinates as needed)
        # Note: You might need to adjust (W/2, H/2) based on your specific background image
        text_days = str(days_left)
        draw.text((300, 350), text_days, font=font_large, fill="white")
        
        # Draw "DAYS LEFT"
        draw.text((350, 500), "DAYS LEFT", font=font_small, fill="black")
        
        # Save to memory
        bio = io.BytesIO()
        bio.name = 'status.jpg'
        img.save(bio, 'JPEG')
        bio.seek(0)
        return bio
    except Exception as e:
        print(f"Error creating image: {e}")
        return None

def send_telegram_message(image_bio, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = {'photo': image_bio}
    data = {'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'HTML'}
    
    resp = requests.post(url, files=files, data=data)
    return resp.json()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Calculate Time
        days, weeks, hours, mins, now = get_time_left()
        
        # 2. Pick a Quote
        quote = random.choice(QUOTES)
        
        # 3. Create Caption (Using Sinhala/English mix like the image)
        date_str = now.strftime("%Y-%m-%d")
        
        caption = f"""
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

        # 4. Generate Image
        image = create_image(days)
        
        # 5. Send to Telegram
        if image and BOT_TOKEN and CHAT_ID:
            result = send_telegram_message(image, caption)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(str(result).encode('utf-8'))
        else:
            self.send_response(500)
            self.end_headers()
            self.wfile.write("Missing configuration or Image error".encode('utf-8'))
        return
