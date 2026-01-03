from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import get_connection

def register_user(user):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO otp_users (user_id, username, first_name, last_name) 
                VALUES (%s, %s, %s, %s) 
                ON CONFLICT (user_id) 
                DO UPDATE SET username=EXCLUDED.username, first_name=EXCLUDED.first_name;
            """, (user.id, user.username, user.first_name, user.last_name))
            conn.commit()
            conn.close()
        except Exception as e: print(e)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    register_user(user)

    text = f"BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏\n\nHello {user.first_name}!..."
    # (Pones aquí todo tu texto largo de bienvenida)

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Enter Key", callback_data="enter_key"),
        InlineKeyboardButton("Bot Status", callback_data="bot_status"),
        # ... resto de botones ...
    )
    
    if user.id in ADMIN_IDS:
        markup.add(InlineKeyboardButton("🔒 ADMIN PANEL", callback_data="admin_panel"))

    bot.send_message(message.chat.id, text, reply_markup=markup)
