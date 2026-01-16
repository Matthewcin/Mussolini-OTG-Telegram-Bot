from flask import Flask, request, jsonify
from threading import Thread
from database import add_subscription_days
from config import bot, HOODPAY_MERCHANT_ID
import handlers.payments # Para acceder a PLANS si es necesario

app = Flask('')

@app.route('/')
def home():
    return "I am alive and listening for Payments!"

# ==========================================
# WEBHOOK HOODPAY
# ==========================================
@app.route('/hoodpay/webhook', methods=['POST'])
def hoodpay_webhook():
    try:
        data = request.json
        print(f"💰 Hoodpay Webhook Received: {data}")
        
        # Validar que sea un pago completado
        # Nota: La estructura del JSON depende de Hoodpay. 
        # Normalmente buscan "status": "COMPLETED" o "PAID"
        status = data.get("status")
        
        if status == "COMPLETED" or status == "PAID":
            # Extraer Metadata (User ID y Plan)
            # Hoodpay suele devolver la metadata que enviamos al crear el pago
            metadata = data.get("metadata", {})
            user_id = metadata.get("user_id")
            plan_type = metadata.get("plan_type")
            
            if user_id and plan_type:
                # Calcular días
                days = 0
                if plan_type == "daily": days = 1
                elif plan_type == "weekly": days = 7
                elif plan_type == "monthly": days = 30
                
                # Dar la licencia en base de datos
                success, new_date = add_subscription_days(user_id, days)
                
                if success:
                    # Avisar al usuario por Telegram
                    try:
                        formatted_date = new_date.strftime("%Y-%m-%d %H:%M")
                        msg = (
                            f"✅ **PAYMENT RECEIVED!**\n\n"
                            f"Your plan ({plan_type}) has been activated.\n"
                            f"Expires on: `{formatted_date}`\n\n"
                            f"Type /commands to start."
                        )
                        bot.send_message(user_id, msg, parse_mode="Markdown")
                        print(f"✅ User {user_id} activated via Webhook.")
                    except Exception as e:
                        print(f"Error sending msg to user: {e}")
                
                return jsonify({"status": "success"}), 200
            
        return jsonify({"status": "ignored"}), 200

    except Exception as e:
        print(f"🔴 Webhook Error: {e}")
        return jsonify({"status": "error"}), 500

def run():
    # En Render, el puerto lo asigna la variable de entorno PORT automáticamente
    app.run(host='0.0.0.0', port=8080)

def start_server():
    t = Thread(target=run)
    t.start()
