from config import bot
from database import get_connection
from datetime import datetime, timedelta

def process_key_step(message):
    """Validates the key entered by the user."""
    key_input = message.text.strip()
    user = message.from_user
    
    # Prepare user data for the error message
    u_username = f"@{user.username}" if user.username else "No Username"
    u_first = user.first_name if user.first_name else "Unknown"
    u_last = user.last_name if user.last_name else ""
    
    conn = get_connection()
    valid = False
    duration = 0
    
    if conn:
        try:
            cur = conn.cursor()
            # Check if key exists and is active
            cur.execute("SELECT duration_days FROM otp_licenses WHERE key_code = %s AND status = 'active'", (key_input,))
            res = cur.fetchone()
            
            if res:
                valid = True
                duration = res[0]
                # Mark key as used
                cur.execute("UPDATE otp_licenses SET status='used', used_by=%s WHERE key_code=%s", (user.id, key_input))
                # Add time to subscription
                new_end_date = datetime.now() + timedelta(days=duration)
                cur.execute("UPDATE otp_users SET subscription_end=%s WHERE user_id=%s", (new_end_date, user.id))
                conn.commit()
            
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error validating key: {e}")

    # --- RESPONSES ---
    if valid:
        bot.reply_to(message, "🟢 **Nice!**\n\nThanks for Joining. Start using our bot by typing /commands")
    else:
        # CUSTOM ERROR MESSAGE
        error_msg = f"""
BIGFATOTP - OTP BOT

 🟢 Operational | 📈 Uptime: 100%

 Oops! We have detected you don't have a license.

Username: {u_username}
First Name: {u_first}
Last Name: {u_last}
ID : {user.id}

• Restart Bot: /start 
• To Buy Subscription: /buy
"""
        bot.reply_to(message, error_msg)
