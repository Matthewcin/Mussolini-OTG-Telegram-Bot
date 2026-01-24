import secrets
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import get_connection
from handlers.keys import process_key_step
from handlers.payments import create_hoodpay_payment

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    if call.data == "back_home":
        # Redirigimos al start (puedes copiar el markup de start.py aqui)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "🏠 Menu reload: /start")

    # ADMIN PANEL
    elif call.data == "admin_panel":
        if user_id in ADMIN_IDS:
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🔑 1 Day", callback_data="gen_1"), InlineKeyboardButton("🔑 1 Week", callback_data="gen_7"))
            markup.row(InlineKeyboardButton("📜 Logs", callback_data="show_log"), InlineKeyboardButton("ℹ️ Version", callback_data="show_version"))
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

    # MENUS DE INFO
    elif call.data == "commands":
        bot.edit_message_text("🤖 **Commands:**\n/start\n/call [num] [service]\n/buy", call.message.chat.id, call.message.message_id)
    
    elif call.data == "features":
        bot.edit_message_text("🛠️ **Features:**\n- Twilio Voice\n- Hoodpay", call.message.chat.id, call.message.message_id)

    elif call.data == "buy_subs":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📅 1 Day ($50)", callback_data="pay_daily"))
        markup.add(InlineKeyboardButton("🗓 1 Week ($150)", callback_data="pay_weekly"))
        markup.add(InlineKeyboardButton("📆 1 Month ($285)", callback_data="pay_monthly"))
        bot.edit_message_text("💳 **Select Plan:**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data in ["pay_daily", "pay_weekly", "pay_monthly", "pay_dev_test"]:
        plan = call.data.split("_")[1]
        if "dev" in call.data: plan = "dev_test"
        create_hoodpay_payment(call.message.chat.id, plan)

    elif call.data == "enter_key":
        msg = bot.send_message(call.message.chat.id, "🎟️ Send Key:")
        bot.register_next_step_handler(msg, process_key_step)
        
    else:
        bot.answer_callback_query(call.id, "Coming soon")
