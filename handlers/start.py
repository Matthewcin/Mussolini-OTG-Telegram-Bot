from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS, REFERRAL_BONUS
from database import register_user, add_balance, get_referral_count

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    
    # Lógica de Referidos
    # El comando viene como: "/start 123456"
    args = message.text.split()
    referrer_id = None
    
    if len(args) > 1:
        try:
            possible_id = int(args[1])
            if possible_id != user.id: # Evitar auto-referirse
                referrer_id = possible_id
        except:
            pass
            
    # 1. REGISTRAR USUARIO (Y capturar si es nuevo)
    # register_user devuelve True solo si el usuario NO existía antes
    is_new = register_user(user, referrer_id)

    # 2. SI ES NUEVO Y TIENE PADRINO -> PAGAR RECOMPENSA Y AVISAR
    if is_new and referrer_id:
        try:
            # A) Dar dinero al que invitó
            add_balance(referrer_id, REFERRAL_BONUS)
            
            # B) Obtener contador actualizado
            total_refs = get_referral_count(referrer_id)
            
            # C) Datos del nuevo usuario para el mensaje
            new_user_name = f"@{user.username}" if user.username else user.first_name
            
            # D) MENSAJE EN INGLÉS PARA EL PADRINO
            notification_msg = f"""
🎉 **New Referral!**

👤 **User:** {new_user_name}
🆔 **ID:** `{user.id}`
🎟 **Code used:** `{referrer_id}`
💰 **Bonus credited:** +${REFERRAL_BONUS} tokens
📊 **Total Referrals:** {total_refs}

_The tokens have been added to your general balance._
            """
            
            # Enviar mensaje al Referrer (Padrino)
            bot.send_message(referrer_id, notification_msg, parse_mode="Markdown")
            
        except Exception as e:
            print(f"Error enviando bono de referido: {e}")

    # 3. MENSAJE DE BIENVENIDA AL USUARIO
    text = f"""
BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏
Hello, {user.first_name}! Welcome to the professional Social Engineering kit.

MODES: Banks, Crypto, Social Media.
STATUS: Online 🟢

Select an option below:
    """

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎟️ Enter Key", callback_data="enter_key"),
        InlineKeyboardButton("👤 Profile", callback_data="show_profile"),
        InlineKeyboardButton("🪙 ₿uy Plan", callback_data="buy_subs"),
        InlineKeyboardButton("🤖 Commands", callback_data="commands"),
        InlineKeyboardButton("🛠️ Features", callback_data="features"),
        InlineKeyboardButton("🫂 Community", callback_data="community"),
        InlineKeyboardButton("👥 Referral", callback_data="referral"),
        InlineKeyboardButton("⛑️ Support", callback_data="support")
    )
    
    if user.id in ADMIN_IDS:
        markup.add(InlineKeyboardButton("🕴️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", callback_data="admin_panel"))

    bot.send_message(message.chat.id, text, reply_markup=markup)