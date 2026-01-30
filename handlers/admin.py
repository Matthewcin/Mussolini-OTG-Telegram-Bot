from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from twilio.rest import Client
from config import bot, ADMIN_IDS, TWILIO_SID, TWILIO_TOKEN
from database import add_balance, get_user_balance, manage_plan, get_all_plans

# ==========================================
# 📡 TWILIO CHECKER (BALANCE & NUMBERS)
# ==========================================
def check_twilio_status():
    """Conecta con Twilio y obtiene saldo y números."""
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        
        # 1. Obtener Cuenta (Saldo)
        account = client.api.accounts(TWILIO_SID).fetch()
        balance = f"{account.balance} {account.currency}"
        status = account.status
        
        # 2. Obtener Números (Limitado a 5 para no saturar)
        numbers = client.incoming_phone_numbers.list(limit=10)
        if numbers:
            num_list = "\n".join([f"📞 <code>{n.phone_number}</code> ({n.friendly_name})" for n in numbers])
        else:
            num_list = "⚠️ No active numbers."
            
        return True, balance, status, num_list
    except Exception as e:
        return False, str(e), None, None

@bot.message_handler(commands=['twilio'])
def cmd_check_twilio(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    
    msg = bot.reply_to(message, "⏳ <b>Connecting to Twilio...</b>", parse_mode="HTML")
    
    success, bal, stat, nums = check_twilio_status()
    
    if success:
        text = (
            f"📡 <b>TWILIO STATUS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Balance:</b> <code>{bal}</code>\n"
            f"📊 <b>Status:</b> {stat.upper()}\n\n"
            f"🔢 <b>Active Numbers:</b>\n{nums}"
        )
        bot.edit_message_text(text, message.chat.id, msg.message_id, parse_mode="HTML")
    else:
        bot.edit_message_text(f"❌ <b>Twilio Error:</b>\n{bal}", message.chat.id, msg.message_id, parse_mode="HTML")

# ==========================================
# 💰 ADD BALANCE (MANUAL COMMAND)
# ==========================================
@bot.message_handler(commands=['addbalance'])
def admin_add_balance(message: Message):
    if message.from_user.id not in ADMIN_IDS: return

    try:
        args = message.text.split()
        if len(args) < 3:
            return bot.reply_to(message, "⚠️ Usage: `/addbalance [ID] [Amount]`", parse_mode="Markdown")
        
        target_id = int(args[1])
        amount = float(args[2])

        if add_balance(target_id, amount):
            new_bal = get_user_balance(target_id)
            bot.reply_to(message, f"✅ <b>Added ${amount}</b> to <code>{target_id}</code>\nNew Balance: ${new_bal}", parse_mode="HTML")
            try: bot.send_message(target_id, f"💰 <b>Deposit Received!</b>\nAdmin added <b>${amount}</b>.\nCurrent Balance: <b>${new_bal}</b>", parse_mode="HTML")
            except: pass
        else:
            bot.reply_to(message, "❌ Database Error.")
    except ValueError:
        bot.reply_to(message, "❌ Invalid format.")

# ==========================================
# 🛠️ PLAN MANAGEMENT (COMMANDS)
# ==========================================
@bot.message_handler(commands=['listplans'])
def admin_list_plans(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    plans = get_all_plans()
    if not plans: return bot.reply_to(message, "📭 No plans.")
    text = "📋 <b>PLANS</b>\n" + "\n".join([f"• ${p[1]} -> ${p[2]}" for p in plans])
    bot.reply_to(message, text, parse_mode="HTML")