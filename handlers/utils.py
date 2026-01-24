from telebot.types import Message
from config import bot

@bot.message_handler(commands=['clear', 'clean'])
def cmd_clear(message: Message):
    chat_id = message.chat.id
    msg_id = message.message_id
    try:
        for i in range(msg_id, msg_id - 30, -1):
            try: bot.delete_message(chat_id, i)
            except: continue
        bot.send_message(chat_id, "🧹 Chat Cleaned")
    except: pass
