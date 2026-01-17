import requests
import json
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
    "dev_test": {
        "title": "Developer Test",
        "price": 1.00, 
        "days": 1
    }
}

def create_hoodpay_payment(chat_id, plan_type):
    """
    Generates a payment link using Hoodpay API with FULL DEBUGGING.
    """
    # 1. Verificación de Variables
    if not HOODPAY_API_TOKEN or not WEBHOOK_BASE_URL:
        bot.send_message(chat_id, "🔴 **Config Error:** Falta el Token o la URL del Webhook en Render.")
        return

    plan = PLANS.get(plan_type)
    if not plan: 
        bot.send_message(chat_id, f"🔴 **Plan Error:** El plan '{plan_type}' no existe.")
        return

    # 2. Configuración de la Petición
    url = "https://api.hoodpay.io/v1/payments"
    
    headers = {
        "Authorization": f"Bearer {HOODPAY_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "amount": plan["price"],
        "currency": "USD",
        "description": f"BIGFATOTP - {plan['title']}",
        "redirect_url": "https://t.me/MussoliniIOTPBot", 
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/hoodpay", 
        "metadata": {
            "user_id": chat_id,
            "plan_type": plan_type
        }
    }

    bot.send_message(chat_id, "⏳ Contactando con Hoodpay...", parse_mode="Markdown")

    try:
        # 3. Hacemos la petición
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # 4. Intentamos leer la respuesta
        try:
            data = response.json()
        except Exception:
            # Si falla al leer JSON, es porque Hoodpay devolvió un error HTML o texto
            raw_text = response.text[:500] # Solo los primeros 500 caracteres
            bot.send_message(chat_id, f"⚠️ **Error de Respuesta (No JSON):**\nStatus: {response.status_code}\n\n`{raw_text}`", parse_mode="Markdown")
            return

        # 5. Verificamos éxito
        if response.status_code in [200, 201] and "data" in data:
            checkout_url = data["data"]["url"] 
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"💸 Pagar ${plan['price']} (Hoodpay)", url=checkout_url))
            
            bot.send_message(
                chat_id,
                f"💳 **Link Generado Exitosamente**\n"
                f"Plan: {plan['title']}\n"
                f"Precio: ${plan['price']}\n",
                reply_markup=markup,
                parse_mode="Markdown"
            )
        else:
            # Error lógico de la API (ej: Token inválido)
            error_dump = json.dumps(data, indent=2)
            bot.send_message(chat_id, f"⚠️ **Hoodpay rechazó la petición:**\nStatus: {response.status_code}\n\n`{error_dump}`", parse_mode="Markdown")
            
    except Exception as e:
        # Error técnico (Conexión, Librería, etc)
        import traceback
        trace = traceback.format_exc()
        print(f"CRITICAL ERROR: {trace}") # Para los logs de Render
        bot.send_message(chat_id, f"🚫 **Error Crítico de Python:**\n`{str(e)}`", parse_mode="Markdown")
