import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import get_connection
# NEW IMPORTS
from handlers.wizard import start_call_wizard, start_sms_wizard, start_balance_wizard
from handlers.payments import create_hoodpay_payment, create_script_invoice, check_payment_status
from handlers.profile import get_profile_content, show_referral
from handlers.keys import process_key_step
from database import deduct_balance, add_balance, save_user_script, get_all_user_scripts

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    if call.data.startswith("live_") or call.data.startswith("wiz_"): return # Handled elsewhere

    # ==========================================
    # 🔙 MAIN MENU
    # ==========================================
    if call.data == "back_home":
        text = f"🛡️ <b>MUSSOLINI OTP BOT v31</b>\n━━━━━━━━━━━━━━━━━━━━\nHello, <b>{call.from_user.first_name}</b>."
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(InlineKeyboardButton("⚡ Dashboard", callback_data="open_dashboard"),
                   InlineKeyboardButton("🛒 Market", callback_data="market_home"))
        markup.add(InlineKeyboardButton("👤 Profile", callback_data="show_profile"),
                   InlineKeyboardButton("🪙 Deposit", callback_data="buy_subs"))
        markup.add(InlineKeyboardButton("🎟️ Redeem Key", callback_data="enter_key"),
                   InlineKeyboardButton("👥 Referral", callback_data="referral"))
        if user_id in ADMIN_IDS:
            markup.add(InlineKeyboardButton("🕴️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", callback_data="admin_panel"))
            
        try: bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

    # ==========================================
    # ⚡ DASHBOARD (WIZARD LAUNCHER)
    # ==========================================
    elif call.data == "open_dashboard":
        text = "⚡ <b>ＤＡＳＨＢＯＡＲＤ</b>\n━━━━━━━━━━━━━━━━━━━━\nSelect a tool to launch Wizard:"
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("📞 Call", callback_data="wiz_call"),
                   InlineKeyboardButton("📩 SMS", callback_data="wiz_sms"))
        markup.row(InlineKeyboardButton("📂 My Scripts", callback_data="show_myscripts"),
                   InlineKeyboardButton("💎 Shop", callback_data="show_shop"))
        
        if user_id in ADMIN_IDS:
            markup.row(InlineKeyboardButton("🔒 Add Bal", callback_data="wiz_addbal"))
        
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # ==========================================
    # 🛒 MARKET UI
    # ==========================================
    elif call.data == "market_home":
        text = "🛒 <b>ＭＡＲＫＥＴＰＬＡＣＥ</b>\n━━━━━━━━━━━━━━━━━━━━\nSelect option:"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📂 My Scripts", callback_data="show_myscripts"),
                   InlineKeyboardButton("📚 Free Lib", callback_data="show_freescripts"),
                   InlineKeyboardButton("💎 Premium Shop", callback_data="show_shop"))
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif call.data == "show_myscripts":
        scripts = get_all_user_scripts(user_id)
        msg = "📂 <b>MY SCRIPTS</b>\n\n" + ("\n".join([f"🔹 {s[0]}" for s in scripts]) if scripts else "No scripts found.")
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="market_home"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif call.data == "show_shop":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, price FROM otp_market WHERE is_premium = TRUE")
        items = cur.fetchall()
        conn.close()
        msg = "💎 <b>SHOP</b>\n\n" + ("\n".join([f"🔹 {i[1]} (${i[2]}) - ID: {i[0]}" for i in items]) if items else "Shop empty.")
        msg += "\n\nUse <code>/getscript [Name]</code> or <code>/confirmbuy [ID]</code>"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="market_home"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        
    elif call.data == "show_freescripts":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT service_name FROM otp_market WHERE price = 0 OR is_premium = FALSE")
        items = cur.fetchall()
        conn.close()
        msg = "📚 <b>LIBRARY</b>\n\n" + ("\n".join([f"🔹 {i[0]}" for i in items]) if items else "Library empty.")
        msg += "\n\nUse <code>/getscript [Name]</code>"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="market_home"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # ==========================================
    # WIZARD TRIGGERS (Redirects)
    # ==========================================
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

    # ==========================================
    # BUYING LOGIC (Credits vs Crypto)
    # ==========================================
    elif call.data.startswith("buy_cred_"):
        sid = int(call.data.split("_")[2])
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

    # ... (Mantener lógica estándar: profile, subs, keys, admin_panel) ...
    elif call.data == "show_profile":
        text, markup = get_profile_content(user_id, call.from_user.first_name)
        if text: bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    
    elif call.data == "admin_panel":
        if user_id in ADMIN_IDS:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📜 Logs", callback_data="show_log"), InlineKeyboardButton("⬅ Back", callback_data="back_home"))
            bot.edit_message_text("🕴️ <b>ADMIN</b>", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif call.data == "show_log":
        if user_id in ADMIN_IDS:
            try:
                with open("bot.log", "r") as f: lines = f.readlines()[-15:]
                log_text = "".join(lines)
            except: log_text = "No logs."
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("⬅ Back", callback_data="admin_panel"))
            bot.edit_message_text(f"📜 <b>LOGS:</b>\n<pre>{log_text}</pre>", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

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
        
        # Commission (60%)
        comm = price * 0.60
        if pref == "credits": add_balance(author, comm)
        
        conn.commit()
        bot.send_message(buyer_id, f"✅ Bought <b>{title}</b>", parse_mode="HTML")
        try: bot.send_message(author, f"💰 Sold <b>{title}</b> (+${comm})", parse_mode="HTML")
        except: pass
    conn.close()