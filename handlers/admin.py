import secrets
from telebot.types import Message
from config import bot, ADMIN_IDS
from database import get_connection

@bot.message_handler(commands=['create'])
def create_key(message: Message):
    if message.from_user.id not in ADMIN_IDS: return 
    try:
        days = int(message.text.split()[1])
        new_key = f"KEY-{secrets.token_hex(4).upper()}"
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO otp_licenses (key_code, duration_days) VALUES (%s, %s)", (new_key, days))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"Key Created: `{new_key}`", parse_mode="Markdown")
    except:
        bot.reply_to(message, "Usage: /create [days]")

@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if message.from_user.id in ADMIN_IDS:
        bot.reply_to(message, "Welcome Admin. Use /create or the Panel in /start")
