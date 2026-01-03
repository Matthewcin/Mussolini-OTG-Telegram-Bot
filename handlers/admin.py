import secrets
from config import bot, ADMIN_IDS
from database import get_connection

@bot.message_handler(commands=['create'])
def create_key(message):
    """
    Creates a new license key.
    Usage: /create [days]
    Example: /create 30
    """
    if message.from_user.id not in ADMIN_IDS:
        return # Ignore if not admin
        
    try:
        days = int(message.text.split()[1])
        # Generate a random key like KEY-A1B2
        new_key = f"KEY-{secrets.token_hex(4).upper()}"
        
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO otp_licenses (key_code, duration_days) VALUES (%s, %s)", (new_key, days))
            conn.commit()
            conn.close()
            bot.reply_to(message, f"✅ **Key Created Successfully**\n\n🔑 Code: `{new_key}`\njw Duration: {days} days", parse_mode="Markdown")
    except IndexError:
        bot.reply_to(message, "⚠️ **Usage Error:**\nPlease specify days.\nExample: `/create 30`")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")
