import traceback
from telebot.types import Message
from config import bot
from database import get_connection, add_subscription_days, register_user

# ==========================================
# 1. PROCESSING LOGIC
# ==========================================
def process_key_logic(message: Message):
    """
    Central function to process the key.
    """
    key_input = message.text.strip()
    
    # We use from_user.id to identify the person, not the group
    user_id = message.from_user.id 
    
    print(f"🔑 Processing Key: {key_input} for User: {user_id}")

    # Cancel if it looks like a command
    if key_input.startswith("/") and not key_input.startswith("/redeem"):
        bot.reply_to(message, "⚠️ **Action Cancelled.**", parse_mode="Markdown")
        return

    # Ensure user exists in DB
    register_user(message.from_user)

    conn = get_connection()
    if not conn:
        bot.reply_to(message, "🔴 **System Error:** Database offline.")
        return

    try:
        cur = conn.cursor()
        
        # 1. FIND KEY
        cur.execute("SELECT duration_days FROM otp_licenses WHERE key_code = %s AND status = 'active'", (key_input,))
        result = cur.fetchone()
        
        if result:
            duration = result[0]
            
            # 2. MARK AS USED
            cur.execute("UPDATE otp_licenses SET status='used', used_by=%s WHERE key_code=%s", (user_id, key_input))
            conn.commit()
            
            # 3. ADD TIME
            success, new_date = add_subscription_days(user_id, duration)
            
            if success:
                date_str = new_date.strftime("%Y-%m-%d")
                bot.reply_to(message, f"✅ **License Activated!**\n\n👤 User: {message.from_user.first_name}\n🔑 Key: `{key_input}`\n⏳ Added: {duration} Days\n📅 Expires: `{date_str}`", parse_mode="Markdown")
            else:
                bot.reply_to(message, "⚠️ **Error:** Key accepted but failed to add time. Contact Admin.")
                
        else:
            bot.reply_to(message, "❌ **Invalid Key:**\nKey not found or already used.")
            
        cur.close()
        conn.close()

    except Exception as e:
        print(f"🔴 Key Error: {traceback.format_exc()}")
        bot.reply_to(message, "🔴 **Critical Error** processing key.")


# ==========================================
# 2. HANDLERS
# ==========================================

# A) Next Step Handler
def process_key_step(message):
    process_key_logic(message)

# B) Auto-Detect (Regex)
@bot.message_handler(regexp=r"^KEY-")
def auto_detect_key(message):
    process_key_logic(message)

# C) Manual Command
@bot.message_handler(commands=['redeem'])
def manual_redeem(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "Usage: `/redeem KEY-XXXX`")
        return
    
    message.text = args[1] 
    process_key_logic(message)
