import time
from telebot.types import Message
from config import bot

@bot.message_handler(commands=['clear', 'clean'])
def cmd_clear(message: Message):
    """
    Deletes the last 30 messages in the chat to clean the view.
    Note: Can only delete messages less than 48 hours old.
    """
    chat_id = message.chat.id
    current_msg_id = message.message_id
    
    status_msg = bot.send_message(chat_id, "**Cleaning chat...**", parse_mode="Markdown")
    
    # Loop backwards to delete messages
    # We try to delete the last 30 messages (including the /clear or /clean command :D)
    for i in range(current_msg_id, current_msg_id - 30, -1): # <--- Modify the '30' Thing to delete more Messages.
        try:
            bot.delete_message(chat_id, i)
        except Exception:
            # If the message is too old or doesn't exist, skip it.
            continue

    # "Cleaning..." status message gone at this point.
    try:
        bot.delete_message(chat_id, status_msg.message_id)
    except:
        pass

    # Send final confirmation
    bot.send_message(chat_id, "**Chat Cleared!**", parse_mode="Markdown")
