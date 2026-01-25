import requests
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, HOODPAY_API_TOKEN, HOODPAY_MERCHANT_ID, WEBHOOK_BASE_URL

PLANS = {
    "daily": {"title": "Daily License", "price": 50.00},
    "weekly": {"title": "Weekly License", "price": 150.00},
    "monthly": {"title": "Monthly License", "price": 285.00},
    "dev_test": {"title": "Dev Test", "price": 1.00}
}

def create_hoodpay_payment(chat_id, plan_type):
    if not HOODPAY_API_TOKEN: 
        return bot.send_message(chat_id, "❌ Error: Payments not configured.")
    
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
    
    msg = bot.send_message(chat_id, "⚙️ **Generating Payment Link...**", parse_mode="Markdown")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if "data" in data and "url" in data["data"]:
            checkout_url = data["data"]["url"]
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"💸 Pay ${plan['price']}", url=checkout_url))
            # 🔙 BOTÓN BACK (Importante por si se arrepienten)
            markup.add(InlineKeyboardButton("❌ Cancel / Back", callback_data="back_home"))
            
            bot.edit_message_text(
                f"✅ **Invoice Created**\n\nPlan: {plan['title']}\nAmount: **${plan['price']}**\n\nClick below to pay with Crypto/Card. Activation is instant.",
                chat_id=chat_id,
                message_id=msg.message_id,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        else:
            bot.edit_message_text(f"❌ Error creating invoice. Try again later.", chat_id=chat_id, message_id=msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Connection Error: {e}", chat_id=chat_id, message_id=msg.message_id)
