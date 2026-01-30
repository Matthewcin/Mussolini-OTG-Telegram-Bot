import os
import secrets
import platform
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from twilio.rest import Client
from config import bot, ADMIN_IDS, TWILIO_SID, TWILIO_TOKEN
from database import (
    get_connection, check_subscription, get_user_balance, deduct_balance, 
    add_balance, save_user_script
)
from handlers.keys import process_key_step
from handlers.payments import create_hoodpay_payment, create_script_invoice, check_payment_status
from handlers.profile import get_profile_content, show_referral

VERSION = "v4.2 (Marketplace Pro)"

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    if call.data.startswith("live_"): return

    # ==========================================
    # 🔙 MAIN MENU
    # ==========================================
    if call.data == "back_home":
        text = f"🛡️ <b>ＢＩＧＦＡＴＯＴＰ</b>\n━━━━━━━━━━━━━━━━━━━━\nHello, <b>{call.from_user.first_name}</b>.\nSelect an option below:"
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🎟️ Enter Key", callback_data="enter_key"),
            InlineKeyboardButton("👤 Profile", callback_data="show_profile"),
            InlineKeyboardButton("🪙 Buy Plan", callback_data="buy_subs"),
            InlineKeyboardButton("🛒 Market", callback_data="market_home"), 
            InlineKeyboardButton("🤖 Commands", callback_data="commands"),
            InlineKeyboardButton("🛠️ Features", callback_data="features"),
            InlineKeyboardButton("👥 Referral", callback_data="referral"),
            InlineKeyboardButton("⛑️ Support", callback_data="support")
        )
        if user_id in ADMIN_IDS:
            markup.add(InlineKeyboardButton("🕴️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", callback_data="admin_panel"))
            
        try: bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

    # ==========================================
    # 🛒 MARKETPLACE BUYING LOGIC
    # ==========================================
    
    # A. Buy with CREDITS
    elif call.data.startswith("buy_cred_"):
        script_id = int(call.data.split("_")[2])
        process_script_purchase(call.message, user_id, script_id, "credits")

    # B. Buy with CRYPTO
    elif call.data.startswith("buy_cryp_"):
        script_id = int(call.data.split("_")[2])
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT title, price FROM otp_market WHERE id = %s", (script_id,))
        item = cur.fetchone()
        conn.close()
        
        if item:
            title, price = item
            create_script_invoice(user_id, script_id, price, title)
            bot.delete_message(call.message.chat.id, call.message.message_id)

    # C. Verify Payment Callback
    elif call.data.startswith("chk_scr_"):
        parts = call.data.split("_")
        pay_id = parts[2]
        script_id = int(parts[3])
        
        if check_payment_status(pay_id):
            process_script_purchase(call.message, user_id, script_id, "crypto")
        else:
            bot.answer_callback_query(call.id, "⏳ Payment not detected yet.", show_alert=True)

    # ==========================================
    # 🛒 MARKETPLACE UI
    # ==========================================
    elif call.data == "market_home":
        text = "🛒 <b>ＳＣＲＩＰＴ  ＭＡＲＫＥＴ</b>\n━━━━━━━━━━━━━━━━━━━━\nManage custom scripts or buy premium ones.\nSelect an option:"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📂 My Scripts", callback_data="show_myscripts"))
        markup.add(InlineKeyboardButton("📚 Free Library", callback_data="show_freescripts"))
        markup.add(InlineKeyboardButton("💎 Premium Shop", callback_data="show_shop"))
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif call.data == "show_myscripts":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT service_name, language FROM otp_scripts WHERE user_id = %s", (user_id,))
        scripts = cur.fetchall()
        conn.close()
        
        if not scripts:
            msg = "📂 <b>ＭＹ  ＳＣＲＩＰＴＳ</b>\n━━━━━━━━━━━━━━━━━━━━\nYou have no scripts.\nUse <code>/setscript</code> to create one."
        else:
            msg = "📂 <b>ＭＹ  ＳＣＲＩＰＴＳ</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            for s in scripts: msg += f"🔹 <code>{s[0]}</code> ({s[1]})\n"
            
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="market_home"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif call.data == "show_shop":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        # We trigger the command logic to avoid duplicating code, or send manual message
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="market_home"))
        bot.send_message(call.message.chat.id, "💎 Use <code>/shop</code> to view items.", reply_markup=markup, parse_mode="HTML")

    elif call.data == "show_freescripts":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="market_home"))
        bot.send_message(call.message.chat.id, "📚 Use <code>/freescripts</code> to view library.", reply_markup=markup, parse_mode="HTML")

    # ==========================================
    # STANDARD MENUS
    # ==========================================
    elif call.data == "show_profile":
        text, markup = get_profile_content(user_id, call.from_user.first_name)
        if text: bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif call.data == "buy_subs":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📅 1 Day ($50)", callback_data="pay_daily"))
        markup.add(InlineKeyboardButton("🗓 1 Week ($150)", callback_data="pay_weekly"))
        markup.add(InlineKeyboardButton("📆 1 Month ($285)", callback_data="pay_monthly"))
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text("💳 <b>SELECT PLAN:</b>", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif call.data in ["pay_daily", "pay_weekly", "pay_monthly"]:
        plan = call.data.split("_")[1]
        create_hoodpay_payment(call.message.chat.id, plan)

    elif call.data == "enter_key":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ Cancel", callback_data="back_home"))
        msg = bot.send_message(call.message.chat.id, "🎟️ <b>Send Key:</b>", reply_markup=markup, parse_mode="HTML")
        bot.register_next_step_handler(msg, process_key_step)

    elif call.data == "admin_panel":
        if user_id in ADMIN_IDS:
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🔑 1 Day", callback_data="gen_1"), InlineKeyboardButton("🔑 1 Week", callback_data="gen_7"))
            markup.row(InlineKeyboardButton("📜 Logs", callback_data="show_log"), InlineKeyboardButton("ℹ️ Info", callback_data="show_version"))
            markup.row(InlineKeyboardButton("📡 Balance", callback_data="admin_twilio"), InlineKeyboardButton("🐞 Debug", callback_data="twilio_debug"))
            markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
            bot.edit_message_text("🕴️ <b>ADMIN DASHBOARD</b>", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # Twilio Debug & Others... (Standard Admin functions omitted for brevity but should be here if you use them)
    # The key parts requested are above.

# ==========================================
# ⚙️ PURCHASE PROCESSING FUNCTION
# ==========================================
def process_script_purchase(message, buyer_id, script_id, payment_method):
    conn = get_connection()
    cur = conn.cursor()
    
    # 1. Check ownership
    cur.execute("SELECT * FROM otp_purchases WHERE user_id = %s AND script_id = %s", (buyer_id, script_id))
    if cur.fetchone():
        conn.close()
        bot.send_message(buyer_id, "✅ You already own this script.")
        return

    # 2. Get script info
    cur.execute("SELECT service_name, language, script_text, title, price, author_id, payout_pref, payout_wallet FROM otp_market WHERE id = %s", (script_id,))
    data = cur.fetchone()
    
    if not data: return
    service, lang, text, title, price, author_id, payout_pref, payout_wallet = data
    price = float(price)
    
    # 3. Charge Buyer (If Credits)
    if payment_method == "credits":
        if not deduct_balance(buyer_id, price):
            conn.close()
            bot.send_message(buyer_id, "💸 <b>Insufficient Credits.</b> Top up or use Crypto.", parse_mode="HTML")
            return
    
    # 4. Install
    cur.execute("INSERT INTO otp_purchases (user_id, script_id) VALUES (%s, %s)", (buyer_id, script_id))
    save_user_script(buyer_id, service, lang, text)
    conn.commit()
    
    # 5. Commission Logic (60%)
    commission = price * 0.60
    
    if payout_pref == "credits":
        add_balance(author_id, commission)
        try: bot.send_message(author_id, f"💰 <b>SALE ALERT!</b>\nSold: {title}\n➕ <b>${commission:.2f}</b> credits added.", parse_mode="HTML")
        except: pass
        
    elif payout_pref == "crypto":
        # Notify Admins for Manual Payout
        for admin in ADMIN_IDS:
            try:
                bot.send_message(admin, 
                    f"⚠️ <b>PAYOUT REQUIRED</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 <b>Seller:</b> <code>{author_id}</code>\n"
                    f"💵 <b>Amount:</b> <code>${commission:.2f}</code>\n"
                    f"🏦 <b>Wallet:</b> <code>{payout_wallet}</code>\n"
                    f"📜 <b>Item:</b> {title}", parse_mode="HTML"
                )
            except: pass
        
        try: bot.send_message(author_id, f"💰 <b>SALE ALERT!</b>\nSold: {title}\n⏳ <b>${commission:.2f}</b> crypto payout processing.", parse_mode="HTML")
        except: pass

    conn.close()
    bot.send_message(buyer_id, f"✅ <b>SUCCESS!</b>\nScript <b>{title}</b> installed.", parse_mode="HTML")