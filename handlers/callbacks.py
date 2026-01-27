import secrets
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import get_connection, check_subscription
from handlers.keys import process_key_step
from handlers.payments import create_hoodpay_payment
# IMPORTAR LA NUEVA LÓGICA Y REFERRAL
from handlers.profile import get_profile_content, show_referral

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    # ==========================================
    # 🔙 BACK TO HOME
    # ==========================================
    if call.data == "back_home":
        text = f"BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏\nHello, {call.from_user.first_name}!\n\nSelect an option below:"
        
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
        if user_id in ADMIN_IDS:
            markup.add(InlineKeyboardButton("🕴️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", callback_data="admin_panel"))
            
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    # ==========================================
    # 👤 PERFIL (CORREGIDO)
    # ==========================================
    elif call.data == "show_profile":
        # Usamos la función lógica pasándole el ID del usuario del botón
        text, markup = get_profile_content(user_id, call.from_user.first_name)
        
        if text:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "⚠️ Profile not found. Type /start", show_alert=True)

    elif call.data == "referral":
        # Para referral, como show_referral espera un 'message', lo más fácil es borrar y reenviar
        # o adaptar show_referral. Por ahora, borramos y enviamos nuevo.
        bot.delete_message(call.message.chat.id, call.message.message_id)
        # Creamos un objeto mensaje falso para reutilizar la funcion
        call.message.from_user = call.from_user
        show_referral(call.message)

    elif call.data == "bot_status":
        bot.answer_callback_query(call.id, "✅ Systems Online", show_alert=True)

    # ==========================================
    # 🕴️ ADMIN PANEL
    # ==========================================
    elif call.data == "admin_panel":
        if user_id in ADMIN_IDS:
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🔑 1 Day", callback_data="gen_1"), InlineKeyboardButton("🔑 1 Week", callback_data="gen_7"))
            markup.row(InlineKeyboardButton("📜 Logs", callback_data="show_log"), InlineKeyboardButton("ℹ️ Version", callback_data="show_version"))
            markup.add(InlineKeyboardButton("⬅ Back to Menu", callback_data="back_home"))
            bot.edit_message_text("🕴️ **ADMIN DASHBOARD**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "⛔ Access Denied")

    # GENERAR KEYS
    elif call.data.startswith("gen_"):
        if user_id not in ADMIN_IDS: return
        days = int(call.data.split("_")[1])
        new_key = f"KEY-{secrets.token_hex(4).upper()}"
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO otp_licenses (key_code, duration_days) VALUES (%s, %s)", (new_key, days))
        conn.commit()
        conn.close()
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back to Admin", callback_data="admin_panel"))
        
        bot.edit_message_text(
            f"✅ **Key Created!**\nCode: `{new_key}`\nDays: {days}", 
            call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
        )

    # ==========================================
    # ℹ️ INFO MENUS
    # ==========================================
    elif call.data == "commands":
        text = """
🤖 **COMMANDS LIST**

👤 **User:**
`/start` - Main Menu
`/profile` - Subscription Info
`/call [number] [service]` - OTP Call
`/sms [number] [service]` - Warning SMS
`/cvv [number] [bank]` - CVV Mode
`/setscript` - Custom Voice
`/clean` - Delete History

👮‍♂️ **Admin:**
`/create [days]` - Generate Key
        """
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    
    elif call.data == "features":
        text = "🛠️ **FEATURES**\n\n• **Neural Voice:** Native accents.\n• **DTMF Capture:** Instant logging.\n• **Live Feeds:** Public hits channel.\n• **SMS:** Warmup messages.\n• **CVV Mode:** Capture 3 digits."
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "community":
        text = "🫂 **COMMUNITY**\n\nJoin our official channel:\n👉 @YourChannelHere"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "support":
        text = "⛑️ **SUPPORT**\n\nContact: @MatthewOwner"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # ==========================================
    # 💳 PAYMENTS & KEYS
    # ==========================================
    elif call.data == "enter_key":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ Cancel", callback_data="back_home"))
        msg = bot.send_message(call.message.chat.id, "🎟️ **Send your Key:**", reply_markup=markup)
        bot.register_next_step_handler(msg, process_key_step)

    elif call.data == "buy_subs":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📅 1 Day ($50)", callback_data="pay_daily"))
        markup.add(InlineKeyboardButton("🗓 1 Week ($150)", callback_data="pay_weekly"))
        markup.add(InlineKeyboardButton("📆 1 Month ($285)", callback_data="pay_monthly"))
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text("💳 **Select Plan:**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data in ["pay_daily", "pay_weekly", "pay_monthly", "pay_dev_test"]:
        plan = call.data.split("_")[1]
        if "dev" in call.data: plan = "dev_test"
        create_hoodpay_payment(call.message.chat.id, plan)
        
    else:
        bot.answer_callback_query(call.id, "Coming soon")
