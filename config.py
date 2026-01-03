import os
import telebot
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# DIAGNOSTICS (Logs In case that Any UPDATE is Wrong...)
# ==========================================
print("--- STARTING Config.py ---")

API_TOKEN = os.getenv('API_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

# Check API TOKEN
if API_TOKEN:
    print(f"🟢 API_TOKEN found. Length: {len(API_TOKEN)} characters.")
else:
    print("🔴 FATAL ERROR: API_TOKEN not found in environment variables.")

# Check DATABASE URL
if DATABASE_URL:
    print("🟢 DATABASE_URL found.")
else:
    print("🔴 FATAL ERROR: DATABASE_URL not found.")

print("--- DIAGNOSTICS COMPLETE ---")

# ==========================================
# ADMIN CONFIGURATION
# ==========================================
# This is the list of User IDs that can access the Admin Panel.
# You must include your ID here.
ADMIN_IDS = [
    934491540, # (Matthew / VirusNTO) <-- Bot Maker
    7294894666 # (Mussolini) <-- Owner
]

# ==========================================
# BOT INITIALIZATION
# ==========================================
if API_TOKEN:
    bot = telebot.TeleBot(API_TOKEN)
else:
    # This stops the script immediately if the token is missing
    raise ValueError("Stopping bot! API_TOKEN environment variable is missing.")
