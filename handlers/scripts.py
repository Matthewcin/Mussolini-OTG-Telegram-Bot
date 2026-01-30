from telebot.types import Message
from config import bot, ADMIN_IDS
from database import (
    save_user_script, get_all_user_scripts, delete_user_script, 
    check_subscription, get_connection, deduct_balance, get_user_balance
)

# ==========================================
# 🌍 CONFIGURACIÓN DE IDIOMAS (TU CÓDIGO)
# ==========================================
# Supported Languages (Neural TTS)
LANGUAGES = {
    "en": "en-US",      # English (US)
    "es": "es-MX",      # Spanish (Mexico)
    "es-es": "es-ES",   # Spanish (Spain)
    "pt": "pt-BR",      # Portuguese (Brazil)
    "fr": "fr-FR",      # French
    "de": "de-DE",      # German
    "it": "it-IT"       # Italian
}

TEMPLATE_MSG = """
📝 **SCRIPT MAKER TEMPLATE**

Create custom scripts with Neural Voices.

**Command:**
`/setscript [service] [lang] [text]`

**Available Languages:**
🇺🇸 `en` (English US)
🇲🇽 `es` (Spanish Latin)
🇪🇸 `es-es` (Spanish Spain)
🇧🇷 `pt` (Portuguese)
🇫🇷 `fr` (French)
🇮🇹 `it` (Italian)

💡 **Example 1 (English):**
`/setscript Amazon en Hello, this is Amazon Security. We blocked a suspicious attempt. Enter the code sent to your mobile.`

💡 **Example 2 (Spanish):**
`/setscript PayPal es Hola, hablamos de PayPal. Ingrese su código de seguridad.`
"""

# ==========================================
# 1. 📂 GESTIÓN DE SCRIPTS PROPIOS
# ==========================================

@bot.message_handler(commands=['template', 'help_scripts'])
def show_template(message):
    bot.reply_to(message, TEMPLATE_MSG, parse_mode="Markdown")

@bot.message_handler(commands=['setscript'])
def set_script(message: Message):
    # 1. Verify Subscription
    if not check_subscription(message.chat.id):
        return bot.reply_to(message, "💎 **Premium Feature:** You need an active plan to create custom scripts.\nUse `/start` -> `Buy Plan`.")

    try:
        # args[0]=/setscript, args[1]=service, args[2]=lang, args[3:]=text
        args = message.text.split(maxsplit=3)
        
        if len(args) < 4:
            return bot.reply_to(message, "❌ **Error:** Missing arguments.\n\nUse `/template` to see examples.")
        
        service = args[1]
        lang_code = args[2].lower()
        text = args[3]
        
        # Validate Language
        if lang_code not in LANGUAGES:
            supported = ", ".join(LANGUAGES.keys())
            return bot.reply_to(message, f"⚠️ **Invalid Language.**\nSupported: `{supported}`", parse_mode="Markdown")
        
        twilio_lang = LANGUAGES[lang_code]
        
        # Guardar usando tu función de database.py
        if save_user_script(message.chat.id, service, twilio_lang, text):
            bot.reply_to(message, f"✅ **Script Saved Successfully!**\n\n🎯 Service: `{service}`\n🗣️ Voice: `{twilio_lang}`\n📜 Text: _{text}_", parse_mode="Markdown")
        else:
            bot.reply_to(message, "🔴 **Database Error:** Could not save script.")
            
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

@bot.message_handler(commands=['myscripts'])
def list_scripts(message):
    # 1. Verify Subscription
    if not check_subscription(message.chat.id):
        return bot.reply_to(message, "💎 **Premium Feature:** You need an active plan.")

    scripts = get_all_user_scripts(message.chat.id)
    if not scripts:
        return bot.reply_to(message, "📭 **No custom scripts found.**\nUse `/template` to create one or visit `/freescripts`.")
    
    msg = "📂 **MY CUSTOM SCRIPTS**\n\n"
    for s in scripts:
        # s[0] is service_name, s[1] is language
        msg += f"🔹 `{s[0]}` ({s[1]})\n"
    
    msg += "\nTo delete: `/delscript [service]`"
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['delscript'])
def delete_script(message):
    args = message.text.split()
    if len(args) < 2: return bot.reply_to(message, "Usage: `/delscript [service]`")
    
    service = args[1]
    if delete_user_script(message.chat.id, service):
        bot.reply_to(message, f"🗑️ Script for `{service}` deleted. Default script will be used.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Script not found.")

# ==========================================
# 2. 🆓 FREE SCRIPTS (LIBRERÍA PÚBLICA)
# ==========================================
@bot.message_handler(commands=['freescripts'])
def free_scripts(message: Message):
    conn = get_connection()
    cur = conn.cursor()
    # Buscamos scripts que valgan 0.00 o no sean premium
    cur.execute("SELECT id, title, service_name, language FROM otp_market WHERE price = 0 OR is_premium = FALSE")
    scripts = cur.fetchall()
    conn.close()

    if not scripts:
        bot.reply_to(message, "📚 **Library Empty.** No free scripts available yet.")
        return

    text = "📚 **FREE SCRIPTS LIBRARY**\nUse `/getscript [ID]` to install one.\n\n"
    for s in scripts:
        # ID | Title | Service | Lang
        text += f"🆔 `{s[0]}` | **{s[1]}** ({s[2]}) [{s[3]}]\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

# ==========================================
# 3. 🛒 BUY SCRIPTS (TIENDA PREMIUM)
# ==========================================
@bot.message_handler(commands=['buyscript', 'shop'])
def buy_script_menu(message: Message):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, price, language FROM otp_market WHERE is_premium = TRUE")
    items = cur.fetchall()
    conn.close()
    
    if not items:
        bot.reply_to(message, "🛒 **Shop Empty.** No premium scripts for sale right now.")
        return

    text = "🛒 **PREMIUM SCRIPT SHOP**\nHigh converting scripts verified by admins.\n\n"
    for item in items:
        text += f"💎 **{item[1]}**\n🆔 ID: `{item[0]}`\n💰 Price: `${item[2]}`\n🗣 Lang: {item[3]}\n➖➖➖➖➖➖\n"
    
    text += "\nTo buy, verify your balance and type:\n`/confirmbuy [ID]`"
    bot.reply_to(message, text, parse_mode="Markdown")

# ==========================================
# 4. 👁️ PREVIEW SCRIPT (SOLO ADMIN)
# ==========================================
@bot.message_handler(commands=['previewscript'])
def preview_script(message: Message):
    # 🔒 SEGURIDAD: Solo Admin puede ver el script completo antes de comprar
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "⛔ **Access Denied:** Only Admins can preview full scripts.")
        return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: `/previewscript [ID]`")
            return
        
        script_id = int(args[1])
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT title, script_text, price, is_premium, service_name FROM otp_market WHERE id = %s", (script_id,))
        data = cur.fetchone()
        conn.close()
        
        if not data:
            bot.reply_to(message, "❌ Script ID not found.")
            return
            
        title, text, price, is_prem, service = data
        
        type_lbl = "💎 PREMIUM" if is_prem else "🆓 FREE"
            
        msg = f"👁️ **ADMIN PREVIEW**\n━━━━━━━━━━━━\n🏷 **Title:** {title}\n🏢 **Service:** {service}\n💰 **Price:** ${price}\n📜 **Type:** {type_lbl}\n\n📝 **Full Text:**\n`{text}`"
        bot.reply_to(message, msg, parse_mode="Markdown")
        
    except ValueError:
        bot.reply_to(message, "❌ ID must be a number.")

# ==========================================
# 5. 💰 CONFIRM BUY (COMPRA)
# ==========================================
@bot.message_handler(commands=['confirmbuy'])
def confirm_buy(message: Message):
    user_id = message.from_user.id
    try:
        script_id = int(message.text.split()[1])
    except:
        bot.reply_to(message, "⚠️ Usage: `/confirmbuy [ID]`")
        return

    conn = get_connection()
    cur = conn.cursor()
    
    # 1. Obtener datos del script
    cur.execute("SELECT price, service_name, language, script_text, title FROM otp_market WHERE id = %s", (script_id,))
    item = cur.fetchone()
    
    if not item:
        bot.reply_to(message, "❌ Script not found.")
        return
        
    price, service, lang, text, title = item
    
    # 2. Verificar si ya lo compró
    cur.execute("SELECT * FROM otp_purchases WHERE user_id = %s AND script_id = %s", (user_id, script_id))
    if cur.fetchone():
        bot.reply_to(message, "✅ You already own this script! Use `/myscripts`.")
        return

    # 3. Intentar Cobrar
    if deduct_balance(user_id, float(price)):
        # 4. Guardar Compra
        cur.execute("INSERT INTO otp_purchases (user_id, script_id) VALUES (%s, %s)", (user_id, script_id))
        
        # 5. Instalar en la cuenta del usuario (usando tu función save_user_script o SQL directo)
        save_user_script(user_id, service, lang, text)
        
        conn.commit()
        bot.reply_to(message, f"✅ **Purchase Successful!**\n\nScript **{title}** has been installed to your account for `{service}`.\n\nType `/call [number] {service}` to use it.", parse_mode="Markdown")
    else:
        bal = get_user_balance(user_id)
        bot.reply_to(message, f"💸 **Insufficient Funds.**\nCost: `${price}`\nYour Balance: `${bal}`")
    
    conn.close()

# ==========================================
# 6. 🛠️ GET SCRIPT (INSTALAR GRATIS)
# ==========================================
@bot.message_handler(commands=['getscript'])
def get_free_script(message: Message):
    user_id = message.from_user.id
    try: script_id = int(message.text.split()[1])
    except: return bot.reply_to(message, "Usage: `/getscript [ID]`")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT service_name, language, script_text, is_premium, title FROM otp_market WHERE id = %s", (script_id,))
    data = cur.fetchone()
    
    if not data: return bot.reply_to(message, "❌ Not found.")
    
    # data = (service, lang, text, is_prem, title)
    if data[3]: # Si es premium
        bot.reply_to(message, "💎 This is a premium script. Use `/confirmbuy`.")
        conn.close()
        return

    # Instalar
    save_user_script(user_id, data[0], data[1], data[2])
    
    conn.commit()
    conn.close()
    
    bot.reply_to(message, f"✅ Script **{data[4]}** installed for `{data[0]}`!", parse_mode="Markdown")

# ==========================================
# 7. 👮‍♂️ ADMIN: GESTIONAR MERCADO
# ==========================================
@bot.message_handler(commands=['addmarket'])
def admin_add_market(message: Message):
    if message.from_user.id not in ADMIN_IDS: return

    # Formato: /addmarket [PRECIO] [SERVICE] [LANG] [TITLE] | [TEXTO]
    # Ejemplo: /addmarket 5.00 Amazon en-US Amazon V1 | Hello...
    try:
        args = message.text.split(maxsplit=4)
        if len(args) < 5: raise ValueError

        price = float(args[1])
        service = args[2] # Ej: Amazon
        lang = args[3]    # Ej: en-US
        
        # El resto es "Título | Texto"
        rest = args[4].split("|")
        if len(rest) < 2: raise ValueError
        
        title = rest[0].strip()
        text = rest[1].strip()
        
        is_prem = True if price > 0 else False
        
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO otp_market (title, service_name, script_text, price, is_premium, author_id, language)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (title, service.lower(), text, price, is_prem, message.from_user.id, lang))
        conn.commit()
        conn.close()
        
        type_lbl = "💎 PREMIUM" if is_prem else "🆓 FREE"
        bot.reply_to(message, f"✅ **Market Item Added!**\n\n📌 Title: {title}\n💰 Price: ${price}\n🏢 Service: {service}\n🗣 Lang: {lang}\n🏷 Type: {type_lbl}", parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ **Usage Error.**\n\nFormat:\n`/addmarket [PRICE] [SERVICE] [LANG] [TITLE] | [SCRIPT_TEXT]`\n\nExample:\n`/addmarket 5.00 Amazon en-US Amazon V2 | Hello this is Amazon security...`\n\n_(Use | to separate title and text)_", parse_mode="Markdown")

@bot.message_handler(commands=['scriptlist'])
def admin_script_list(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, price, is_premium, service_name FROM otp_market ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()
    
    if not rows:
        bot.reply_to(message, "📭 Market is empty.")
        return

    text = "📋 **MARKET INVENTORY:**\n\n"
    for r in rows:
        type_s = "💎" if r[3] else "🆓"
        text += f"ID `{r[0]}` | {type_s} **{r[1]}** (${r[2]}) - {r[4]}\n"
        
    bot.reply_to(message, text, parse_mode="Markdown")