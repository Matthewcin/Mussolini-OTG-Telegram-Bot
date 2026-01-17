import requests
import json
import traceback
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, HOODPAY_API_TOKEN, HOODPAY_MERCHANT_ID, WEBHOOK_BASE_URL

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
    "dev_test": {
        "title": "Developer Test",
        "price": 1.00, 
        "days": 1
    }
}

def create_hoodpay_payment(chat_id, plan_type):
    """
    Genera un link de Hoodpay (Corregido: Metadata como String).
    """
    
    # 1. Verificaciones
    if not HOODPAY_API_TOKEN or not HOODPAY_MERCHANT_ID:
        bot.send_message(chat_id, "🚫 **Error:** Faltan credenciales de Hoodpay en config.")
        return

    plan = PLANS.get(plan_type)
    if not plan: 
        bot.send_message(chat_id, f"🚫 **Error:** Plan `{plan_type}` desconocido.")
        return

    # 2. URL
    url = f"https://api.hoodpay.io/v1/businesses/{HOODPAY_MERCHANT_ID}/payments"
    
    headers = {
        "Authorization": f"Bearer {HOODPAY_API_TOKEN}",
        "Content-Type": "application/json"
    }

    webhook_target = f"{WEBHOOK_BASE_URL}/webhook/hoodpay"

    # 3. PAYLOAD (AQUÍ ESTABA EL ERROR)
    payload = {
        "amount": plan["price"],
        "currency": "USD",
        "description": f"BIGFATOTP - {plan['title']}",
        "redirect_url": "https://t.me/MussoliniIOTPBot", 
        "webhook_url": webhook_target, 
        "metadata": {
            # CORRECCIÓN: Usamos str() para convertir el número a texto
            "user_id": str(chat_id),      
            "plan_type": str(plan_type)
        }
    }

    bot.send_message(chat_id, "⚙️ **Conectando con Hoodpay...**", parse_mode="Markdown")

    try:
        # 4. Enviar Petición
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            bot.send_message(chat_id, f"⚠️ **Error No-JSON:** Status {response.status_code}\n`{response.text[:200]}`", parse_mode="Markdown")
            return

        # 5. Éxito
        if response.status_code in [200, 201] and "data" in data and "url" in data["data"]:
            checkout_url = data["data"]["url"] 
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"💸 Pagar ${plan['price']}", url=checkout_url))
            
            bot.send_message(
                chat_id,
                f"✅ **Link de Pago Creado**\n"
                f"Plan: {plan['title']}\n"
                f"Precio: ${plan['price']}\n\n"
                f"Haz clic abajo para pagar con Crypto/Tarjeta.",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            
        else:
            # Fallo con detalles
            error_msg = json.dumps(data, indent=2)
            bot.send_message(chat_id, f"❌ **Hoodpay Rechazó:**\nStatus: {response.status_code}\n```json\n{error_msg}\n```", parse_mode="Markdown")

    except Exception as e:
        tb = traceback.format_exc()
        print(f"ERROR PAYMENTS: {tb}")
        bot.send_message(chat_id, f"☠️ **Error de Conexión:** `{str(e)}`", parse_mode="Markdown")
