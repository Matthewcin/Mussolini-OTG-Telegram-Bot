import os
import telebot
from dotenv import load_dotenv

# Cargar variables de entorno locales (si usas .env)
load_dotenv()

print("--- STARTING Config.py ---")

# ==========================================
# 1. TELEGRAM CONFIG
# ==========================================
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    print("🔴 ERROR: API_TOKEN not found.")
else:
    print("🟢 API_TOKEN found.")

LIVE_FEED_CHANNEL_ID = os.getenv("LIVE_FEED_CHANNEL_ID")

# ==========================================
# 2. DATABASE CONFIG
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL")

# ==========================================
# 3. ADMIN CONFIG
# ==========================================
default_admins = "934491540,7294894666"
admin_env = os.getenv("ADMIN_IDS", default_admins)

try:
    ADMIN_IDS = [int(x) for x in admin_env.split(",") if x.strip()]
except:
    ADMIN_IDS = [934491540, 7294894666]
    print("⚠️ Warning: Using default Admin IDs.")

# ==========================================
# 4. TWILIO CONFIG
# ==========================================
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
TWILIO_APP_URL = os.getenv("TWILIO_APP_URL") or os.getenv("RENDER_EXTERNAL_URL")

# ==========================================
# 5. HOODPAY CONFIG (CORREGIDO)
# ==========================================
# Usamos exactamente los nombres que tienes en Render
HOODPAY_API_TOKEN = os.getenv("HOODPAY_API_TOKEN")
HOODPAY_MERCHANT_ID = os.getenv("HOODPAY_MERCHANT_ID")

if not HOODPAY_API_TOKEN:
    print("⚠️ Warning: HOODPAY_API_TOKEN not found.")

# ==========================================
# 6. ECONOMY & PRICING
# ==========================================
try:
    REFERRAL_BONUS = float(os.getenv("REFERRAL_BONUS", "2.00"))
except:
    REFERRAL_BONUS = 2.00

PLAN_CREDITS = {
    1: 0.00,
    7: 2.00,
    30: 5.00
}

PRICING = {
    "call_base": 0.50,
    "call_per_minute": 0.20
}

# ==========================================
# 7. INITIALIZE BOT
# ==========================================
bot = telebot.TeleBot(API_TOKEN)

print("--- DIAGNOSTICS COMPLETE ---")