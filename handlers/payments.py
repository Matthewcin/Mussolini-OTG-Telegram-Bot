import requests
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, HOODPAY_API_TOKEN, HOODPAY_MERCHANT_ID, WEBHOOK_BASE_URL

PLANS = {
    "daily": {"title": "Daily", "price": 50.00},
    "weekly": {"title": "Weekly", "price": 150.00},
    "monthly": {"title": "Monthly", "price": 285.00},
    "dev_test": {"title": "Test", "price": 1.00}
}

def create_hoodpay_payment(chat_id, plan_type):
    if not HOODPAY_API_TOKEN: return bot.send_message(chat_id, "Error: No Hoodpay Token")
    
    plan = PLANS.get(plan_type)
    if not plan: return
    
    url = f"https://api.hoodpay.io/v1/businesses/{HOODPAY_MERCHANT_ID}/payments"
    headers = {"Authorization": f"Bearer {HOODPAY_API_TOKEN}", "Content-Type": "application/json"}
    
    payload = {
        "amount": plan["price"],
        "currency": "USD",
        "description": f"OTP Bot - {plan['title']}",
        "redirect_url": "https://t.me/MussoliniIOTPBot", 
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/hoodpay", 
        "metadata": {
            "user_id": str(chat_id),      
            "plan_type": str(plan_type)
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        if "data" in data and "url" in data["data"]:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("💸 Pay Now", url=data["data"]["url"]))
            bot.send_message(chat_id, f"✅ Link Generated: ${plan['price']}", reply_markup=markup)
        else:
            bot.send_message(chat_id, f"Error: {data}")
    except Exception as e:
        bot.send_message(chat_id, f"Error: {e}")
