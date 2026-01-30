from telebot.types import Message
from config import bot, ADMIN_IDS
from database import add_balance, get_user_balance, manage_plan, get_all_plans

# ==========================================
# 💰 ADD BALANCE (MANUAL)
# ==========================================
@bot.message_handler(commands=['addbalance'])
def admin_add_balance(message: Message):
    if message.from_user.id not in ADMIN_IDS: return

    try:
        args = message.text.split()
        if len(args) == 2:
            target_id = message.from_user.id
            amount = float(args[1])
        elif len(args) == 3:
            target_id = int(args[1])
            amount = float(args[2])
        else:
            bot.reply_to(message, "⚠️ Usage: `/addbalance [ID] [Amount]`", parse_mode="Markdown")
            return

        if add_balance(target_id, amount):
            new_bal = get_user_balance(target_id)
            bot.reply_to(message, f"✅ **Balance Added!**\nUser: `{target_id}`\nNew Balance: `${new_bal}`", parse_mode="Markdown")
            if target_id != message.from_user.id:
                try: bot.send_message(target_id, f"💰 **Deposit Received!**\nAdmin added **${amount}**.\nCurrent Balance: **${new_bal}**", parse_mode="Markdown")
                except: pass
        else:
            bot.reply_to(message, "❌ Database Error.")
    except ValueError:
        bot.reply_to(message, "❌ Invalid numbers.")

# ==========================================
# 🛠️ PLAN MANAGEMENT COMMANDS
# ==========================================

@bot.message_handler(commands=['addplan', 'editplan'])
def admin_add_plan(message: Message):
    # Uso: /addplan 12 5 (Precio 12, da 5 de saldo)
    if message.from_user.id not in ADMIN_IDS: return

    try:
        args = message.text.split()
        if len(args) < 3:
            return bot.reply_to(message, "⚠️ **Usage:**\n`/addplan [Price] [Reward]`\nExample: `/addplan 12 5`", parse_mode="Markdown")
        
        price = float(args[1])
        reward = float(args[2])
        
        if manage_plan("add", price, reward):
            bot.reply_to(message, f"✅ **Plan Saved!**\n\nCost: **${price}**\nReward: **${reward}** Balance", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Error saving plan.")
            
    except ValueError:
        bot.reply_to(message, "❌ Values must be numbers.")

@bot.message_handler(commands=['delplan'])
def admin_del_plan(message: Message):
    # Uso: /delplan 12
    if message.from_user.id not in ADMIN_IDS: return

    try:
        args = message.text.split()
        if len(args) < 2:
            return bot.reply_to(message, "⚠️ **Usage:** `/delplan [Price]`", parse_mode="Markdown")
        
        price = float(args[1])
        
        if manage_plan("del", price):
            bot.reply_to(message, f"🗑️ **Plan deleted:** ${price}", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Plan not found or DB error.")
            
    except ValueError:
        bot.reply_to(message, "❌ Price must be a number.")

@bot.message_handler(commands=['listplans'])
def admin_list_plans(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    
    plans = get_all_plans()
    if not plans:
        return bot.reply_to(message, "📭 No plans configured.")
        
    text = "📋 **CURRENT PLANS**\n━━━━━━━━━━━━━━━━\n"
    for p in plans:
        # p = (id, price, reward)
        text += f"🔹 **Cost:** ${p[1]} ➡️ **Get:** ${p[2]}\n"
        
    bot.reply_to(message, text, parse_mode="Markdown")