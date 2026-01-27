import os
import telebot
from dotenv import load_dotenv

load_dotenv()

print("--- STARTING Config.py ---")

# BOT PRINCIPAL
API_TOKEN = os.getenv('API_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

# HOODPAY
HOODPAY_MERCHANT_ID = os.getenv('HOODPAY_MERCHANT_ID')
HOODPAY_API_TOKEN = os.getenv('HOODPAY_API_TOKEN')
WEBHOOK_BASE_URL = os.getenv('WEBHOOK_BASE_URL') 

# LOGS (BOT SECUNDARIO)
LOG_BOT_TOKEN = os.getenv('LOG_BOT_TOKEN')    
LOG_CHANNEL_ID = os.getenv('LOG_CHANNEL_ID')  

# LIVE FEED (BOT TERCIARIO)
LIVE_FEED_CHANNEL_ID = os.getenv('LIVE_FEED_CHANNEL_ID')

# TWILIO (LLAMADAS)
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_TOKEN = os.getenv('TWILIO_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER') 
TWILIO_APP_URL = os.getenv('WEBHOOK_BASE_URL')

# DIAGNOSTICO
if API_TOKEN: print(f"🟢 API_TOKEN found.")
else: print("🔴 FATAL ERROR: API_TOKEN missing.")

# ADMIN IDS (¡IMPORTANTE! Pon aquí tu ID numérico real)
ADMIN_IDS = [
    934491540, 
    7294894666
]

# INICIALIZAR BOT
if API_TOKEN:
    bot = telebot.TeleBot(API_TOKEN)
else:
    raise ValueError("Stopping bot! API_TOKEN is missing.")
