from telebot.types import Message
from config import bot
from database import get_connection, add_subscription_days

def process_key_step(message: Message):
    """
    Procesa la clave ingresada por el usuario después de presionar 'Enter Key'.
    """
    key_input = message.text.strip()
    user_id = message.chat.id
    
    # Si el usuario se arrepiente y escribe un comando, cancelamos para no dar error
    if key_input.startswith("/"):
        bot.reply_to(message, "⚠️ **Action Cancelled.**\nCommands detected. Please use the menu again if you want to redeem a key.", parse_mode="Markdown")
        return

    conn = get_connection()
    if not conn:
        bot.reply_to(message, "🔴 **System Error:** Database offline.")
        return

    try:
        cur = conn.cursor()
        
        # 1. BUSCAR LA KEY (Debe existir y estar 'active')
        cur.execute("SELECT duration_days FROM otp_licenses WHERE key_code = %s AND status = 'active'", (key_input,))
        result = cur.fetchone()
        
        if result:
            duration = result[0]
            
            # 2. MARCAR COMO USADA (Para evitar condiciones de carrera)
            cur.execute("UPDATE otp_licenses SET status='used', used_by=%s WHERE key_code=%s", (user_id, key_input))
            conn.commit() # Guardamos cambio en licencias
            
            # 3. DAR EL TIEMPO AL USUARIO
            # Usamos la función centralizada que ya maneja si es renovación o nuevo
            success, new_date = add_subscription_days(user_id, duration)
            
            if success:
                date_str = new_date.strftime("%Y-%m-%d")
                bot.reply_to(message, f"✅ **License Activated Successfully!**\n\n🔑 Key: `{key_input}`\n⏳ Added: {duration} Days\n📅 Expires: `{date_str}`\n\n_Thank you for your support!_", parse_mode="Markdown")
            else:
                bot.reply_to(message, "⚠️ **Error:** Key valid but failed to add days. Contact Admin.")
                
        else:
            bot.reply_to(message, "❌ **Invalid Key:**\nThis key does not exist or has already been used.")
            
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Key Processing Error: {e}")
        bot.reply_to(message, "🔴 **Critical Error** processing your request.")
