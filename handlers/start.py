from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import register_user

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    register_user(user)

    text = f"""
BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏
Hello, {user.first_name}! Welcome to Mussolini OTP Bot.

Select an option below:
    """

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎟️ Enter Key", callback_data="enter_key"),
        InlineKeyboardButton("📊 Bot Status", callback_data="bot_status"),
        InlineKeyboardButton("🪙 ₿uy Plan", callback_data="buy_subs"),
        InlineKeyboardButton("🤖 Commands", callback_data="commands"),
        InlineKeyboardButton("🛠️ Features", callback_data="features"),
        InlineKeyboardButton("🫂 Community", callback_data="community"),
        InlineKeyboardButton("👥 Referral", callback_data="referral"),
        InlineKeyboardButton("⛑️ Support", callback_data="support")
    )
    
    # Solo mostrar panel si es admin
    if user.id in ADMIN_IDS:
        markup.add(InlineKeyboardButton("🕴️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", callback_data="admin_panel"))

    bot.send_message(message.chat.id, text, reply_markup=markup)
