from config import bot
from database import get_connection
from datetime import datetime, timedelta

def process_key_step(message):
    key_input = message.text.strip()
    user = message.from_user
    conn = get_connection()
    
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT duration_days FROM otp_licenses WHERE key_code = %s AND status = 'active'", (key_input,))
        res = cur.fetchone()
        
        if res:
            duration = res[0]
            cur.execute("UPDATE otp_licenses SET status='used', used_by=%s WHERE key_code=%s", (user.id, key_input))
            
            # Update user time
            new_end = datetime.now() + timedelta(days=duration)
            cur.execute("UPDATE otp_users SET subscription_end=%s WHERE user_id=%s", (new_end, user.id))
            conn.commit()
            bot.reply_to(message, "✅ License Activated!")
        else:
            bot.reply_to(message, "❌ Invalid or Used Key.")
        conn.close()
