import secrets
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import get_connection
from handlers.keys import process_key_step

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    # ==========================================
    # MAIN MENU & NAVIGATION
    # ==========================================
    
    # 🔙 BACK TO MAIN MENU (Re-uses the /start layout but edits the message)
    if call.data == "back_home":
        text = f"""
BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏 (EXAMPLE TEXT)

 Hello, Config Cloud - Matthew! Welcome to the BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏. This bot is used to subsrice to our spoofcall bot and recieve notifications.

BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏 have UNIQUE features that you can't find in any other bot.

 Our bot is an Hybrid between OTP Bot and 3CX. its a professional Social Engineering kit for professional OTP users.

 MODES: Banks, NFCs, Payment Services, Payment Gateways, Brokerages, Stores, Carriers, Emails, Crypto Exchanges, Crypto Hardwares, Social Medias, Cloud Services

 Features included:
 24/7 Support
 Automated Payment System
 Live Panel Feeling
 12+ Pre-made Modes
 Customizable Caller ID / Spoofing
 99.99% Up-time
 Customizable Scripts
 Customizable Panel Actions
 International Support
 Multilingual Support (60+ Voices)
 PGP / Conference Calls
 Live DTMF
 Call Streaming - Listen to call in Real-Time!

⤷ Capture Any OTP.
⤷ Capture Banks OTP.
⤷ Capture Crypto OTP 
⤷ Capture Any Pin Code.
⤷ Capture Any CVV Code
⤷ Get SSN From Victim.
⤷ Capture Voice OTP.
⤷ Get Victim To Approve Message.
⤷ Capture Any Carrier Pin.

 DAILY [$50] / WEEKLY [$150] / MONTHLY [$285]
        """
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🎟️ Enter Key", callback_data="enter_key"),
            InlineKeyboardButton("🚦 Bot Status", callback_data="bot_status"),
            InlineKeyboardButton("🪙 Buy Plan", callback_data="buy_subs"),
            InlineKeyboardButton("🤖 Commands", callback_data="commands"),
            InlineKeyboardButton("🛠️ Features", callback_data="features"),
            InlineKeyboardButton("🫂 Community", callback_data="community"),
            InlineKeyboardButton("👥 Referral", callback_data="referral"),
            InlineKeyboardButton("⛑️ Support", callback_data="support")
        )
        if user_id in ADMIN_IDS:
            markup.add(InlineKeyboardButton("🕴️ ADMIN PANEL", callback_data="admin_panel"))
            
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    # ==========================================
    # ADMIN PANEL DASHBOARD
    # ==========================================
    elif call.data == "admin_panel":
        if user_id in ADMIN_IDS:
            markup = InlineKeyboardMarkup()
            # Row 1: Quick Keys
            markup.row(
                InlineKeyboardButton("🔑 1 Day (+50 USD)", callback_data="gen_1"),
                InlineKeyboardButton("🔑 1 Week (+150 USD)", callback_data="gen_7"),
                InlineKeyboardButton("🔑 1 Month (+285 USD)", callback_data="gen_30")
            )
            # Row 2: Tools
            markup.row(
                InlineKeyboardButton("📜 System Log", callback_data="show_log"),
                InlineKeyboardButton("ℹ️ Version", callback_data="show_version")
            )
            # Row 3: Back
            markup.add(InlineKeyboardButton("⬅ Back to Menu", callback_data="back_home"))
            
            bot.edit_message_text(
                "**ADMIN DASHBOARD**\n\nSelect an action to execute:",
                call.message.chat.id, 
                call.message.message_id, 
                reply_markup=markup,
                parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, "⛔ Access Denied")

    # ADMIN ACTIONS (KEYS GENERATION)
    elif call.data.startswith("gen_"):
        if user_id not in ADMIN_IDS: return
        
        days = int(call.data.split("_")[1]) # Extracts 1, 7 or 30
        new_key = f"KEY-{secrets.token_hex(4).upper()}"
        
        conn = get_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("INSERT INTO otp_licenses (key_code, duration_days) VALUES (%s, %s)", (new_key, days))
                conn.commit()
                cur.close()
                conn.close()
                
                # Show the key with a Copy Button (Using Markdown code block)
                bot.send_message(
                    call.message.chat.id, 
                    f"🟢 **Key Generated**\n\n🔑 Key: `{new_key}`\n⏳ Duration: {days} Days\n\n_Click the key to copy._", 
                    parse_mode="Markdown"
                )
                bot.answer_callback_query(call.id, "Key Created!")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"🔴 Error: {e}")

    # ==========================================
    # USER ACTIONS
    # ==========================================
    
    # ENTER KEY
    elif call.data == "enter_key":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id, 
            "🎟️ **LICENSE ACTIVATION**\n\nPlease enter your access key below.\nFormat example: `KEY-XXXX-YYYY`", 
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, process_key_step)

    # STATUS
    elif call.data == "bot_status":
        bot.answer_callback_query(call.id)
        # Check DB status roughly
        conn = get_connection()
        db_s = "🟢 Online" if conn else "🔴 Offline"
        if conn: conn.close()
        
        bot.send_message(call.message.chat.id, f"🟢 **System Status:** ONLINE\n🗄 **Database:** {db_s}\n⚡ **Latency:** 24ms", parse_mode="Markdown")

    # BUY SUBS
    elif call.data == "buy_subs":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "💰 **Prices:**\n- Daily: $50\n- Weekly: $150\n- Monthly: $285")

    # PLACEHOLDERS
    else:
        bot.answer_callback_query(call.id, "Coming soon!")
