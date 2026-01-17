import requests
import json
import traceback # Para ver la línea exacta donde falla
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, HOODPAY_API_TOKEN, WEBHOOK_BASE_URL

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
    # Mantenemos el plan de prueba de $1
    "dev_test": {
        "title": "Developer Test",
        "price": 1.00, 
        "days": 1
    }
}

def create_hoodpay_payment(chat_id, plan_type):
    """
    Genera un link de Hoodpay y, si falla, ENVÍA EL LOG DE ERROR AL CHAT.
    """
    
    # 1. LOG: Verificamos variables antes de empezar
    if not HOODPAY_API_TOKEN:
        bot.send_message(chat_id, "🚫 **Error Crítico:** Falta `HOODPAY_API_TOKEN` en las variables de entorno.")
        return
    if not WEBHOOK_BASE_URL:
        bot.send_message(chat_id, "🚫 **Error Crítico:** Falta `WEBHOOK_BASE_URL` en las variables de entorno.")
        return

    plan = PLANS.get(plan_type)
    if not plan: 
        bot.send_message(chat_id, f"🚫 **Error:** El plan `{plan_type}` no está definido en el código.")
        return

    # 2. Preparamos la petición
    url = "https://api.hoodpay.io/v1/payments"
    
    headers = {
        "Authorization": f"Bearer {HOODPAY_API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Aquí definimos la URL del webhook igual que en tu panel
    webhook_target = f"{WEBHOOK_BASE_URL}/webhook/hoodpay"

    payload = {
        "amount": plan["price"],
        "currency": "USD",
        "description": f"BIGFATOTP - {plan['title']}",
        "redirect_url": "https://t.me/MussoliniIOTPBot", 
        "webhook_url": webhook_target, 
        "metadata": {
            "user_id": chat_id,
            "plan_type": plan_type
        }
    }

    bot.send_message(chat_id, f"⚙️ **Iniciando solicitud a Hoodpay...**\nTarget: `{webhook_target}`", parse_mode="Markdown")

    try:
        # 3. Intentamos conectar
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        # 4. Analizamos la respuesta
        try:
            data = response.json()
        except json.JSONDecodeError:
            # Si Hoodpay devuelve HTML (error 500 o 404 del servidor de ellos)
            bot.send_message(chat_id, f"⚠️ **Hoodpay devolvió algo que no es JSON:**\nStatus: {response.status_code}\nTexto: `{response.text[:200]}`", parse_mode="Markdown")
            return

        # 5. ÉXITO (Código 200 o 201 y existe "data")
        if response.status_code in [200, 201] and "data" in data and "url" in data["data"]:
            checkout_url = data["data"]["url"] 
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"💸 Pagar ${plan['price']}", url=checkout_url))
            
            bot.send_message(
                chat_id,
                f"✅ **Link Generado**\n"
                f"Plan: {plan['title']}\n"
                f"Link: [Click Aquí]({checkout_url})",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            
        # 6. FALLO DE API (Hoodpay dice que no)
        else:
            # Convertimos el JSON de error a texto bonito
            error_details = json.dumps(data, indent=2)
            bot.send_message(
                chat_id, 
                f"❌ **Hoodpay rechazó la compra:**\n"
                f"Status Code: `{response.status_code}`\n"
                f"Respuesta:\n```json\n{error_details}\n```", 
                parse_mode="Markdown"
            )

    except Exception as e:
        # 7. FALLO DE PYTHON (Librerías, Conexión, etc.)
        tb = traceback.format_exc()
        print(f"ERROR EN PAYMENTS: {tb}") # Esto va al log de Render
        bot.send_message(
            chat_id, 
            f"☠️ **Error Interno del Bot:**\n"
            f"Tipo: `{type(e).__name__}`\n"
            f"Mensaje: `{str(e)}`",
            parse_mode="Markdown"
        )