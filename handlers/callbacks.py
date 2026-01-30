import os
import secrets
import platform
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from twilio.rest import Client
from config import bot, ADMIN_IDS, TWILIO_SID, TWILIO_TOKEN
from database import get_connection, check_subscription
from handlers.keys import process_key_step
from handlers.payments import create_hoodpay_payment
from handlers.profile import get_profile_content, show_referral

# Versión del Sistema
VERSION = "v3.5 (Live Panel & Wallet Edition)"

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    # ⚠️ IMPORTANTE: Si el callback empieza con "live_", lo ignoramos en este archivo
    # para que lo maneje handlers/live.py (si está importado en main.py antes o después).
    if call.data.startswith("live_"):
        return

    # ==========================================
    # 🔙 BACK TO HOME (MENÚ PRINCIPAL)
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
        # Botón de Admin solo si es admin
        if user_id in ADMIN_IDS:
            markup.add(InlineKeyboardButton("🕴️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", callback_data="admin_panel"))
            
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

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
        # Borramos el mensaje anterior para enviar uno nuevo limpio
        bot.delete_message(call.message.chat.id, call.message.message_id)
        # Simulamos que el usuario envió el comando /referral
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
        # REEMPLAZA ESTOS LINKS CON LOS TUYOS REALES
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
            # Fila 1: Generar Keys
            markup.row(InlineKeyboardButton("🔑 1 Day", callback_data="gen_1"), InlineKeyboardButton("🔑 1 Week", callback_data="gen_7"))
            # Fila 2: Logs y Version
            markup.row(InlineKeyboardButton("📜 View Logs", callback_data="show_log"), InlineKeyboardButton("ℹ️ System Info", callback_data="show_version"))
            # Fila 3: Twilio
            markup.add(InlineKeyboardButton("📡 Twilio Balance & Info", callback_data="admin_twilio"))
            # Fila 4: Volver
            markup.add(InlineKeyboardButton("⬅ Back to Menu", callback_data="back_home"))
            
            bot.edit_message_text("🕴️ **ADMIN DASHBOARD**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "⛔ Access Denied")

    # ==========================================
    # 📡 ADMIN TWILIO CHECKER
    # ==========================================
    elif call.data == "admin_twilio":
        if user_id not in ADMIN_IDS: return

        bot.answer_callback_query(call.id, "🔄 Fetching data from Twilio...")
        
        try:
            client = Client(TWILIO_SID, TWILIO_TOKEN)
            
            # 1. Obtener Info de Cuenta (Saldo y Estado)
            try:
                balance_data = client.api.v2010.accounts(TWILIO_SID).balance.fetch()
                balance = f"{balance_data.balance} {balance_data.currency}"
            except:
                balance = "Unknown (Check Console)"

            account = client.api.v2010.accounts(TWILIO_SID).fetch()
            status = account.status.upper()
            type_acc = account.type.upper() # Trial o Full

            # 2. Obtener Lista de Números (Límite 10)
            numbers = client.incoming_phone_numbers.list(limit=10)
            nums_text = ""
            if numbers:
                for n in numbers:
                    cap = []
                    if n.capabilities.get('voice'): cap.append("🎤")
                    if n.capabilities.get('sms'): cap.append("📩")
                    nums_text += f"🔹 `{n.phone_number}` {' '.join(cap)}\n"
            else:
                nums_text = "❌ No numbers found."

            info_msg = f"""
📡 **TWILIO STATUS REPORT**
━━━━━━━━━━━━━━━━━━━━
💰 **Balance:** `{balance}`
📊 **Status:** {status}
🏷 **Type:** {type_acc}

📱 **Active Numbers:**
{nums_text}
            """
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("⬅ Back to Admin", callback_data="admin_panel"))
            
            bot.edit_message_text(info_msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

        except Exception as e:
            bot.edit_message_text(f"❌ **Twilio API Error:**\n`{str(e)}`\n\nCheck your SID/Token in config.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    # ==========================================
    # 📜 ADMIN LOGS VIEWER
    # ==========================================
    elif call.data == "show_log":
        if user_id not in ADMIN_IDS: return
        
        try:
            # Intentamos leer el archivo bot.log
            if os.path.exists("bot.log"):
                with open("bot.log", "r") as f:
                    lines = f.readlines()
                    # Mostramos solo las últimas 15 líneas para no saturar
                    last_lines = "".join(lines[-15:]) 
                
                log_text = f"📜 **SYSTEM LOGS (Last 15 lines):**\n\n```\n{last_lines}```"
            else:
                log_text = "⚠️ **Log file not found.** (No activity yet or file missing)"

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔄 Refresh Logs", callback_data="show_log"))
            markup.add(InlineKeyboardButton("⬅ Back to Admin", callback_data="admin_panel"))
            
            bot.edit_message_text(log_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
            
        except Exception as e:
            bot.answer_callback_query(call.id, f"Error reading logs: {e}")

    # ==========================================
    # ℹ️ SYSTEM INFO / VERSION
    # ==========================================
    elif call.data == "show_version":
        if user_id not in ADMIN_IDS: return
        
        sys_info = f"Python {platform.python_version()} on {platform.system()}"
        
        text = f"""
ℹ️ **SYSTEM INFORMATION**
━━━━━━━━━━━━━━━━━━
🤖 **Bot Version:** `{VERSION}`
🐍 **Environment:** {sys_info}
📡 **Server:** Render Cloud / Linux
🟢 **Status:** Online & Listening
        """
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="admin_panel"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # ==========================================
    # 🔑 GENERAR KEYS (ADMIN)
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
        
        bot.edit_message_text(
            f"✅ **Key Created Successfully!**\n\n🔑 Code: `{new_key}`\n⏳ Duration: {days} Days", 
            call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
        )

    # ==========================================
    # ℹ️ MENÚS DE INFORMACIÓN Y AYUDA
    # ==========================================
    elif call.data == "commands":
        text = """
🤖 **COMMANDS LIST**

👤 **User:**
`/start` - Main Menu
`/profile` - Check Credits & Sub
`/call [number] [service]` - OTP Call ($0.50)
`/sms [number] [service]` - Warning SMS ($0.25)
`/cvv [number] [bank]` - CVV Mode ($0.50)
`/setscript` - Custom Voice
`/myscripts` - Manage Scripts
`/clean` - Delete History

👮‍♂️ **Admin:**
`/create [days]` - Generate Key
`/addbalance [id] [amount]` - Give Money
        """
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    
    elif call.data == "features":
        text = "🛠️ **FEATURES**\n\n• **Neural Voice:** Native accents (US, MX, ES, BR).\n• **Live Panel:** Approve/Reject codes in real-time.\n• **Wallet System:** Pay per use credits.\n• **SMS:** Warmup messages.\n• **CVV Mode:** Capture 3 digits."
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "support":
        text = "⛑️ **SUPPORT**\n\nNeed help with a payment or setup?\n\nContact Owner: @MatthewOwner\n_Response time: 2-4 hours_"
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
        markup.add(InlineKeyboardButton("❌ Cancel / Back", callback_data="back_home"))
        
        msg = bot.send_message(call.message.chat.id, "🎟️ **REDEEM LICENSE**\n\nPlease paste your Key below (e.g., `KEY-XXXX`):", reply_markup=markup, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_key_step)

    elif call.data == "buy_subs":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📅 1 Day ($50)", callback_data="pay_daily"))
        markup.add(InlineKeyboardButton("🗓 1 Week ($150)", callback_data="pay_weekly"))
        markup.add(InlineKeyboardButton("📆 1 Month ($285)", callback_data="pay_monthly"))
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        
        bot.edit_message_text("💳 **SELECT SUBSCRIPTION PLAN**\n\nChoose your license duration. Activation is automatic.", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data in ["pay_daily", "pay_weekly", "pay_monthly", "pay_dev_test"]:
        plan = call.data.split("_")[1]
        if "dev" in call.data: plan = "dev_test"
        create_hoodpay_payment(call.message.chat.id, plan)
        
    else:
        bot.answer_callback_query(call.id, "Coming soon")
