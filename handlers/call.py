from telebot.types import Message
from twilio.rest import Client
from config import bot, TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER, TWILIO_APP_URL

twilio_client = None
if TWILIO_SID and TWILIO_TOKEN:
    try: twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)
    except: pass

@bot.message_handler(commands=['call'])
def handle_call(message: Message):
    if not twilio_client: return bot.reply_to(message, "❌ Twilio not configured")
    
    args = message.text.split()
    if len(args) < 3: return bot.reply_to(message, "Usage: /call +Number Service")
    
    target = args[1]
    service = " ".join(args[2:])
    user_id = message.chat.id
    
    try:
        twiml_url = f"{TWILIO_APP_URL}/twilio/voice?service={service}&user_id={user_id}"
        call = twilio_client.calls.create(
            to=target, from_=TWILIO_NUMBER, url=twiml_url, method='POST'
        )
        bot.reply_to(message, f"📞 Calling... SID: `{call.sid}`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")
