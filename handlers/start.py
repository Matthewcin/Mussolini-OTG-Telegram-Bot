from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import register_user

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    
    # Register user in DB
    register_user(user)

    # Welcome Text
    text = f"""
BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏 (EXAMPLE TEXT)

 Hello, {user.first_name}! Welcome to the BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏. This bot is used to subsrice to our spoofcall bot and recieve notifications.

BIGFATOTP - 𝙊𝙏𝙋 𝘽𝙊𝙏 have UNIQUE features that you can't find in any other bot.

 Our bot is an Hybrid between OTP Bot and 3CX. its a professional Social Engineering kit for professional OTP users.

 MODES: Banks, NFCs, Payment Services, Payment Gateways, Brokerages, Stores, Carriers, Emails, Crypto Exchanges, Crypto Hardwares, Social Medias, Cloud Services

 Features included:
 24/7 Support
 Automated Payment System
 Live Panel Feeling
 12+ Pre-made Modes
 Customizable Caller ID / Spoofing
 99.99% Up-time
 Customizable Scripts
 Customizable Panel Actions
 International Support
 Multilingual Support (60+ Voices)
 PGP / Conference Calls
 Live DTMF
 Call Streaming - Listen to call in Real-Time!

⤷ Capture Any OTP.
⤷ Capture Banks OTP.
⤷ Capture Crypto OTP 
⤷ Capture Any Pin Code.
⤷ Capture Any CVV Code
⤷ Get SSN From Victim.
⤷ Capture Voice OTP.
⤷ Get Victim To Approve Message.
⤷ Capture Any Carrier Pin.

 DAILY [$50] / WEEKLY [$150] / MONTHLY [$285]
    """

    # Buttons Layout
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎟️ Enter Key", callback_data="enter_key"),
        InlineKeyboardButton("📊 Bot Status", callback_data="bot_status"),
        InlineKeyboardButton("🪙 ₿uy Plan", callback_data="buy_subs"),
        InlineKeyboardButton("🤖 Commands", callback_data="commands"),
        InlineKeyboardButton("🛠️ Features", callback_data="features"),
        InlineKeyboardButton("🫂 Community", callback_data="community"),
        InlineKeyboardButton("👥 Referral", callback_data="referral"),
        InlineKeyboardButton("⛑️ Support", callback_data="support")
    )
    
    # 🔒 ADMIN PANEL: Only visible if the user ID is in the ADMIN_IDS list
    if user.id in ADMIN_IDS:
        markup.add(InlineKeyboardButton("🕴️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", callback_data="admin_panel"))

    bot.send_message(message.chat.id, text, reply_markup=markup)
