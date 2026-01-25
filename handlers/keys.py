import traceback
from telebot.types import Message
from config import bot
from database import get_connection, add_subscription_days, register_user

# ==========================================
# 1. LÓGICA DE PROCESAMIENTO
# ==========================================
def process_key_logic(message: Message):
    """
    Función central que procesa la clave, venga de donde venga.
    """
    key_input = message.text.strip()
    
    # CORRECCIÓN IMPORTANTE:
    # message.chat.id = ID del Grupo (si están en grupo)
    # message.from_user.id = ID de la Persona (siempre)
    user_id = message.from_user.id 
    
    print(f"🔑 Procesando Key: {key_input} para User Real: {user_id}")

    # Si el usuario mandó un comando en vez de una key, cancelamos
    if key_input.startswith("/") and not key_input.startswith("/redeem"):
        bot.reply_to(message, "⚠️ **Action Cancelled.**", parse_mode="Markdown")
        return

    # PASO DE SEGURIDAD:
    # Aseguramos que el usuario exista en la DB antes de intentar darle días.
    # Si es la primera vez que usa el bot (y lo hace desde un grupo), esto lo registra.
    register_user(message.from_user)

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
            
            # 2. MARCAR COMO USADA
            # Guardamos el ID de la persona, NO del grupo
            cur.execute("UPDATE otp_licenses SET status='used', used_by=%s WHERE key_code=%s", (user_id, key_input))
            conn.commit()
            
            # 3. DAR EL TIEMPO
            success, new_date = add_subscription_days(user_id, duration)
            
            if success:
                date_str = new_date.strftime("%Y-%m-%d")
                # reply_to responde en el grupo citando al usuario
                bot.reply_to(message, f"✅ **License Activated!**\n\n👤 User: {message.from_user.first_name}\n🔑 Key: `{key_input}`\n⏳ Added: {duration} Days\n📅 Expires: `{date_str}`", parse_mode="Markdown")
            else:
                bot.reply_to(message, "⚠️ **Error:** Key accepted but failed to add time. Contact Admin.")
                
        else:
            # Opcional: Si quieres que solo responda en privado si falla para no spammear grupos
            bot.reply_to(message, "❌ **Invalid Key:**\nKey not found or already used.")
            
        cur.close()
        conn.close()

    except Exception as e:
        print(f"🔴 Key Error: {traceback.format_exc()}")
        bot.reply_to(message, "🔴 **Critical Error** processing key.")


# ==========================================
# 2. HANDLERS
# ==========================================

# A) El "Paso siguiente" (Input manual)
def process_key_step(message):
    process_key_logic(message)

# B) Detección Automática (Regex)
@bot.message_handler(regexp=r"^KEY-")
def auto_detect_key(message):
    process_key_logic(message)

# C) Comando Manual (/redeem)
@bot.message_handler(commands=['redeem'])
def manual_redeem(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "Usage: `/redeem KEY-XXXX`")
        return
    
    # Preparamos el mensaje falso solo con la key
    message.text = args[1] 
    process_key_logic(message)
