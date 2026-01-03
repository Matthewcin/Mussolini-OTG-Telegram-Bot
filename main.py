import telebot
import psycopg2
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from threading import Thread # NECESARIO PARA RENDER
from flask import Flask, request # NECESARIO PARA RENDER

# ==========================================
# ⚙️ CONFIGURACIÓN
# ==========================================
# IMPORTANTE: Render a veces guarda las variables de entorno en os.environ
API_TOKEN = '8527602486:AAE1P1COCYidG7oyjMWANvTMfjfVql2wtJc' 
DATABASE_URL = "postgresql://neondb_owner:npg_1LOXompPCH7U@ep-royal-glitter-acsbyxbr-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require"

# ADMIN IDS
ADMIN_IDS = [934491540]

bot = telebot.TeleBot(API_TOKEN)

# ==========================================
# 🗄️ LÓGICA DE BASE DE DATOS
# ==========================================
def get_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"❌ Error DB: {e}")
        return None

def init_db():
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS otp_users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    subscription_end TIMESTAMP DEFAULT NULL,
                    is_admin BOOLEAN DEFAULT FALSE
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS otp_licenses (
                    key_code TEXT PRIMARY KEY,
                    duration_days INT NOT NULL,
                    status TEXT DEFAULT 'active',
                    used_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("✅ DB conectada y tablas listas.")
        except Exception as e:
            print(f"❌ Error Init DB: {e}")

def register_user(user, first_name, last_name, username):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO otp_users (user_id, username, first_name, last_name) 
                VALUES (%s, %s, %s, %s) 
                ON CONFLICT (user_id) 
                DO UPDATE SET username=EXCLUDED.username, first_name=EXCLUDED.first_name, last_name=EXCLUDED.last_name;
            """, (user.id, username, first_name, last_name))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error registro: {e}")

# ==========================================
# 🤖 COMANDO /START
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    register_user(user, user.first_name, user.last_name, user.username)

    text = f"""
BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏 
 Hello, {user.first_name}! Welcome... (Resumido para ahorrar espacio)
 DAILY [$50] / WEEKLY [$150] / MONTHLY [$285]
    """

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Enter Key", callback_data="enter_key"),
        InlineKeyboardButton("Bot Status", callback_data="bot_status"),
        InlineKeyboardButton("Buy Subs", callback_data="buy_subs"),
        InlineKeyboardButton("Commands", callback_data="commands"),
        InlineKeyboardButton("Features", callback_data="features"),
        InlineKeyboardButton("Community", callback_data="community"),
        InlineKeyboardButton("Referral", callback_data="referral"),
        InlineKeyboardButton("Support", callback_data="support")
    )
    
    if user.id in ADMIN_IDS:
        markup.add(InlineKeyboardButton("🔒 ADMIN PANEL", callback_data="admin_panel"))

    bot.send_message(message.chat.id, text, reply_markup=markup)

# ==========================================
# 🔑 LÓGICA DE REDEEM KEY
# ==========================================
def process_key_step(message):
    key_input = message.text.strip()
    user = message.from_user
    user_id = user.id
    
    u_username = f"@{user.username}" if user.username else "No Username"
    u_first = user.first_name if user.first_name else "Unknown"
    u_last = user.last_name if user.last_name else ""
    
    conn = get_connection()
    valid = False
    duration = 0
    
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT duration_days FROM otp_licenses WHERE key_code = %s AND status = 'active'", (key_input,))
            res = cur.fetchone()
            
            if res:
                valid = True
                duration = res[0]
                cur.execute("UPDATE otp_licenses SET status='used', used_by=%s WHERE key_code=%s", (user_id, key_input))
                new_end_date = datetime.now() + timedelta(days=duration)
                cur.execute("UPDATE otp_users SET subscription_end=%s WHERE user_id=%s", (new_end_date, user_id))
                conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error validando key: {e}")

    if valid:
        bot.reply_to(message, "✅ **Success!**\n\nThanks for Join. Start using our bot Typing /commands")
    else:
        error_msg = f"""
BIGFATOTP - OTP BOT
 🟢 Operational | 📈 Uptime: 100%
 Oops! We have detected you don't have a license.

Username: {u_username}
First Name: {u_first}
Last Name: {u_last}
ID : {user_id}
• Restart Bot: /start 
• To Buy Subscription: /buy
"""
        bot.reply_to(message, error_msg)

# ==========================================
# 🖱️ CALLBACKS
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "enter_key":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "🔑 **LICENSE ACTIVATION**\nEnter key:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_key_step)

    elif call.data == "bot_status":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "✅ **System Status:** ONLINE\n⚡ **Latency:** 24ms", parse_mode="Markdown")

    elif call.data == "buy_subs":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "💰 **Prices:**\n- Daily: $50\n- Weekly: $150\n- Monthly: $285")

    elif call.data == "admin_panel":
        if call.from_user.id in ADMIN_IDS:
            bot.answer_callback_query(call.id, "Welcome Admin!")
            bot.send_message(call.message.chat.id, "Use /create [days] to generate keys.")
        else:
            bot.answer_callback_query(call.id, "⛔ Access Denied")
    else:
        bot.answer_callback_query(call.id, "Coming soon!")

@bot.message_handler(commands=['create'])
def create_key(message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        days = int(message.text.split()[1])
        import secrets
        new_key = f"KEY-{secrets.token_hex(4).upper()}"
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO otp_licenses (key_code, duration_days) VALUES (%s, %s)", (new_key, days))
            conn.commit()
            conn.close()
            bot.reply_to(message, f"✅ Key Created:\n`{new_key}`\nDuration: {days} days", parse_mode="Markdown")
    except:
        bot.reply_to(message, "Use: /create [days]")

# ==========================================
# 🌐 SERVIDOR WEB (PARA RENDER) - ESTO ES LO NUEVO
# ==========================================
server = Flask(__name__)

@server.route('/')
def home():
    return "Bot is running OK"

def run_web_server():
    # Render asigna el puerto en la variable de entorno PORT
    # Si no hay variable, usa 8080 por defecto
    port = int(os.environ.get("PORT", 8080))
    server.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

# ==========================================
# 🚀 RUN
# ==========================================
if __name__ == "__main__":
    init_db()
    
    # 1. Iniciar el servidor web falso para engañar a Render
    keep_alive()
    
    # 2. Iniciar el bot
    print("🤖 Bot is running...")
    bot.infinity_polling()
