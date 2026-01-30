from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from datetime import datetime
from config import bot, ADMIN_IDS
from database import get_connection, check_subscription, get_user_balance, get_referral_count

# ==========================================
# 👤 PROFILE GENERATOR
# ==========================================
def get_profile_content(user_id, first_name):
    """
    Genera el texto y los botones del perfil de usuario.
    Retorna: (text, markup)
    """
    conn = get_connection()
    if not conn:
        return "⚠️ Database Error", None

    cur = conn.cursor()
    
    # 1. Obtener datos básicos
    cur.execute("SELECT joined_at, subscription_end FROM otp_users WHERE user_id = %s", (user_id,))
    user_data = cur.fetchone()
    
    # 2. Obtener estadísticas de compras (Scripts)
    cur.execute("SELECT COUNT(*) FROM otp_purchases WHERE user_id = %s", (user_id,))
    scripts_owned = cur.fetchone()[0]
    
    # 3. Obtener Balance
    balance = get_user_balance(user_id)
    
    # 4. Obtener Referidos
    refs = get_referral_count(user_id)
    
    conn.close()

    if not user_data:
        return "⚠️ Profile not found. Type /start to register.", None

    joined_at, sub_end = user_data

    # --- LÓGICA DE ESTADO ---
    if user_id in ADMIN_IDS:
        status_badge = "🕴️ ＡＤＭＩＮ"
        sub_status = "∞ Infinite Access"
    elif check_subscription(user_id):
        status_badge = "💎 ＰＲＥＭＩＵＭ"
        days_left = (sub_end - datetime.now()).days if sub_end else 0
        sub_status = f"Active ({days_left} days left)"
    else:
        status_badge = "👤 ＦＲＥＥ  ＵＳＥＲ"
        sub_status = "Inactive"

    # --- DISEÑO DEL TEXTO (HTML) ---
    text = (
        f"👤 <b>ＵＳＥＲ  ＰＲＯＦＩＬＥ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"🏷 <b>Role:</b> {status_badge}\n"
        f"📅 <b>Joined:</b> {joined_at.strftime('%Y-%m-%d')}\n\n"
        
        f"👛 <b>ＷＡＬＬＥＴ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 <b>Balance:</b> <code>${balance:.2f}</code>\n"
        f"📦 <b>Scripts:</b> <code>{scripts_owned} Owned</code>\n\n"
        
        f"🔑 <b>ＳＵＢＳＣＲＩＰＴＩＯＮ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>Status:</b> {sub_status}\n"
        f"👥 <b>Referrals:</b> <code>{refs} Users</code>"
    )

    # --- BOTONES ---
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🪙 Top Up Balance", callback_data="buy_subs"),
               InlineKeyboardButton("🎟️ Redeem Key", callback_data="enter_key"))
    
    markup.row(InlineKeyboardButton("📂 My Scripts", callback_data="show_myscripts"),
               InlineKeyboardButton("👥 Invite Friends", callback_data="referral"))
    
    markup.add(InlineKeyboardButton("⬅ Back to Menu", callback_data="back_home"))

    return text, markup

# ==========================================
# 👥 REFERRAL SYSTEM
# ==========================================
def show_referral(message):
    """
    Muestra el enlace de referido y las estadísticas.
    """
    user_id = message.from_user.id
    bot_name = bot.get_me().username
    ref_link = f"https://t.me/{bot_name}?start={user_id}"
    
    refs = get_referral_count(user_id)
    # Ejemplo: Ganas $2.00 de crédito por referido (puedes ajustar esto)
    earnings = refs * 2.00 
    
    text = (
        f"👥 <b>ＲＥＦＥＲＲＡＬ  ＳＹＳＴＥＭ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Invite your friends and earn credits!\n\n"
        
        f"🔗 <b>Your Link:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        
        f"📊 <b>Stats:</b>\n"
        f"• Total Invites: <code>{refs}</code>\n"
        f"• Total Earned: <code>${earnings:.2f}</code>\n\n"
        
        f"<i>(Credits are automatically added when they join)</i>"
    )
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⬅ Back", callback_data="show_profile"))
    
    # Si es llamada de callback, editamos. Si es comando, enviamos.
    try:
        bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup, parse_mode="HTML")
    except:
        bot.reply_to(message, text, reply_markup=markup, parse_mode="HTML")

# ==========================================
# 🕹️ COMANDO /PROFILE
# ==========================================
@bot.message_handler(commands=['profile', 'me'])
def profile_command(message: Message):
    text, markup = get_profile_content(message.from_user.id, message.from_user.first_name)
    if text:
        bot.reply_to(message, text, reply_markup=markup, parse_mode="HTML")