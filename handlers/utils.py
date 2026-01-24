from telebot.types import Message
from config import bot

@bot.message_handler(commands=['clear', 'clean'])
def cmd_clear(message: Message):
    """
    Intenta borrar los últimos 50 mensajes del chat.
    """
    chat_id = message.chat.id
    message_id = message.message_id
    
    # Enviamos mensaje de "Borrando..." y guardamos su ID para borrarlo al final
    status_msg = bot.send_message(chat_id, "🧹 **Cleaning Chat...**", parse_mode="Markdown")
    
    # Intentamos borrar los últimos 50 mensajes hacia atrás
    # Empezamos desde el mensaje del comando (/clean) hacia atrás
    for i in range(message_id, message_id - 50, -1):
        try:
            bot.delete_message(chat_id, i)
        except Exception:
            # Si falla (mensaje muy viejo o no existe), simplemente continuamos
            continue

    # Al final, intentamos borrar el mensaje de "Cleaning..." si sigue ahí
    try:
        bot.delete_message(chat_id, status_msg.message_id)
    except:
        pass

    # Mensaje final que se autodestruye en 3 segundos (opcional, para dejarlo 100% limpio)
    final = bot.send_message(chat_id, "✨ **Chat Cleared!**", parse_mode="Markdown")
    
    # Tip Pro: Podrías usar time.sleep y borrar este mensaje también, 
    # pero bloquearía el bot unos segundos. Mejor dejarlo así.
