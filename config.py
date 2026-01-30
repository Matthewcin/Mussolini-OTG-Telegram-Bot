import os
import telebot
from dotenv import load_dotenv

# Cargar variables de entorno locales (si usas .env)
load_dotenv()

print("--- STARTING Config.py ---")

# 1. Telegram Bot Token
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    print("🔴 ERROR: API_TOKEN not found.")
else:
    print("🟢 API_TOKEN found.")

# 2. Database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# 3. Admin IDs (Lista separada por comas)
admin_env = os.getenv("ADMIN_IDS", "")
try:
    ADMIN_IDS = [int(x) for x in admin_env.split(",") if x.strip()]
except:
    ADMIN_IDS = []
    print("⚠️ Warning: No ADMIN_IDS found or invalid format.")

# 4. Twilio Credentials
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

# 5. Hoodpay Credentials (CORREGIDO AQUÍ)
# El código espera HOODPAY_API_KEY, así que leemos eso o HOODPAY_API_TOKEN y lo asignamos
HOODPAY_API_KEY = os.getenv("HOODPAY_API_KEY") or os.getenv("HOODPAY_API_TOKEN")
HOODPAY_BUSINESS_ID = os.getenv("HOODPAY_BUSINESS_ID")

if not HOODPAY_API_KEY:
    print("⚠️ Warning: HOODPAY_API_KEY not found.")

# Inicializar Bot
bot = telebot.TeleBot(API_TOKEN)

print("--- DIAGNOSTICS COMPLETE ---")