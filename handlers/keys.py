import traceback
from telebot.types import Message
from config import bot, PLAN_CREDITS
from database import get_connection, add_subscription_days, register_user, add_balance

# ==========================================
# 1. LÓGICA DE PROCESAMIENTO
# ==========================================
def process_key_logic(message: Message):
    key_input = message.text.strip()
    user_id = message.from_user.id 
    
    print(f"🔑 Procesando Key: {key_input} para User: {user_id}")

    if key_input.startswith("/") and not key_input.startswith("/redeem"):
        bot.reply_to(message, "⚠️ **Action Cancelled.**", parse_mode="Markdown")
        return

    register_user(message.from_user)

    conn = get_connection()
    if not conn:
        bot.reply_to(message, "🔴 **System Error:** Database offline.")
        return

    try:
        cur = conn.cursor()
        
        # 1. BUSCAR LA KEY
        cur.execute("SELECT duration_days FROM otp_licenses WHERE key_code = %s AND status = 'active'", (key_input,))
        result = cur.fetchone()
        
        if result:
            duration = result[0]
            
            # 2. CALCULAR CRÉDITOS
            credits_to_add = 0.00
            if duration == 1: credits_to_add = PLAN_CREDITS.get("1_day", 5.0)
            elif duration == 7: credits_to_add = PLAN_CREDITS.get("1_week", 20.0)
            elif duration == 30: credits_to_add = PLAN_CREDITS.get("1_month", 50.0)
            else:
                # Si son días personalizados, damos $1 por día como fallback
                credits_to_add = float(duration)

            # 3. MARCAR COMO USADA
            cur.execute("UPDATE otp_licenses SET status='used', used_by=%s WHERE key_code=%s", (user_id, key_input))
            conn.commit()
            
            # 4. DAR TIEMPO Y SALDO
            success, new_date = add_subscription_days(user_id, duration)
            add_balance(user_id, credits_to_add) # Sumar el dinero
            
            if success:
                date_str = new_date.strftime("%Y-%m-%d")
                bot.reply_to(message, 
                    f"✅ **License Activated!**\n\n"
                    f"👤 User: {message.from_user.first_name}\n"
                    f"🔑 Key: `{key_input}`\n"
                    f"⏳ Added: {duration} Days\n"
                    f"💰 **Credits Added:** ${credits_to_add}\n"
                    f"📅 Expires: `{date_str}`", 
                    parse_mode="Markdown")
            else:
                bot.reply_to(message, "⚠️ **Error:** Key accepted but failed to add time.")
                
        else:
            bot.reply_to(message, "❌ **Invalid Key:**\nKey not found or already used.")
            
        cur.close()
        conn.close()

    except Exception as e:
        print(f"🔴 Key Error: {traceback.format_exc()}")
        bot.reply_to(message, "🔴 **Critical Error** processing key.")

# ==========================================
# 2. HANDLERS
# ==========================================

# A) Paso siguiente (Input manual)
def process_key_step(message):
    process_key_logic(message)

# B) Detección Automática (Regex)
@bot.message_handler(regexp=r"^KEY-")
def auto_detect_key(message):
    process_key_logic(message)

# C) Comando Manual
@bot.message_handler(commands=['redeem'])
def manual_redeem(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "Usage: `/redeem KEY-XXXX`")
        return
    
    message.text = args[1] 
    process_key_logic(message)
