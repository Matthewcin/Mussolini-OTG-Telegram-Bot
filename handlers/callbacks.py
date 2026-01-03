from config import bot, ADMIN_IDS
from database import get_connection
from handlers.keys import process_key_step

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    
    # 1. ENTER KEY
    if call.data == "enter_key":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id, 
            "🔑 **LICENSE ACTIVATION**\n\nPlease enter your access key below.\nFormat example: `KEY-XXXX-YYYY`", 
            parse_mode="Markdown"
        )
        # ⚠️ This connects to handlers/keys.py
        bot.register_next_step_handler(msg, process_key_step)

    # 2. STATUS
    elif call.data == "bot_status":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🟢 **System Status:** ONLINE\n⚡ **Latency:** 24ms", parse_mode="Markdown")

    # 3. BUY SUBS
    elif call.data == "buy_subs":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "💰 **Prices:**\n- Daily: $50\n- Weekly: $150\n- Monthly: $285")

    # 4. ADMIN PANEL
    elif call.data == "admin_panel":
        if call.from_user.id in ADMIN_IDS:
            bot.answer_callback_query(call.id, "Admin Mode!")
            bot.send_message(call.message.chat.id, "🕵️ **Admin Panel**\n\nUse `/create [days]` to generate keys.\nExample: `/create 30`", parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "⛔ Access Denied")

    # 5. OTHERS
    else:
        bot.answer_callback_query(call.id, "Coming soon!")
