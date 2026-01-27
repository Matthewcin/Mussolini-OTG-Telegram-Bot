from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import get_user_info, get_referral_count
from datetime import datetime

# ==========================================
# 🧠 LÓGICA PURA (Generador de Texto)
# ==========================================
def get_profile_content(user_id, first_name):
    """
    Genera el texto y los botones del perfil.
    """
    info = get_user_info(user_id)
    
    if not info:
        return None, None
    
    # Ahora info trae: (subscription_end, joined_at, referred_by, wallet_balance)
    sub_end = info[0]
    joined_at = info[1]
    wallet_balance = info[3] # <--- NUEVO
    
    is_admin = user_id in ADMIN_IDS
    now = datetime.now()
    
    if is_admin:
        plan_status = "🛡️ **OWNER / ADMIN**"
        days_left = "∞ (Infinity)"
        expiry_date = "Never"
    elif sub_end and sub_end > now:
        plan_status = "💎 **PREMIUM PLAN**"
        delta = sub_end - now
        days_left = f"{delta.days} Days" if delta.days > 0 else f"{delta.seconds//3600} Hours"
        expiry_date = sub_end.strftime("%Y-%m-%d")
    else:
        plan_status = "🆓 **FREE / EXPIRED**"
        days_left = "0"
        expiry_date = "Expired"

    joined_date = joined_at.strftime("%Y-%m-%d") if joined_at else "Unknown"

    text = f"""
👤 **USER PROFILE**
━━━━━━━━━━━━━━━━
🆔 **ID:** `{user_id}`
👤 **Name:** {first_name}
📅 **Joined:** {joined_date}

💳 **WALLET & SUBSCRIPTION**
━━━━━━━━━━━━━━━━
💰 **Balance:** `${wallet_balance}`
📊 **Status:** {plan_status}
⏳ **Time Left:** {days_left}
🗓 **Expires:** `{expiry_date}`
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🪙 Top Up / Extend", callback_data="buy_subs"))
    markup.add(InlineKeyboardButton("👥 Referral System", callback_data="referral"))
    markup.add(InlineKeyboardButton("⬅ Back to Menu", callback_data="back_home"))
    
    return text, markup

# ==========================================
# 📡 COMANDOS
# ==========================================

@bot.message_handler(commands=['profile', 'me'])
def show_profile_command(message):
    user = message.from_user
    text, markup = get_profile_content(user.id, user.first_name)
    
    if text:
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ Profile not found. Please type /start.")

@bot.message_handler(commands=['referral', 'invite'])
def show_referral(message):
    user_id = message.from_user.id
    bot_name = bot.get_me().username
    
    ref_link = f"https://t.me/{bot_name}?start={user_id}"
    count = get_referral_count(user_id)
    
    text = f"""
👥 **REFERRAL PROGRAM**

Invite friends and earn credits! (Coming Soon)

🔗 **Your Link:**
`{ref_link}`

📊 **Your Stats:**
Users Invited: **{count}**
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⬅ Back to Menu", callback_data="back_home"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
