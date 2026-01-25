from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import register_user

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    
    # Lógica de Referidos
    # El comando viene como: "/start 123456" (donde 123456 es el ID del que invita)
    args = message.text.split()
    referrer_id = None
    
    if len(args) > 1:
        try:
            possible_id = int(args[1])
            # Evitar auto-referirse
            if possible_id != user.id:
                referrer_id = possible_id
        except:
            pass
            
    # Registramos usuario (y guardamos quién lo invitó si es nuevo)
    register_user(user, referrer_id)

    text = f"""
Mussolini860 - 𝙊𝙏𝙋 𝘽𝙊𝙏
Hello, {user.first_name}! Welcome to the professional Social Engineering kit.

Select an option below:
    """

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎟️ Enter Key", callback_data="enter_key"),
        InlineKeyboardButton("👤 My Profile", callback_data="show_profile"), # <--- NUEVO BOTÓN
        InlineKeyboardButton("🪙 Buy Plan", callback_data="buy_subs"),
        InlineKeyboardButton("🤖 Commands", callback_data="commands"),
        InlineKeyboardButton("🛠️ Features", callback_data="features"),
        InlineKeyboardButton("🫂 Community", callback_data="community"),
        InlineKeyboardButton("👥 Referral", callback_data="referral"),
        InlineKeyboardButton("⛑️ Support", callback_data="support")
    )
    
    if user.id in ADMIN_IDS:
        markup.add(InlineKeyboardButton("🕴️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", callback_data="admin_panel"))

    bot.send_message(message.chat.id, text, reply_markup=markup)
