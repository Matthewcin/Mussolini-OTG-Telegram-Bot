import os
import telebot
from dotenv import load_dotenv

# Load environment variables (for local testing)
load_dotenv()

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================

# Telegram Bot Token
API_TOKEN = os.getenv('8527602486:AAE1P1COCYidG7oyjMWANvTMfjfVql2wtJc')

# Database URL (Neon / Postgres)
DATABASE_URL = os.getenv('DATABASE_URL')

# 🛡️ ADMIN IDS CONFIGURATION
# Add the Telegram IDs of the people who can access the Admin Panel.
# Example: ADMIN_IDS = [934491540, 12345678, 98765432]
ADMIN_IDS = [
    934491540  # Developer (Matthew / VirusNTO)
    # 0000000, # Admin 2 (Example)
    # 0000000, # Admin 3 (Example)
]

# Initialize Bot Instance
bot = telebot.TeleBot(API_TOKEN)
