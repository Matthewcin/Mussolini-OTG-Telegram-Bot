import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, HOODPAY_API_TOKEN, HOODPAY_MERCHANT_ID
from database import get_plan_by_id

# ==========================================
# 💸 HOODPAY INTEGRATION (CORREGIDO)
# ==========================================

def create_dynamic_plan_invoice(user_id, plan_id):
    """Crea un link de pago para un Plan de Saldo."""
    
    # 1. Obtener datos del plan
    plan = get_plan_by_id(plan_id) # (price, reward)
    if not plan:
        return bot.send_message(user_id, "❌ Error: Plan not found.")

    price = float(plan[0])
    reward = float(plan[1])
    
    # 2. Verificar Variables
    if not HOODPAY_API_TOKEN or not HOODPAY_MERCHANT_ID:
        print("🔴 ERROR: Faltan credenciales de Hoodpay (TOKEN/MERCHANT_ID).")
        return bot.send_message(user_id, "❌ System Error: Payments not configured.")

    # 3. Request
    url = "https://api.hoodpay.io/v1/payment/create"
    headers = {
        "Authorization": f"Bearer {HOODPAY_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "business_id": HOODPAY_MERCHANT_ID, # Mapeamos tu Merchant ID al campo business_id
        "amount": price,
        "currency": "USD",
        "description": f"Balance Top-up: ${reward}",
        "redirect_url": "https://t.me/MussoliniOtpBot" # Opcional: pon tu bot user
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        # Logs para debug en consola de Render
        print(f"💰 Hoodpay Response: {data}")

        if response.status_code in [200, 201] and data.get('success'):
            pay_url = data['data']['checkout_url']
            pay_id = data['data']['id']
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("💳 Click to Pay", url=pay_url))
            markup.add(InlineKeyboardButton("✅ Check Payment", callback_data=f"chk_plan_{pay_id}_{plan_id}"))
            
            bot.send_message(user_id, 
                             f"💎 <b>INVOICE GENERATED</b>\n"
                             f"━━━━━━━━━━━━━━━━━━━━\n"
                             f"💵 <b>Amount:</b> ${price}\n"
                             f"💰 <b>Reward:</b> ${reward}\n\n"
                             f"<i>Click below to pay via Crypto/Card.</i>", 
                             reply_markup=markup, parse_mode="HTML")
        else:
            err_msg = data.get('message', 'Unknown Error')
            bot.send_message(user_id, f"❌ Gateway Error: {err_msg}")
            
    except Exception as e:
        print(f"🔴 Request Exception: {e}")
        bot.send_message(user_id, "❌ Connection Error.")

def create_script_invoice(user_id, script_id, price, script_title):
    """Crea pago para Script."""
    
    if not HOODPAY_API_TOKEN or not HOODPAY_MERCHANT_ID:
        return bot.send_message(user_id, "❌ Payments not configured.")

    url = "https://api.hoodpay.io/v1/payment/create"
    headers = {
        "Authorization": f"Bearer {HOODPAY_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "business_id": HOODPAY_MERCHANT_ID,
        "amount": float(price),
        "currency": "USD",
        "description": f"Script: {script_title}",
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if response.status_code in [200, 201] and data.get('success'):
            pay_url = data['data']['checkout_url']
            pay_id = data['data']['id']
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("💳 Pay Crypto", url=pay_url))
            markup.add(InlineKeyboardButton("✅ I Paid", callback_data=f"chk_scr_{pay_id}_{script_id}"))
            
            bot.send_message(user_id, f"💎 <b>BUY SCRIPT: {script_title}</b>", reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(user_id, "❌ Error generating invoice.")
    except:
        bot.send_message(user_id, "❌ System Error.")

def check_payment_status(payment_id):
    """Verifica estado del pago."""
    if not HOODPAY_API_TOKEN: return False
    
    url = f"https://api.hoodpay.io/v1/payment/{payment_id}"
    headers = {"Authorization": f"Bearer {HOODPAY_API_TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data.get('success') and data['data']['status'] == 'COMPLETED':
            return True
    except: pass
    return False