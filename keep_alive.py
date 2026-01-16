from flask import Flask, request, jsonify
from threading import Thread
from database import add_subscription_days
from config import bot, HOODPAY_MERCHANT_ID
import handlers.payments 
import json 

app = Flask('')

@app.route('/')
def home():
    return "I am alive and listening for Payments!"

# ==========================================
# WEBHOOK HOODPAY
# ==========================================
# CORRECCION AQUI: La ruta coincide con tu panel de Hoodpay
@app.route('/webhook/hoodpay', methods=['POST'])
def hoodpay_webhook():
    try:
        data = request.json
        
        # LOG DE DEPURACIÓN
        print("\n🔵 [WEBHOOK RECEIVED] -----------------------")
        print(json.dumps(data, indent=2))
        print("----------------------------------------------\n")
        
        status = data.get("status", "").upper()
        
        # Aceptamos varios estados de éxito
        if status in ["COMPLETED", "PAID", "SUCCESS"]:
            metadata = data.get("metadata", {})
            user_id = metadata.get("user_id")
            plan_type = metadata.get("plan_type")
            
            print(f"✅ Processing Payment -> User: {user_id}, Plan: {plan_type}")

            if user_id and plan_type:
                days = 0
                if plan_type == "daily": days = 1
                elif plan_type == "weekly": days = 7
                elif plan_type == "monthly": days = 30
                elif plan_type == "dev_test": days = 1 
                
                success, new_date = add_subscription_days(user_id, days)
                
                if success:
                    try:
                        formatted_date = new_date.strftime("%Y-%m-%d %H:%M")
                        msg = (
                            f"✅ **PAYMENT RECEIVED!**\n\n"
                            f"Your plan ({plan_type}) has been activated.\n"
                            f"Expires on: `{formatted_date}`\n\n"
                            f"Type /commands to start."
                        )
                        bot.send_message(user_id, msg, parse_mode="Markdown")
                        print(f"✅ User {user_id} activated successfully.")
                    except Exception as e:
                        print(f"🔴 Error sending Telegram msg: {e}")
                else:
                    print("🔴 Database Error: Could not add subscription days.")
                
                return jsonify({"status": "success"}), 200
            else:
                print("🟠 Metadata missing (user_id or plan_type not found).")
            
        else:
            print(f"🟠 Payment not completed yet. Status: {status}")
            return jsonify({"status": "ignored"}), 200

    except Exception as e:
        print(f"🔴 Webhook Critical Error: {e}")
        return jsonify({"status": "error"}), 500

def run():
    app.run(host='0.0.0.0', port=8080)

def start_server():
    t = Thread(target=run)
    t.start()
