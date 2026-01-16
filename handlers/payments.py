import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, HOODPAY_MERCHANT_ID, HOODPAY_API_TOKEN, WEBHOOK_BASE_URL

# ==========================================
# PAYMENT CONFIGURATION
# ==========================================
PLANS = {
    "daily": {
        "title": "Daily License",
        "price": 50.00,
        "days": 1
    },
    "weekly": {
        "title": "Weekly License",
        "price": 150.00,
        "days": 7
    },
    "monthly": {
        "title": "Monthly License",
        "price": 285.00,
        "days": 30
    },
    # PLAN DE PRUEBA (SOLO PARA TI)
    "dev_test": {
        "title": "Developer Test",
        "price": 1.00, 
        "days": 1
    }
}

def create_hoodpay_payment(chat_id, plan_type):
    """
    Generates a payment link using Hoodpay API.
    """
    if not HOODPAY_API_TOKEN or not WEBHOOK_BASE_URL:
        bot.send_message(chat_id, "🔴 **System Error:** Payment configuration missing (Token or Webhook URL).")
        return

    plan = PLANS.get(plan_type)
    if not plan: return

    # Hoodpay API Endpoint
    url = "https://api.hoodpay.io/v1/payments"
    
    headers = {
        "Authorization": f"Bearer {HOODPAY_API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Payload para crear el pago
    payload = {
        "amount": plan["price"],
        "currency": "USD",
        "description": f"BIGFATOTP - {plan['title']}",
        "redirect_url": "https://t.me/MussoliniIOTPBot", 
        # CORRECCION AQUI: Usamos la ruta que tienes en la foto
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/hoodpay", 
        "metadata": {
            "user_id": chat_id,
            "plan_type": plan_type
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        if response.status_code in [200, 201] and "data" in data:
            checkout_url = data["data"]["url"] 
            
            # Crear botón con el link
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"💸 Pay ${plan['price']} (Hoodpay)", url=checkout_url))
            
            bot.send_message(
                chat_id,
                f"💳 **Purchase: {plan['title']}**\n"
                f"💵 Amount: ${plan['price']} USD\n\n"
                f"Click the button below to pay securely via Hoodpay.\n"
                f"**Note:** Crypto/Card payments may take a few minutes to confirm.",
                reply_markup=markup,
                parse_mode="Markdown"
            )
        else:
            print(f"🔴 Hoodpay API Error: {data}")
            bot.send_message(chat_id, f"⚠️ Error generating payment link.\nDebug: `{data}`", parse_mode="Markdown")
            
    except Exception as e:
        print(f"Exception creating payment: {e}")
        bot.send_message(chat_id, "⚠️ Server Error generating payment.")
