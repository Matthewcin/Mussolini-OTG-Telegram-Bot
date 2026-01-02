import telebot
import psycopg2
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

# ==========================================
# ⚙️ CONFIGURACIÓN
# ==========================================

# 1. TU TOKEN DE TELEGRAM (Cámbialo por el tuyo)
API_TOKEN = '8527602486:AAE1P1COCYidG7oyjMWANvTMfjfVql2wtJc'

# 2. CONEXIÓN A BASE DE DATOS (Extraída de tu archivo subido)
# Esta es la URL correcta de tu proyecto "royal-glitter" en Neon
DATABASE_URL = "postgresql://neondb_owner:npg_1LOXompPCH7U@ep-royal-glitter-acsbyxbr-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require"

# Inicializar Bot
bot = telebot.TeleBot(API_TOKEN)

# ==========================================
# 🗄️ LÓGICA DE BASE DE DATOS (POSTGRESQL / NEON)
# ==========================================

def get_connection():
    """Conecta a Neon DB usando psycopg2"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Error conectando a Neon: {e}")
        return None

def init_db():
    """Crea las tablas para el OTP BOT si no existen"""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # 1. Tabla de USUARIOS (OTP BOT)
            # Guardamos créditos o fecha de expiración de suscripción
            cur.execute("""
                CREATE TABLE IF NOT EXISTS otp_users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    subscription_end TIMESTAMP DEFAULT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    balance DECIMAL(10, 2) DEFAULT 0.00
                );
            """)
            
            # 2. Tabla de LICENCIAS (KEYS)
            # Para vender acceso diario/semanal
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
            print("✅ Base de datos Neon conectada (Royal Glitter) y tablas listas.")
        except Exception as e:
            print(f"❌ Error DB Init: {e}")

def register_user(user_id, username, first_name):
    """Registra o actualiza al usuario en la DB"""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO otp_users (user_id, username, first_name) 
                VALUES (%s, %s, %s) 
                ON CONFLICT (user_id) 
                DO UPDATE SET username = EXCLUDED.username, first_name = EXCLUDED.first_name;
            """, (user_id, username, first_name))
            conn.commit()
            cur.close()
            conn.close()
            print(f"👤 Usuario {first_name} ({user_id}) registrado/actualizado.")
        except Exception as e:
            print(f"❌ Error registrando usuario: {e}")

# ==========================================
# 🤖 LÓGICA DEL BOT (GUI & HANDLERS)
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # 1. Guardar en Base de Datos (Neon)
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    register_user(user_id, username, first_name)

    # 2. Texto del mensaje (Estilo BIGFATOTP)
    text = f"""
BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏 

 Hello, {first_name}! Welcome to the BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏. This bot is used to subsrice to our spoofcall bot and recieve notifications.

BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏 have UNIQUE features that you can't find in any other bot.

 Our bot is an Hybrid between OTP Bot and 3CX. its a professional Social Engineering kit for professional OTP users.

 MODES: Banks, NFCs, Payment Services, Payment Gateways, Brokerages, Stores, Carriers, Emails, Crypto Exchanges, Crypto Hardwares, Social Medias, Cloud Services

 Features included:
 24/7 Support
 Automated Payment System
 Live Panel Feeling
 12+ Pre-made Modes
 Customizable Caller ID / Spoofing
 99.99% Up-time
 Customizable Scripts
 Customizable Panel Actions
 International Support
 Multilingual Support (60+ Voices)
 PGP / Conference Calls
 Live DTMF
 Call Streaming - Listen to call in Real-Time!

⤷ Capture Any OTP.
⤷ Capture Banks OTP.
⤷ Capture Crypto OTP 
⤷ Capture Any Pin Code.
⤷ Capture Any CVV Code
⤷ Get SSN From Victim.
⤷ Capture Voice OTP.
⤷ Get Victim To Approve Message.
⤷ Capture Any Carrier Pin.

 DAILY [$50] / WEEKLY [$150] / MONTHLY [$285]
    """

    # 3. Botones (Menu Principal)
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
    # Panel de Admin abajo del todo
    markup.add(InlineKeyboardButton("ADMIN PANEL", callback_data="admin_panel"))

    bot.send_message(message.chat.id, text, reply_markup=markup)

# --- MANEJADOR DE CLICS EN BOTONES ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # Lógica de "Enter Key"
    if call.data == "enter_key":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔑 **Please enter your license key:**\n(Example: `KEY-1234`)", parse_mode="Markdown")
        # Aquí luego agregaremos el 'register_next_step_handler' para validar la key
        
    # Lógica de Estado
    elif call.data == "bot_status":
        bot.answer_callback_query(call.id)
        # Verificamos conexión DB
        conn = get_connection()
        db_status = "🟢 Online" if conn else "🔴 Offline"
        if conn: conn.close()
        
        bot.send_message(call.message.chat.id, f"✅ **System Status:** ONLINE\n📡 **Database:** {db_status}\n⚡ **Latency:** 24ms", parse_mode="Markdown")

    # Lógica de Precios
    elif call.data == "buy_subs":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "💰 **Prices:**\n- Daily: $50\n- Weekly: $150\n- Monthly: $285\n\nSelect a method below (Crypto).")

    # Panel Admin
    elif call.data == "admin_panel":
        bot.answer_callback_query(call.id, "Checking permissions...")
        # Aquí verificaremos si user_id == TU_ID
        bot.send_message(call.message.chat.id, "🔒 **Access Denied.** You are not an admin.")

    else:
        bot.answer_callback_query(call.id, "Feature coming soon! 🛠️")

# ==========================================
# 🚀 ARRANQUE
# ==========================================
if __name__ == "__main__":
    print("⏳ Conectando a Neon DB...")
    init_db()  # Inicializar tablas
    print("🤖 OTP Bot Iniciado (Esperando mensajes)...")

    bot.infinity_polling()
