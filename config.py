import os
import telebot
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# DIAGNOSTICS
# ==========================================
print("--- STARTING Config.py ---")

API_TOKEN = os.getenv('API_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

# HOODPAY CONFIGURATION
HOODPAY_MERCHANT_ID = os.getenv('HOODPAY_MERCHANT_ID')
HOODPAY_API_TOKEN = os.getenv('HOODPAY_API_TOKEN')
WEBHOOK_BASE_URL = os.getenv('WEBHOOK_BASE_URL') 

# WEBHOOK LOG CONFIGURATION

LOG_BOT_TOKEN = os.getenv('LOG_BOT_TOKEN')    # Token
LOG_CHANNEL_ID = os.getenv('LOG_CHANNEL_ID')  # Channel ID

if API_TOKEN:
    print(f"🟢 API_TOKEN found.")
else:
    print("🔴 FATAL ERROR: API_TOKEN missing.")

if HOODPAY_API_TOKEN and HOODPAY_MERCHANT_ID:
    print("🟢 HOODPAY Credentials found.")
else:
    print("🟠 WARNING: HOODPAY Credentials missing. Payments won't work.")

print("--- DIAGNOSTICS COMPLETE ---")

# ==========================================
# ADMIN CONFIGURATION
# ==========================================
ADMIN_IDS = [
    934491540, 
    7294894666 
]

# ==========================================
# BOT INITIALIZATION
# ==========================================
if API_TOKEN:
    bot = telebot.TeleBot(API_TOKEN)
else:
    raise ValueError("Stopping bot! API_TOKEN is missing.")
