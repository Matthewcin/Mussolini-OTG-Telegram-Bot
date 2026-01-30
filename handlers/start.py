from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS, REFERRAL_BONUS
from database import register_user, add_balance, get_referral_count

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    
    # ==========================================
    # 1. LOGICA DE REFERIDOS
    # ==========================================
    args = message.text.split()
    referrer_id = None
    
    if len(args) > 1:
        try:
            possible_id = int(args[1])
            if possible_id != user.id: # Evitar auto-referirse
                referrer_id = possible_id
        except:
            pass
            
    # Registrar usuario (Devuelve True si es nuevo)
    is_new = register_user(user, referrer_id)

    # Si es nuevo y tiene padrino -> Pagar recompensa
    if is_new and referrer_id:
        try:
            # A) Dar dinero al que invitó
            add_balance(referrer_id, REFERRAL_BONUS)
            
            # B) Obtener contador actualizado
            total_refs = get_referral_count(referrer_id)
            
            # C) Datos del nuevo usuario
            new_user_name = f"@{user.username}" if user.username else user.first_name
            
            # D) Notificación
            notification_msg = f"""
🎉 **New Referral!**

👤 **User:** {new_user_name}
🆔 **ID:** `{user.id}`
🎟 **Code used:** `{referrer_id}`
💰 **Bonus credited:** +${REFERRAL_BONUS} tokens
📊 **Total Referrals:** {total_refs}

_The tokens have been added to your general balance._
            """
            bot.send_message(referrer_id, notification_msg, parse_mode="Markdown")
            
        except Exception as e:
            print(f"Error referral bonus: {e}")

    # ==========================================
    # 2. MENSAJE DE BIENVENIDA
    # ==========================================
    text = f"""
🛡️ **MUSSOLINI OTP BOT v31**
Hello, {user.first_name}! Welcome to the professional Social Engineering kit.

🔥 **MODES:** Banks, Crypto, Social Media.
🟢 **STATUS:** Online

Select an option below:
    """

    # ==========================================
    # 3. BOTONES (ACTUALIZADOS)
    # ==========================================
    markup = InlineKeyboardMarkup(row_width=2)
    
    # ⚡ FILA 1: DASHBOARD (WIZARD) & MARKET (NUEVO)
    markup.add(
        InlineKeyboardButton("⚡ Dashboard", callback_data="open_dashboard"),
        InlineKeyboardButton("🛒 Market", callback_data="market_home")
    )

    # FILA 2: PERFIL & DEPOSITOS
    markup.add(
        InlineKeyboardButton("👤 Profile", callback_data="show_profile"),
        InlineKeyboardButton("🪙 Deposit", callback_data="buy_subs")
    )
    
    # FILA 3: KEYS & REFERIDOS
    markup.add(
        InlineKeyboardButton("🎟️ Redeem Key", callback_data="enter_key"),
        InlineKeyboardButton("👥 Referral", callback_data="referral")
    )

    # FILA 4: EXTRAS
    markup.add(
        InlineKeyboardButton("🛠️ Features", callback_data="features"),
        InlineKeyboardButton("⛑️ Support", callback_data="support")
    )
    
    # FILA ADMIN
    if user.id in ADMIN_IDS:
        markup.add(InlineKeyboardButton("🕴️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", callback_data="admin_panel"))

    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# Handler de soporte (necesario si el botón existe)
@bot.callback_query_handler(func=lambda call: call.data == "support")
def support_handler(call):
    text = (
        "⛑️ **SUPPORT**\n"
        "━━━━━━━━━━━━━━━━\n"
        "Contact Admin for help:\n"
        "👨‍💻 @Mussolini860\n"
        "━━━━━━━━━━━━━━━━\n"
        "Contact Developer for Issues\n"
        "🦠 @whois_tyler (VirusNTO)"
    )
    bot.answer_callback_query(call.id, "Support contact sent.")
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")