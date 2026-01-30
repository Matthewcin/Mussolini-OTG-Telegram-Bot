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

# Canal para Live Feed (Opcional, si no existe lo dejamos en None)
# Si te da error, ponle un ID de canal o dejalo vacio en Render
LIVE_FEED_CHANNEL_ID = os.getenv("LIVE_FEED_CHANNEL_ID")

# ==========================================
# 2. DATABASE CONFIG
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL")

# ==========================================
# 3. ADMIN CONFIG
# ==========================================
admin_env = os.getenv("ADMIN_IDS", "")
try:
    ADMIN_IDS = [int(x) for x in admin_env.split(",") if x.strip()]
except:
    ADMIN_IDS = []
    print("⚠️ Warning: No ADMIN_IDS found or invalid format.")

# ==========================================
# 4. TWILIO & SERVER CONFIG
# ==========================================
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

# URL de tu servidor en Render (necesaria para los Webhooks de Twilio)
# Render suele dar la variable RENDER_EXTERNAL_URL automaticamente
TWILIO_APP_URL = os.getenv("TWILIO_APP_URL") or os.getenv("RENDER_EXTERNAL_URL")

# ==========================================
# 5. HOODPAY CONFIG
# ==========================================
# Soporte dual para KEY o TOKEN
HOODPAY_API_KEY = os.getenv("HOODPAY_API_KEY") or os.getenv("HOODPAY_API_TOKEN")
HOODPAY_BUSINESS_ID = os.getenv("HOODPAY_BUSINESS_ID")

if not HOODPAY_API_KEY:
    print("⚠️ Warning: HOODPAY_API_KEY not found.")

# ==========================================
# 6. INITIALIZE BOT
# ==========================================
bot = telebot.TeleBot(API_TOKEN)

print("--- DIAGNOSTICS COMPLETE ---")