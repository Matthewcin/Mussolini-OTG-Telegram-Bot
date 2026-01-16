import secrets
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, ADMIN_IDS
from database import get_connection
from handlers.keys import process_key_step
# CAMBIO: Importamos la nueva función de Hoodpay
from handlers.payments import create_hoodpay_payment 

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    # ... [MANTENER TODO EL CÓDIGO DEL MENÚ PRINCIPAL IGUAL QUE ANTES] ...
    # ... (Solo pondré la parte de BUY_SUBS que cambia) ...

    # BUY SUBS (MENU SELECTION)
    if call.data == "buy_subs":
        bot.answer_callback_query(call.id)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📅 1 Day Access ($50)", callback_data="pay_daily"))
        markup.add(InlineKeyboardButton("🗓 1 Week Access ($150)", callback_data="pay_weekly"))
        markup.add(InlineKeyboardButton("📆 1 Month Access ($285)", callback_data="pay_monthly"))
        markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_home"))
        
        bot.edit_message_text(
            "💳 **SELECT A SUBSCRIPTION PLAN**\n\nSecure payment via Hoodpay (Crypto/Cards).\nAccess is automatic immediately after payment.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
    # PAYMENT TRIGGERS (Hoodpay)
    elif call.data == "pay_daily":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        create_hoodpay_payment(call.message.chat.id, "daily")
        
    elif call.data == "pay_weekly":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        create_hoodpay_payment(call.message.chat.id, "weekly")
        
    elif call.data == "pay_monthly":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        create_hoodpay_payment(call.message.chat.id, "monthly")

    # ... [RESTO DEL CÓDIGO IGUAL] ...
    # ADMIN PANEL, ETC.
    
    # IMPORTANTE: Si copiaste y pegaste lo anterior, asegúrate de mantener el resto del archivo callbacks.py
    # Si no quieres errores, simplemente reemplaza los bloques 'pay_daily', etc. con estos nuevos.
