from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import bot, ADMIN_IDS
from database import (
    save_user_script, get_all_user_scripts, delete_user_script, 
    check_subscription, get_connection, get_user_script, get_market_script_by_name
)

LANGUAGES = {
    "en": "en-US", "es": "es-MX", "es-es": "es-ES",
    "pt": "pt-BR", "fr": "fr-FR", "de": "de-DE", "it": "it-IT"
}

# ==========================================
# 🔍 GET SCRIPT (SMART)
# ==========================================
@bot.message_handler(commands=['getscript'])
def get_script_by_name_cmd(message: Message):
    # Check Args
    try: query = message.text.split(maxsplit=1)[1]
    except IndexError: return bot.reply_to(message, "⚠️ Usage: <code>/getscript [Name]</code>", parse_mode="HTML")

    # DB Search
    script_data = get_market_script_by_name(query)
    
    if not script_data:
        return bot.reply_to(message, f"❌ Script <b>'{query}'</b> not found in Market.", parse_mode="HTML")
    
    # Unpack data
    sid, title, price, is_prem, text, service, lang = script_data
    price = float(price)

    # A) FREE Script -> Install immediately
    if not is_prem or price <= 0:
        save_user_script(message.from_user.id, service, lang, text)
        bot.reply_to(message, 
            f"✅ <b>INSTALLED!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>Script:</b> {title}\n"
            f"🏢 <b>Service:</b> {service}\n"
            f"🗣 <b>Lang:</b> {lang}\n"
            f"<i>Added to library.</i>", 
            parse_mode="HTML")
            
    # B) PREMIUM Script -> Show Menu
    else:
        # Blurred preview logic
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"👁️ Preview (Blurred)", callback_data=f"view_prem_{sid}"))
        markup.add(InlineKeyboardButton(f"🛒 Buy for ${price}", callback_data=f"buy_opt_{sid}"))
        markup.add(InlineKeyboardButton("⬅️ Cancel", callback_data="del_msg"))
        
        bot.reply_to(message, 
            f"💎 <b>PREMIUM SCRIPT FOUND</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>Name:</b> {title}\n"
            f"💰 <b>Price:</b> ${price}\n"
            f"🔒 <b>Status:</b> Locked", 
            reply_markup=markup, parse_mode="HTML")

# ==========================================
# 🕹️ GETSCRIPT CALLBACKS
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("view_prem_"))
def view_premium_preview(call: CallbackQuery):
    try:
        sid = int(call.data.split("_")[2])
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT script_text, title FROM otp_market WHERE id=%s", (sid,))
        res = cur.fetchone()
        conn.close()
        
        if res:
            text = res[0]
            title = res[1]
            censored = text[:50] + " ... " + ("▒" * 30) + "\n\n(Purchase to unlock)"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🛒 Buy Now", callback_data=f"buy_opt_{sid}"))
            markup.add(InlineKeyboardButton("⬅ Back", callback_data="del_msg"))
            
            bot.edit_message_text(
                f"👁️ <b>PREVIEW: {title}</b>\n━━━━━━━━━━━━━━━━━━━━\n<code>{censored}</code>",
                call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML"
            )
    except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_opt_"))
def buy_option_bridge(call: CallbackQuery):
    # Bridges the /getscript button to the existing buying command
    sid = call.data.split("_")[2]
    call.message.text = f"/confirmbuy {sid}"
    confirm_buy_command(call.message) 

@bot.callback_query_handler(func=lambda call: call.data == "del_msg")
def delete_msg_callback(call: CallbackQuery):
    bot.delete_message(call.message.chat.id, call.message.message_id)

# ==========================================
# 1. CREATE SCRIPT & ACTIONS
# ==========================================
@bot.message_handler(commands=['setscript'])
def set_script(message: Message):
    if not check_subscription(message.chat.id):
        return bot.reply_to(message, "💎 <b>PREMIUM FEATURE</b>\nBuy a plan.", parse_mode="HTML")

    try:
        args = message.text.split(maxsplit=3)
        if len(args) < 4: return bot.reply_to(message, "Usage: <code>/setscript [service] [lang] [text]</code>", parse_mode="HTML")
        
        service, lang_code, text = args[1].lower(), args[2].lower(), args[3]
        if lang_code not in LANGUAGES: return bot.reply_to(message, "Invalid Language.")
        twilio_lang = LANGUAGES[lang_code]
        
        if save_user_script(message.chat.id, service, twilio_lang, text):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("💰 ＳＥＬＬ  ＳＣＲＩＰＴ", callback_data=f"act_sell_{service}"))
            markup.row(InlineKeyboardButton("🌍 ＰＵＢＬＩＣ", callback_data=f"act_pub_{service}"), 
                       InlineKeyboardButton("🔒 ＰＲＩＶＡＴＥ", callback_data=f"act_priv"))
            bot.reply_to(message, f"✅ <b>Saved!</b> What next?", reply_markup=markup, parse_mode="HTML")
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
        msg = bot.edit_message_text("💰 Enter Price (USD):", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(msg, process_price_step, service)

def process_price_step(message, service):
    try:
        price = float(message.text)
        if price < 1.00: return bot.reply_to(message, "⚠️ Min $1.00")
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 CREDITS", callback_data=f"paypref_cred_{price}_{service}"))
        markup.add(InlineKeyboardButton("💸 CRYPTO", callback_data=f"paypref_cryp_{price}_{service}"))
        bot.reply_to(message, "👇 <b>Select Payout Method:</b>", reply_markup=markup, parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("paypref_"))
def handle_payment_preference(call: CallbackQuery):
    parts = call.data.split("_")
    method, price, service = parts[1], float(parts[2]), parts[3]
    
    if method == "cred":
        publish_to_market(call.message, call.from_user.id, service, price, "credits")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif method == "cryp":
        msg = bot.edit_message_text("💸 Enter Wallet Address:", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(msg, process_wallet_step, service, price)

def process_wallet_step(message, service, price):
    publish_to_market(message, message.from_user.id, service, price, "crypto", message.text)

def publish_to_market(message, user_id, service, price, payout_pref, payout_wallet=None):
    data = get_user_script(user_id, service)
    if not data: return
    script_text, lang = data
    is_prem = price > 0
    try: author = message.from_user.first_name
    except: author = "User"
    title = f"{author}'s {service.capitalize()}"
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO otp_market (title, service_name, script_text, price, is_premium, author_id, language, payout_pref, payout_wallet) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                (title, service, script_text, price, is_prem, user_id, lang, payout_pref, payout_wallet))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ <b>Published!</b>\nItem: {title}\nPrice: ${price}", parse_mode="HTML")

# ==========================================
# 4. BUYING LOGIC
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
    
    if author_id == message.from_user.id: return bot.reply_to(message, "❌ Own script.")
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"💳 Pay Credits (${price})", callback_data=f"buy_cred_{script_id}"))
    markup.add(InlineKeyboardButton(f"💸 Pay Crypto", callback_data=f"buy_cryp_{script_id}"))
    
    bot.reply_to(message, f"🛒 <b>Checkout:</b> {title} (${price})", reply_markup=markup, parse_mode="HTML")

# ==========================================
# OTHER COMMANDS
# ==========================================
@bot.message_handler(commands=['myscripts'])
def list_scripts(message):
    scripts = get_all_user_scripts(message.chat.id)
    if not scripts: return bot.reply_to(message, "📭 Empty.")
    msg = "📂 <b>SCRIPTS</b>\n"
    for s in scripts: msg += f"🔹 <code>{s[0]}</code>\n"
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(commands=['delscript'])
def delete_script_cmd(message):
    try: service = message.text.split()[1]
    except: return
    if delete_user_script(message.chat.id, service): bot.reply_to(message, "🗑️ Deleted.")

@bot.message_handler(commands=['buyscript', 'shop'])
def shop_menu(message):
    bot.reply_to(message, "💎 Use the <b>Dashboard</b> to access the shop.", parse_mode="HTML")

@bot.message_handler(commands=['freescripts'])
def free_scripts(message):
    bot.reply_to(message, "📚 Use the <b>Dashboard</b> to access library.", parse_mode="HTML")