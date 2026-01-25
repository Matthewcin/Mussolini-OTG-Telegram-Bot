from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import get_user_info, get_referral_count
from datetime import datetime

@bot.message_handler(commands=['profile', 'me'])
def show_profile(message):
    user = message.from_user
    user_id = user.id
    
    # Obtener datos de DB
    info = get_user_info(user_id)
    # info structure: (subscription_end, joined_at, referred_by)
    
    if not info:
        return bot.reply_to(message, "⚠️ Profile not found. Type /start to register.")
    
    sub_end = info[0]
    joined_at = info[1]
    
    # Calcular estado de suscripción
    is_admin = user_id in ADMIN_IDS
    now = datetime.now()
    
    if is_admin:
        plan_status = "🛡️ **OWNER / ADMIN**"
        days_left = "Infinity"
    elif sub_end and sub_end > now:
        plan_status = "💎 **PREMIUM PLAN**"
        delta = sub_end - now
        days_left = f"{delta.days} Days, {delta.seconds//3600} Hours"
        expiry_date = sub_end.strftime("%Y-%m-%d %H:%M")
    else:
        plan_status = "🆓 **FREE / EXPIRED**"
        days_left = "0"
        expiry_date = "N/A"

    # Formatear fecha de registro
    joined_date = joined_at.strftime("%Y-%m-%d") if joined_at else "Unknown"

    text = f"""
👤 **USER PROFILE**
━━━━━━━━━━━━━━━━
🆔 **ID:** `{user_id}`
👤 **Name:** {user.first_name}
📅 **Joined:** {joined_date}

💳 **SUBSCRIPTION**
━━━━━━━━━━━━━━━━
📊 **Status:** {plan_status}
⏳ **Time Left:** {days_left}
🗓 **Expires:** `{expiry_date}`
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🪙 Buy Plan", callback_data="buy_subs"))
    markup.add(InlineKeyboardButton("👥 My Referrals", callback_data="referral"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['referral', 'invite'])
def show_referral(message):
    user_id = message.from_user.id
    bot_name = bot.get_me().username
    
    # Enlace de invitación único
    ref_link = f"https://t.me/{bot_name}?start={user_id}"
    
    # Contar referidos
    count = get_referral_count(user_id)
    
    text = f"""
👥 **REFERRAL SYSTEM**

Invite your friends and earn rewards! (Soon)

🔗 **Your Link:**
`{ref_link}`

📊 **Stats:**
👤 Users Invited: **{count}**

_Share this link. When users join, your counter will go up._
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
