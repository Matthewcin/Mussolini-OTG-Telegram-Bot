import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, HOODPAY_API_KEY, HOODPAY_BUSINESS_ID
from database import get_plan_by_id

API_URL = "https://api.hoodpay.io/v1/payment"

# ==========================================
# 1. DYNAMIC PLAN INVOICE (DB BASED)
# ==========================================
def create_dynamic_plan_invoice(user_id, plan_id):
    # Buscamos el plan en la DB
    plan = get_plan_by_id(plan_id)
    if not plan:
        bot.send_message(user_id, "❌ Plan no longer exists.")
        return

    price, reward = plan
    price = float(price)
    reward = float(reward)

    headers = {
        "Authorization": f"Bearer {HOODPAY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "businessId": HOODPAY_BUSINESS_ID,
        "amount": price,
        "currency": "USD",
        "description": f"Top Up: ${reward} Credits",
        "metadata": {
            "type": "balance_topup",
            "user_id": user_id,
            "plan_id": plan_id,
            "reward_amount": reward
        }
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        data = response.json()
        
        if response.status_code in [200, 201] and 'data' in data:
            pay_url = data['data']['checkoutUrl']
            pay_id = data['data']['id']
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"💸 Pay ${price}", url=pay_url))
            # Callback para verificar (usaremos 'chk_plan_')
            markup.add(InlineKeyboardButton("✅ I Have Paid", callback_data=f"chk_plan_{pay_id}_{plan_id}"))
            
            bot.send_message(
                user_id,
                f"💳 <b>DEPOSIT INVOICE</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💵 <b>Pay:</b> ${price} USD\n"
                f"💰 <b>Receive:</b> ${reward} Credits\n"
                f"⏳ <b>Validity:</b> 30 Minutes\n\n"
                f"<i>Click below to pay via Crypto.</i>",
                reply_markup=markup,
                parse_mode="HTML"
            )
        else:
            bot.send_message(user_id, "❌ Error generating invoice.")
            print(f"Hoodpay Error: {data}")
            
    except Exception as e:
        print(f"Payment Ex: {e}")
        bot.send_message(user_id, "❌ System Error.")

# ==========================================
# 2. SCRIPT INVOICE
# ==========================================
def create_script_invoice(user_id, script_id, price, script_title):
    headers = {
        "Authorization": f"Bearer {HOODPAY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "businessId": HOODPAY_BUSINESS_ID,
        "amount": float(price),
        "currency": "USD",
        "description": f"Script: {script_title}",
        "metadata": {
            "type": "script_purchase",
            "user_id": user_id,
            "script_id": script_id
        }
    }
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        data = response.json()
        if response.status_code in [200, 201] and 'data' in data:
            pay_url = data['data']['checkoutUrl']
            pay_id = data['data']['id']
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("💸 Pay Now", url=pay_url))
            markup.add(InlineKeyboardButton("✅ I Have Paid", callback_data=f"chk_scr_{pay_id}_{script_id}"))
            bot.send_message(user_id, f"💎 <b>PURCHASE:</b> {script_title}\n💵 <b>Price:</b> ${price}", reply_markup=markup, parse_mode="HTML")
    except: pass

# ==========================================
# 3. CHECK STATUS
# ==========================================
def check_payment_status(payment_id):
    headers = {"Authorization": f"Bearer {HOODPAY_API_KEY}"}
    try:
        r = requests.get(f"{API_URL}/{payment_id}", headers=headers)
        data = r.json()
        if 'data' in data and 'status' in data['data']:
            if data['data']['status'].lower() in ['completed', 'paid']: return True
    except: pass
    return False