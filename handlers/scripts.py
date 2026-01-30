from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import bot, ADMIN_IDS
from database import (
    save_user_script, get_all_user_scripts, delete_user_script, 
    check_subscription, get_connection, get_user_script
)

LANGUAGES = {
    "en": "en-US", "es": "es-MX", "es-es": "es-ES",
    "pt": "pt-BR", "fr": "fr-FR", "de": "de-DE", "it": "it-IT"
}

# ==========================================
# 1. CREATE SCRIPT & ACTIONS
# ==========================================
@bot.message_handler(commands=['setscript'])
def set_script(message: Message):
    if not check_subscription(message.chat.id):
        return bot.reply_to(message, "💎 <b>PREMIUM FEATURE</b>\n━━━━━━━━━━━━━━━━━━━━\nPlease buy a plan to access this tool.", parse_mode="HTML")

    try:
        args = message.text.split(maxsplit=3)
        if len(args) < 4: 
            return bot.reply_to(message, "⚠️ <b>USAGE ERROR</b>\nFormat: <code>/setscript [service] [lang] [text]</code>", parse_mode="HTML")
        
        service = args[1].lower()
        lang_code = args[2].lower()
        text = args[3]
        
        if lang_code not in LANGUAGES: 
            return bot.reply_to(message, f"⚠️ <b>INVALID LANGUAGE</b>\nSupported: <code>{', '.join(LANGUAGES.keys())}</code>", parse_mode="HTML")
        
        twilio_lang = LANGUAGES[lang_code]
        
        if save_user_script(message.chat.id, service, twilio_lang, text):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("💰 ＳＥＬＬ  ＳＣＲＩＰＴ", callback_data=f"act_sell_{service}"))
            markup.row(InlineKeyboardButton("🌍 ＰＵＢＬＩＣ", callback_data=f"act_pub_{service}"), 
                       InlineKeyboardButton("🔒 ＰＲＩＶＡＴＥ", callback_data=f"act_priv"))
            
            bot.reply_to(message, 
                f"✨ <b>ＳＣＲＩＰＴ  ＣＲＥＡＴＥＤ</b> ✨\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🏢 <b>Service:</b> <code>{service.upper()}</code>\n"
                f"🗣 <b>Voice:</b> <code>{twilio_lang}</code>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"<i>What would you like to do next?</i>", 
                reply_markup=markup, parse_mode="HTML")
        else:
            bot.reply_to(message, "🔴 <b>SYSTEM ERROR</b>\nDatabase connection failed.", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

# ==========================================
# 2. ACTION CALLBACKS (SELL/PUB/PRIV)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("act_"))
def handle_script_action(call: CallbackQuery):
    action = call.data.split("_")[1]
    
    if action == "priv":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "🔒 Saved privately.")
        return

    try: service = call.data.split("_")[2]
    except: return

    if action == "pub":
        publish_to_market(call.message, call.from_user.id, service, 0.00, "credits")
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif action == "sell":
        msg = bot.edit_message_text(
            f"💰 <b>ＳＥＬＬＩＮＧ  ＭＯＤＥ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Enter the price in <b>USD</b> for <code>{service.capitalize()}</code>:\n"
            f"<i>(Example: 10.50)</i>",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(msg, process_price_step, service)

def process_price_step(message, service):
    try:
        price = float(message.text)
        if price < 1.00: 
            return bot.reply_to(message, "⚠️ <b>ERROR:</b> Minimum price is $1.00", parse_mode="HTML")
        
        # 60/40 Revenue Share Calculation
        user_share = price * 0.60
        admin_share = price * 0.40
        
        text = (
            f"📊 <b>ＲＥＶＥＮＵＥ  ＳＨＡＲＥ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷 <b>Selling Price:</b> <code>${price:.2f}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>You Receive (60%):</b> <code>${user_share:.2f}</code>\n"
            f"🤖 <b>Platform Fee (40%):</b> <code>${admin_share:.2f}</code>\n\n"
            f"👇 <b>Select Payout Method:</b>"
        )
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 CREDITS (Instant)", callback_data=f"paypref_cred_{price}_{service}"))
        markup.add(InlineKeyboardButton("💸 CRYPTO (Hoodpay)", callback_data=f"paypref_cryp_{price}_{service}"))
        
        bot.reply_to(message, text, reply_markup=markup, parse_mode="HTML")
        
    except ValueError:
        bot.reply_to(message, "❌ Invalid number.")

# ==========================================
# 3. PAYOUT PREFERENCE
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("paypref_"))
def handle_payment_preference(call: CallbackQuery):
    # Data: paypref_TYPE_PRICE_SERVICE
    parts = call.data.split("_")
    method = parts[1] # 'cred' or 'cryp'
    price = float(parts[2])
    service = parts[3]
    
    if method == "cred":
        publish_to_market(call.message, call.from_user.id, service, price, "credits")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
    elif method == "cryp":
        msg = bot.edit_message_text(
            "💸 <b>ＣＲＹＰＴＯ  ＳＥＴＵＰ</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Please send your <b>LTC</b> or <b>USDT (TRC20)</b> wallet address:",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(msg, process_wallet_step, service, price)

def process_wallet_step(message, service, price):
    wallet = message.text
    if len(wallet) < 10: 
        return bot.reply_to(message, "⚠️ <b>Invalid Wallet Address.</b>", parse_mode="HTML")
    
    publish_to_market(message, message.from_user.id, service, price, "crypto", wallet)

def publish_to_market(message, user_id, service, price, payout_pref, payout_wallet=None):
    data = get_user_script(user_id, service)
    if not data: return bot.reply_to(message, "❌ Script error.")
    script_text, lang = data
    
    is_prem = True if price > 0 else False
    try: author = message.from_user.first_name
    except: author = "User"
    title = f"{author}'s {service.capitalize()}"
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO otp_market (title, service_name, script_text, price, is_premium, author_id, language, payout_pref, payout_wallet)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (title, service, script_text, price, is_prem, user_id, lang, payout_pref, payout_wallet))
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, 
        f"🚀 <b>ＰＵＢＬＩＳＨＥＤ！</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Item:</b> {title}\n"
        f"💰 <b>Price:</b> ${price}\n"
        f"🏦 <b>Payout:</b> {payout_pref.upper()}", parse_mode="HTML")

# ==========================================
# 4. BUYING COMMAND (MANUAL START)
# ==========================================
@bot.message_handler(commands=['confirmbuy'])
def confirm_buy_command(message: Message):
    try: script_id = int(message.text.split()[1])
    except: return bot.reply_to(message, "Usage: <code>/confirmbuy [ID]</code>", parse_mode="HTML")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT title, price, author_id FROM otp_market WHERE id = %s", (script_id,))
    item = cur.fetchone()
    conn.close()
    
    if not item: return bot.reply_to(message, "❌ Not found.")
    title, price, author_id = item
    
    if author_id == message.from_user.id: 
        return bot.reply_to(message, "❌ Cannot buy your own script.")
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"💳 Pay Credits (${price})", callback_data=f"buy_cred_{script_id}"))
    markup.add(InlineKeyboardButton(f"💸 Pay Crypto (Hoodpay)", callback_data=f"buy_cryp_{script_id}"))
    
    bot.reply_to(message, 
        f"🛒 <b>ＣＨＥＣＫＯＵＴ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Item:</b> {title}\n"
        f"💵 <b>Total:</b> ${price}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Select payment method:</i>", 
        reply_markup=markup, parse_mode="HTML")

# ==========================================
# 5. OTHER COMMANDS
# ==========================================
@bot.message_handler(commands=['myscripts'])
def list_scripts(message):
    if not check_subscription(message.chat.id): return
    scripts = get_all_user_scripts(message.chat.id)
    if not scripts: return bot.reply_to(message, "📭 No custom scripts.")
    msg = "📂 <b>ＭＹ  ＳＣＲＩＰＴＳ</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    for s in scripts: msg += f"🔹 <code>{s[0]}</code> ({s[1]})\n"
    msg += "\n🗑 To delete: <code>/delscript [service]</code>"
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(commands=['delscript'])
def delete_script_cmd(message):
    try: service = message.text.split()[1]
    except: return
    if delete_user_script(message.chat.id, service): bot.reply_to(message, "🗑️ Deleted.")

@bot.message_handler(commands=['buyscript', 'shop'])
def shop_menu(message):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, price, language FROM otp_market WHERE is_premium = TRUE")
    items = cur.fetchall()
    conn.close()
    if not items: return bot.reply_to(message, "📭 Shop is empty.")
    text = "💎 <b>ＰＲＥＭＩＵＭ  ＳＨＯＰ</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for i in items: text += f"🔹 <b>{i[1]}</b>\n🆔 ID: <code>{i[0]}</code> | 💵 <b>${i[2]}</b>\n────────────────\n"
    text += "🛒 To Buy: <code>/confirmbuy [ID]</code>"
    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(commands=['previewscript'])
def preview(message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        sid = int(message.text.split()[1])
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT script_text FROM otp_market WHERE id=%s", (sid,))
        d = cur.fetchone()
        conn.close()
        if d: bot.reply_to(message, f"📜 <b>Script Preview:</b>\n<code>{d[0]}</code>", parse_mode="HTML")
    except: pass

@bot.message_handler(commands=['freescripts'])
def free_scripts(message):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, service_name, language FROM otp_market WHERE price = 0 OR is_premium = FALSE")
    scripts = cur.fetchall()
    conn.close()
    if not scripts: return bot.reply_to(message, "📭 Library empty.")
    text = "📚 <b>ＦＲＥＥ  ＬＩＢＲＡＲＹ</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for s in scripts: text += f"🆔 <code>{s[0]}</code> | <b>{s[1]}</b> ({s[2]})\n"
    text += "\n⬇️ Install: <code>/getscript [ID]</code>"
    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(commands=['getscript'])
def get_free_script(message):
    try: script_id = int(message.text.split()[1])
    except: return bot.reply_to(message, "Usage: <code>/getscript [ID]</code>", parse_mode="HTML")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT service_name, language, script_text, is_premium, title FROM otp_market WHERE id = %s", (script_id,))
    data = cur.fetchone()
    conn.close()
    if not data: return bot.reply_to(message, "❌ Not found.")
    save_user_script(message.from_user.id, data[0], data[1], data[2])
    bot.reply_to(message, f"✅ Installed <b>{data[4]}</b>!", parse_mode="HTML")