from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from twilio.rest import Client
from config import bot, ADMIN_IDS, TWILIO_SID, TWILIO_TOKEN
from database import add_balance, get_user_balance, manage_plan, get_all_plans, get_all_users_ids, set_setting, get_setting
import time

# ==========================================
# 📡 TWILIO CHECKER
# ==========================================
def check_twilio_status():
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        account = client.api.accounts(TWILIO_SID).fetch()
        balance = f"{account.balance} {account.currency}"
        status = account.status
        numbers = client.incoming_phone_numbers.list(limit=5)
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
    msg = bot.reply_to(message, "⏳ <b>Connecting...</b>", parse_mode="HTML")
    success, bal, stat, nums = check_twilio_status()
    if success:
        text = f"📡 <b>TWILIO</b>\n💰 <b>Bal:</b> {bal}\n📊 <b>Status:</b> {stat}\n{nums}"
        bot.edit_message_text(text, message.chat.id, msg.message_id, parse_mode="HTML")
    else:
        bot.edit_message_text(f"❌ Error: {bal}", message.chat.id, msg.message_id)

# ==========================================
# 📢 BROADCAST SYSTEM
# ==========================================
def broadcast_to_all(text, type_prefix="📢"):
    ids = get_all_users_ids()
    count = 0
    blocked = 0
    final_msg = f"{type_prefix}\n━━━━━━━━━━━━━━━━━━━━\n{text}"
    
    for uid in ids:
        try:
            bot.send_message(uid, final_msg, parse_mode="HTML")
            count += 1
            time.sleep(0.05) # Rate limit protection
        except:
            blocked += 1
    return count, blocked

# ==========================================
# 📝 CHANGELOG & SETTINGS
# ==========================================
@bot.message_handler(commands=['changelog'])
def show_changelog_public(message: Message):
    text = get_setting("changelog_text")
    if not text: text = "No changelogs yet."
    bot.reply_to(message, f"📝 <b>CHANGELOG</b>\n━━━━━━━━━━━━━━━━━━━━\n{text}", parse_mode="HTML")

# Helper for Wizard input
def process_admin_input(message, action_type):
    if action_type == "changelog":
        if set_setting("changelog_text", message.text):
            bot.reply_to(message, "✅ Changelog updated!")
            
    elif action_type == "maint_msg":
        if set_setting("maintenance_msg", message.text):
            set_setting("maintenance_mode", "ON")
            bot.reply_to(message, "✅ <b>Maintenance ON</b>\nMessage saved.", parse_mode="HTML")
            
    elif action_type.startswith("cast_"):
        b_type = action_type.split("_")[1]
        prefix = "📢 <b>ANNOUNCEMENT</b>"
        if b_type == "update": prefix = "🔄 <b>NEW UPDATE</b>"
        elif b_type == "maint": prefix = "⚠️ <b>MAINTENANCE NOTICE</b>"
        
        msg = bot.reply_to(message, "⏳ Sending broadcast...")
        sent, blk = broadcast_to_all(message.text, prefix)
        bot.edit_message_text(f"✅ <b>Broadcast Sent</b>\nReceived: {sent}\nFailed/Blocked: {blk}", message.chat.id, msg.message_id, parse_mode="HTML")

def toggle_maintenance_mode(chat_id):
    current = get_setting("maintenance_mode")
    new_status = "OFF" if current == "ON" else "ON"
    set_setting("maintenance_mode", new_status)
    return new_status

# ==========================================
# 💰 ADD BALANCE
# ==========================================
@bot.message_handler(commands=['addbalance'])
def admin_add_balance(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        args = message.text.split()
        if len(args) < 3: return
        target_id = int(args[1])
        amount = float(args[2])
        if add_balance(target_id, amount):
            new_bal = get_user_balance(target_id)
            bot.reply_to(message, f"✅ Added ${amount} to {target_id}")
    except: pass