from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import get_user_info, get_referral_count
from datetime import datetime

@bot.message_handler(commands=['profile', 'me'])
def show_profile(message):
    user = message.from_user
    user_id = user.id
    
    info = get_user_info(user_id)
    if not info:
        return bot.reply_to(message, "⚠️ Profile not found. Type /start.")
    
    sub_end = info[0]
    joined_at = info[1]
    
    is_admin = user_id in ADMIN_IDS
    now = datetime.now()
    
    if is_admin:
        plan_status = "🛡️ **ADMIN**"
        days_left = "∞"
        expiry_date = "Never"
    elif sub_end and sub_end > now:
        plan_status = "💎 **PREMIUM**"
        delta = sub_end - now
        days_left = f"{delta.days}d {delta.seconds//3600}h"
        expiry_date = sub_end.strftime("%Y-%m-%d")
    else:
        plan_status = "🆓 **FREE**"
        days_left = "0"
        expiry_date = "Expired"

    joined_date = joined_at.strftime("%Y-%m-%d") if joined_at else "?"

    text = f"""
👤 **USER PROFILE**
━━━━━━━━━━━━━━━━
🆔 `{user_id}`
👤 {user.first_name}
📅 Joined: {joined_date}

💳 **SUBSCRIPTION**
━━━━━━━━━━━━━━━━
📊 Status: {plan_status}
⏳ Left: {days_left}
🗓 Exp: `{expiry_date}`
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🪙 Extend Plan", callback_data="buy_subs"))
    markup.add(InlineKeyboardButton("👥 Referrals", callback_data="referral"))
    # 🔙 BOTÓN BACK
    markup.add(InlineKeyboardButton("⬅ Back to Menu", callback_data="back_home"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['referral', 'invite'])
def show_referral(message):
    user_id = message.from_user.id
    bot_name = bot.get_me().username
    ref_link = f"https://t.me/{bot_name}?start={user_id}"
    count = get_referral_count(user_id)
    
    text = f"""
👥 **REFERRAL PROGRAM**

Invite friends to earn rewards (Coming Soon).

🔗 **Your Link:**
`{ref_link}`

📊 **Your Stats:**
Invited: **{count}** Users
    """
    
    markup = InlineKeyboardMarkup()
    # 🔙 BOTÓN BACK
    markup.add(InlineKeyboardButton("⬅ Back to Menu", callback_data="back_home"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
