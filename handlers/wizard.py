from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import bot, ADMIN_IDS
from database import add_balance, get_available_services, manage_plan, create_license

# Wizard State Storage
# {chat_id: {'state': '...', 'data': ...}}
wizard_context = {}

# ==========================================
# 1. USER WIZARDS (CALL & SMS)
# ==========================================
def start_call_wizard(message):
    msg = bot.send_message(message.chat.id, "📞 <b>ＣＡＬＬ  ＷＩＺＡＲＤ</b>\n━━━━━━━━━━━━━━━━━━━━\nEnter <b>Target Number</b>:\n<i>(Format: +123456789)</i>", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_call_number)

def step_call_number(message):
    if message.text.startswith("/"): return 
    wizard_context[message.chat.id] = {'target': message.text, 'page': 0, 'services': get_available_services(message.chat.id)}
    send_service_menu(message.chat.id)

def send_service_menu(chat_id):
    data = wizard_context.get(chat_id)
    if not data: return
    services = data['services']
    page = data['page']
    items_per_page = 6
    start = page * items_per_page
    end = start + items_per_page
    current_batch = services[start:end]
    
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(f"🏢 {svc}", callback_data=f"wiz_sel_{svc}") for svc in current_batch]
    markup.add(*buttons)
    
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Prev", callback_data="wiz_page_prev"))
    if end < len(services): nav.append(InlineKeyboardButton("Next ➡️", callback_data="wiz_page_next"))
    if nav: markup.row(*nav)
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data="back_home"))
    
    bot.send_message(chat_id, "🏢 <b>SELECT SERVICE</b>\nChoose script:", reply_markup=markup, parse_mode="HTML")

def start_sms_wizard(message):
    msg = bot.send_message(message.chat.id, "📩 <b>SMS Wizard:</b> Enter Number:", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_sms_number)

def step_sms_number(message):
    wizard_context[message.chat.id] = {'target': message.text}
    msg = bot.send_message(message.chat.id, "📝 Enter Service Name:", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_sms_service)

def step_sms_service(message):
    data = wizard_context.get(message.chat.id)
    from handlers.sms import handle_sms_command
    message.text = f"/sms {data['target']} {message.text}"
    handle_sms_command(message)

# ==========================================
# 2. ADMIN WIZARDS (INTERACTIVE PANEL)
# ==========================================

# --- A) ADD BALANCE ---
def start_balance_wizard(message):
    msg = bot.send_message(message.chat.id, "💰 <b>Admin:</b> Enter User ID (or 'me'):", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_bal_user)

def step_bal_user(message):
    uid = message.text.lower()
    if uid == 'me': target = message.from_user.id
    else:
        try: target = int(uid)
        except: return bot.send_message(message.chat.id, "❌ Invalid ID.")
    
    wizard_context[message.chat.id] = {'target': target}
    msg = bot.send_message(message.chat.id, "💵 Enter Amount (USD):")
    bot.register_next_step_handler(msg, step_bal_amount)

def step_bal_amount(message):
    try:
        amount = float(message.text)
        data = wizard_context.get(message.chat.id)
        if add_balance(data['target'], amount):
             bot.send_message(message.chat.id, f"✅ Added ${amount} to User `{data['target']}`", parse_mode="Markdown")
        else:
             bot.send_message(message.chat.id, "❌ Database Error.")
    except: bot.send_message(message.chat.id, "❌ Error: Not a number.")

# --- B) GENERATE KEY ---
def start_genkey_wizard(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("1 Day", callback_data="gkey_1"),
               InlineKeyboardButton("3 Days", callback_data="gkey_3"),
               InlineKeyboardButton("7 Days", callback_data="gkey_7"))
    markup.add(InlineKeyboardButton("30 Days", callback_data="gkey_30"),
               InlineKeyboardButton("LIFETIME (999)", callback_data="gkey_999"))
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data="admin_panel"))
    bot.send_message(message.chat.id, "🎟️ <b>GENERATE LICENSE</b>\nSelect duration:", reply_markup=markup, parse_mode="HTML")

# --- C) ADD PLAN ---
def start_addplan_wizard(message):
    msg = bot.send_message(message.chat.id, "➕ <b>ADD PLAN</b>\nEnter Price (USD):", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_plan_price)

def step_plan_price(message):
    try:
        price = float(message.text)
        wizard_context[message.chat.id] = {'price': price}
        msg = bot.send_message(message.chat.id, f"💎 Price: ${price}\nNow enter <b>Reward Balance</b>:", parse_mode="HTML")
        bot.register_next_step_handler(msg, step_plan_reward)
    except: bot.send_message(message.chat.id, "❌ Invalid number.")

def step_plan_reward(message):
    try:
        reward = float(message.text)
        data = wizard_context.get(message.chat.id)
        if manage_plan("add", data['price'], reward):
            bot.send_message(message.chat.id, f"✅ Plan Saved!\nCost: ${data['price']} -> Get: ${reward}")
    except: pass

# --- D) DEL PLAN ---
def start_delplan_wizard(message):
    msg = bot.send_message(message.chat.id, "➖ <b>DELETE PLAN</b>\nEnter Price of plan to delete:", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_del_plan)

def step_del_plan(message):
    try:
        price = float(message.text)
        if manage_plan("del", price): bot.send_message(message.chat.id, f"🗑️ Plan ${price} deleted.")
        else: bot.send_message(message.chat.id, "❌ Plan not found.")
    except: pass

# ==========================================
# 3. CALLBACK HANDLER (ROUTER)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("wiz_") or call.data.startswith("gkey_"))
def wizard_callbacks(call: CallbackQuery):
    chat_id = call.message.chat.id
    
    # Navigation
    if call.data == "wiz_page_next":
        wizard_context[chat_id]['page'] += 1
        bot.delete_message(chat_id, call.message.message_id)
        send_service_menu(chat_id)
    elif call.data == "wiz_page_prev":
        wizard_context[chat_id]['page'] -= 1
        bot.delete_message(chat_id, call.message.message_id)
        send_service_menu(chat_id)

    # Selection
    elif call.data.startswith("wiz_sel_"):
        service = call.data.split("_")[2]
        data = wizard_context.get(chat_id)
        target = data['target']
        bot.delete_message(chat_id, call.message.message_id)
        call.message.text = f"/call {target} {service}"
        from handlers.call import handle_call
        handle_call(call.message)

    # Admin Triggers
    elif call.data == "wiz_addbal":
        bot.delete_message(chat_id, call.message.message_id)
        start_balance_wizard(call.message)
    elif call.data == "wiz_genkey":
        bot.delete_message(chat_id, call.message.message_id)
        start_genkey_wizard(call.message)
    elif call.data == "wiz_addplan":
        bot.delete_message(chat_id, call.message.message_id)
        start_addplan_wizard(call.message)
    elif call.data == "wiz_delplan":
        bot.delete_message(chat_id, call.message.message_id)
        start_delplan_wizard(call.message)

    # Key Generation Logic
    elif call.data.startswith("gkey_"):
        days = int(call.data.split("_")[1])
        key = create_license(days)
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, f"🎟️ <b>KEY CREATED</b>\nDuration: {days} Days\n\n<code>{key}</code>", parse_mode="HTML")