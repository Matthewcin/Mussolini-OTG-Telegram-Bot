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

# WEBHOOK LOG & FEEDS CONFIGURATION
LOG_BOT_TOKEN = os.getenv('LOG_BOT_TOKEN')    
LOG_CHANNEL_ID = os.getenv('LOG_CHANNEL_ID')
LIVE_FEED_CHANNEL_ID = os.getenv('LIVE_FEED_CHANNEL_ID') 

# TWILIO CONFIGURATION
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_TOKEN = os.getenv('TWILIO_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER') 
TWILIO_APP_URL = os.getenv('WEBHOOK_BASE_URL')

# ==========================================
# 💰 PRICING SYSTEM (WALLET)
# ==========================================
# Costo por acción (se descuenta del saldo del usuario)
PRICING = {
    "call": 0.50,    # $0.50 por llamada OTP
    "sms": 0.25,     # $0.25 por SMS
    "cvv": 0.50,     # $0.50 por llamada CVV
    "live": 0.00     # El panel live es gratis si ya pagó la llamada
}

# Créditos que recibe el usuario al canjear una Key/Plan
PLAN_CREDITS = {
    "1_day": 5.00,     # Plan diario da $5
    "1_week": 20.00,   # Plan semanal da $20
    "1_month": 50.00   # Plan mensual da $50
}

# 👇 ESTA ES LA LÍNEA QUE TE FALTABA 👇
REFERRAL_BONUS = 0.20  # +$0.20 USD por invitado nuevo

# ==========================================
# CHECKS
# ==========================================
if API_TOKEN:
    print(f"🟢 API_TOKEN found.")
else:
    print("🔴 FATAL ERROR: API_TOKEN missing.")

print("--- DIAGNOSTICS COMPLETE ---")

ADMIN_IDS = [
    934491540, 
    7294894666 
]

if API_TOKEN:
    bot = telebot.TeleBot(API_TOKEN)
else:
    raise ValueError("Stopping bot! API_TOKEN is missing.")