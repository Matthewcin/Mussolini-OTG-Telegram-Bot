from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import bot, ADMIN_IDS
from database import add_balance, get_available_services, manage_plan, create_license

# ==========================================
# WIZARD CONTEXT STORAGE
# Stores temporary data for multi-step processes
# Format: {chat_id: {'target': '+123...', 'page': 0, ...}}
# ==========================================
wizard_context = {}

# ==========================================
# 1. USER WIZARDS (CALL & SMS)
# ==========================================

# --- CALL WIZARD ---
def start_call_wizard(message):
    msg = bot.send_message(
        message.chat.id, 
        "📞 <b>ＣＡＬＬ  ＷＩＺＡＲＤ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Please enter the <b>Target Number</b>:\n"
        "<i>(Format: +123456789)</i>", 
        parse_mode="HTML"
    )
    bot.register_next_step_handler(msg, step_call_number)

def step_call_number(message):
    if message.text.startswith("/"): return 
    
    # Init context for this user
    wizard_context[message.chat.id] = {
        'target': message.text,
        'page': 0,
        'services': get_available_services(message.chat.id)
    }
    send_service_menu(message.chat.id)

def send_service_menu(chat_id):
    data = wizard_context.get(chat_id)
    if not data: return
    
    services = data['services']
    page = data['page']
    items_per_page = 6
    
    # Pagination Slicing
    start = page * items_per_page
    end = start + items_per_page
    current_batch = services[start:end]
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Service Buttons
    buttons = [InlineKeyboardButton(f"🏢 {svc}", callback_data=f"wiz_sel_{svc}") for svc in current_batch]
    markup.add(*buttons)
    
    # Navigation Buttons
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data="wiz_page_prev"))
    if end < len(services):
        nav.append(InlineKeyboardButton("Next ➡️", callback_data="wiz_page_next"))
    
    if nav: markup.row(*nav)
    
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data="back_home"))
    
    bot.send_message(chat_id, "🏢 <b>SELECT SERVICE</b>\nChoose script to launch:", reply_markup=markup, parse_mode="HTML")

# --- SMS WIZARD ---
def start_sms_wizard(message):
    msg = bot.send_message(message.chat.id, "📩 <b>SMS Wizard:</b> Enter Target Number:", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_sms_number)

def step_sms_number(message):
    wizard_context[message.chat.id] = {'target': message.text}
    msg = bot.send_message(message.chat.id, "📝 Enter Service Name (e.g. PayPal):", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_sms_service)

def step_sms_service(message):
    data = wizard_context.get(message.chat.id)
    if not data: return
    
    # Lazy import to prevent circular dependency
    from handlers.sms import handle_sms_command
    
    # Simulate command
    message.text = f"/sms {data['target']} {message.text}"
    handle_sms_command(message)

# ==========================================
# 2. ADMIN WIZARDS (INTERACTIVE TOOLS)
# ==========================================

# --- A) ADD BALANCE ---
def start_balance_wizard(message):
    msg = bot.send_message(message.chat.id, "💰 <b>Admin:</b> Enter User ID (or type 'me'):", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_bal_user)

def step_bal_user(message):
    uid = message.text.lower()
    
    if uid == 'me': 
        target = message.from_user.id
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
             bot.send_message(message.chat.id, f"✅ Added <b>${amount}</b> to User <code>{data['target']}</code>", parse_mode="HTML")
        else:
             bot.send_message(message.chat.id, "❌ Database Error.")
    except: 
        bot.send_message(message.chat.id, "❌ Error: Not a valid number.")

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
        msg = bot.send_message(message.chat.id, f"💎 Price: <b>${price}</b>\nNow enter <b>Reward Balance</b> (How much credit user gets):", parse_mode="HTML")
        bot.register_next_step_handler(msg, step_plan_reward)
    except: 
        bot.send_message(message.chat.id, "❌ Invalid number.")

def step_plan_reward(message):
    try:
        reward = float(message.text)
        data = wizard_context.get(message.chat.id)
        if manage_plan("add", data['price'], reward):
            bot.send_message(message.chat.id, f"✅ <b>Plan Saved!</b>\nCost: ${data['price']} -> Get: ${reward}", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ Database Error.")
    except: pass

# --- D) DEL PLAN ---
def start_delplan_wizard(message):
    msg = bot.send_message(message.chat.id, "➖ <b>DELETE PLAN</b>\nEnter Price of plan to delete:", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_del_plan)

def step_del_plan(message):
    try:
        price = float(message.text)
        if manage_plan("del", price): 
            bot.send_message(message.chat.id, f"🗑️ Plan <b>${price}</b> deleted.", parse_mode="HTML")
        else: 
            bot.send_message(message.chat.id, "❌ Plan not found.", parse_mode="HTML")
    except: pass

# ==========================================
# 3. CALLBACK HANDLER (ROUTER)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("wiz_") or call.data.startswith("gkey_"))
def wizard_callbacks(call: CallbackQuery):
    chat_id = call.message.chat.id
    
    # --- NAVIGATION ---
    if call.data == "wiz_page_next":
        if chat_id in wizard_context:
            wizard_context[chat_id]['page'] += 1
            bot.delete_message(chat_id, call.message.message_id)
            send_service_menu(chat_id)
            
    elif call.data == "wiz_page_prev":
        if chat_id in wizard_context:
            wizard_context[chat_id]['page'] -= 1
            bot.delete_message(chat_id, call.message.message_id)
            send_service_menu(chat_id)

    # --- SERVICE SELECTION ---
    elif call.data.startswith("wiz_sel_"):
        service = call.data.split("_")[2]
        data = wizard_context.get(chat_id)
        if data:
            target = data['target']
            bot.delete_message(chat_id, call.message.message_id)
            
            # Simulate Command Call
            call.message.text = f"/call {target} {service}"
            from handlers.call import handle_call
            handle_call(call.message)
            
            # Clean context
            del wizard_context[chat_id]

    # --- ADMIN TRIGGERS (Launched from callbacks.py) ---
    elif call.data == "wiz_addbal":
        if call.from_user.id in ADMIN_IDS:
            bot.delete_message(chat_id, call.message.message_id)
            start_balance_wizard(call.message)
            
    elif call.data == "wiz_genkey":
        if call.from_user.id in ADMIN_IDS:
            bot.delete_message(chat_id, call.message.message_id)
            start_genkey_wizard(call.message)
            
    elif call.data == "wiz_addplan":
        if call.from_user.id in ADMIN_IDS:
            bot.delete_message(chat_id, call.message.message_id)
            start_addplan_wizard(call.message)
            
    elif call.data == "wiz_delplan":
        if call.from_user.id in ADMIN_IDS:
            bot.delete_message(chat_id, call.message.message_id)
            start_delplan_wizard(call.message)

    # --- KEY GENERATION ACTION ---
    elif call.data.startswith("gkey_"):
        if call.from_user.id in ADMIN_IDS:
            try:
                days = int(call.data.split("_")[1])
                key = create_license(days)
                bot.delete_message(chat_id, call.message.message_id)
                
                text = (
                    f"🎟️ <b>KEY GENERATED</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"⏱️ <b>Duration:</b> {days} Days\n"
                    f"🔑 <b>Code:</b>\n<code>{key}</code>\n\n"
                    f"<i>Tap to copy</i>"
                )
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("⬅ Admin Panel", callback_data="admin_panel"))
                
                bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
            except Exception as e:
                bot.send_message(chat_id, f"❌ Error: {e}")