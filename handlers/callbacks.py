import secrets
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import get_connection, check_subscription
from handlers.keys import process_key_step
from handlers.payments import create_hoodpay_payment
# IMPORTAR LAS FUNCIONES DE PERFIL
from handlers.profile import show_profile, show_referral

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    if call.data == "back_home":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        # Reenviamos /start para refrescar menú
        msg = bot.send_message(call.message.chat.id, "🏠 **Menu Reloaded**", parse_mode="Markdown")
        # Aquí podrías llamar a send_welcome, pero lo más simple es pedir que usen start o reenviar el menú.
        # Para mantener consistencia visual, mejor editamos:
        text = f"BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏\nHello, {call.from_user.first_name}!\n\nSelect an option:"
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

    # PERFIL Y REFERIDOS (CONEXIÓN NUEVA)
    elif call.data == "show_profile":
        # Usamos la lógica del handler profile pero editando mensaje
        # Truco: Llamamos a la función pasando el objeto 'message' original
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_profile(call.message)

    elif call.data == "referral":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_referral(call.message)

    elif call.data == "bot_status":
        bot.answer_callback_query(call.id, "Systems Online ✅")

    # ADMIN PANEL
    elif call.data == "admin_panel":
        if user_id in ADMIN_IDS:
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🔑 1 Day", callback_data="gen_1"), InlineKeyboardButton("🔑 1 Week", callback_data="gen_7"))
            markup.row(InlineKeyboardButton("📜 Logs", callback_data="show_log"), InlineKeyboardButton("ℹ️ Version", callback_data="show_version"))
            markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
            bot.edit_message_text("🕴️ **ADMIN CONTROL**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
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
        bot.send_message(call.message.chat.id, f"✅ Key: `{new_key}` ({days}d)", parse_mode="Markdown")
        bot.answer_callback_query(call.id, "Done")

    # MENUS DE INFO
    elif call.data == "commands":
        text = """
🤖 **COMMANDS LIST**

👤 **User:**
`/start` - Main Menu
`/profile` - Check subscription
`/referral` - Invite link
`/call [no] [service]` - Make call
`/setscript` - Custom Voice
`/myscripts` - My Scripts
`/clean` - Clear Chat

👮‍♂️ **Admin:**
`/create [days]` - Generate Key
        """
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    
    elif call.data == "features":
        text = "🛠️ **FEATURES**\n\n• **Neural Voice:** Real human voices.\n• **DTMF Capture:** Get codes instantly.\n• **Scripts:** Create custom dialogues.\n• **Crypto Payments:** Automatic activation."
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "community":
        text = "🫂 **COMMUNITY**\n\nJoin our channel for updates:\n@YourChannelLink"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "support":
        text = "⛑️ **SUPPORT**\n\nContact Owner: @MatthewOwner\nResponse time: 24h"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # USER ACTIONS
    elif call.data == "enter_key":
        msg = bot.send_message(call.message.chat.id, "🎟️ **Send your Key:**")
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
