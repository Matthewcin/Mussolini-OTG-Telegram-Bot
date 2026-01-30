from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import bot, ADMIN_IDS
from database import add_balance, get_available_services

# Wizard State Storage
# {chat_id: {'target': str, 'page': int, 'services': list}}
wizard_context = {}

# ==========================================
# 📞 CALL WIZARD (PAGINATED)
# ==========================================
def start_call_wizard(message):
    msg = bot.send_message(message.chat.id, 
        "📞 <b>ＣＡＬＬ  ＷＩＺＡＲＤ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Please enter the <b>Target Number</b>:\n"
        "<i>(Format: +123456789)</i>", 
        parse_mode="HTML")
    bot.register_next_step_handler(msg, step_call_number)

def step_call_number(message):
    if message.text.startswith("/"): return 
    
    # Store number and get services
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
    
    # Pagination slicing
    start = page * items_per_page
    end = start + items_per_page
    current_batch = services[start:end]
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Service Buttons
    buttons = []
    for svc in current_batch:
        buttons.append(InlineKeyboardButton(f"🏢 {svc}", callback_data=f"wiz_sel_{svc}"))
    markup.add(*buttons)
    
    # Navigation Buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data="wiz_page_prev"))
    
    if end < len(services):
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data="wiz_page_next"))
        
    if nav_buttons:
        markup.row(*nav_buttons)
        
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data="back_home"))
    
    text = (
        "🏢 <b>ＳＥＬＥＣＴ  ＳＥＲＶＩＣＥ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Choose a service script for this call:"
    )
    
    try:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
    except:
        pass # In case of edit conflicts

# ==========================================
# 🕹️ WIZARD CALLBACKS
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("wiz_"))
def wizard_callbacks(call: CallbackQuery):
    chat_id = call.message.chat.id
    
    # 1. Pagination Logic
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

    # 2. Service Selection & Execution
    elif call.data.startswith("wiz_sel_"):
        service = call.data.split("_")[2]
        data = wizard_context.get(chat_id)
        
        if data:
            target = data['target']
            bot.delete_message(chat_id, call.message.message_id)
            
            # Create a fake message object to reuse existing logic
            call.message.text = f"/call {target} {service}"
            
            # Lazy import to avoid circular dependency
            from handlers.call import handle_call
            handle_call(call.message)
            
            # Clean up
            del wizard_context[chat_id]

    # 3. Add Balance Wizard (Start)
    elif call.data == "wiz_addbal":
        bot.delete_message(chat_id, call.message.message_id)
        start_balance_wizard(call.message)

# ==========================================
# 📩 SMS WIZARD
# ==========================================
def start_sms_wizard(message):
    msg = bot.send_message(message.chat.id, "📩 <b>SMS Wizard:</b> Enter Number:", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_sms_number)

def step_sms_number(message):
    wizard_context[message.chat.id] = {'target': message.text}
    msg = bot.send_message(message.chat.id, "📝 Enter Service Name:", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_sms_service)

def step_sms_service(message):
    data = wizard_context.get(message.chat.id)
    if not data: return
    target = data['target']
    service = message.text
    
    from handlers.sms import handle_sms_command
    message.text = f"/sms {target} {service}"
    handle_sms_command(message)

# ==========================================
# 💳 ADMIN ADD BALANCE WIZARD
# ==========================================
def start_balance_wizard(message):
    msg = bot.send_message(message.chat.id, "💰 <b>Admin:</b> Enter User ID (or 'me'):", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_bal_user)

def step_bal_user(message):
    uid = message.text.lower()
    if uid == 'me': target = message.from_user.id
    else: 
        try: target = int(uid)
        except: return 
    
    wizard_context[message.chat.id] = {'target': target}
    msg = bot.send_message(message.chat.id, "💵 Enter Amount (USD):")
    bot.register_next_step_handler(msg, step_bal_amount)

def step_bal_amount(message):
    try:
        amount = float(message.text)
        data = wizard_context.get(message.chat.id)
        if add_balance(data['target'], amount):
             bot.send_message(message.chat.id, f"✅ Added ${amount} to {data['target']}")
    except: pass