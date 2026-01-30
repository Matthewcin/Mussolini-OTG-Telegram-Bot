from telebot.types import Message, CallbackQuery
from config import bot, ADMIN_IDS
from database import get_setting

# ==========================================
# 🛡️ MAINTENANCE MIDDLEWARE
# ==========================================

def is_maintenance_active():
    """Check DB for maintenance flag."""
    status = get_setting("maintenance_mode")
    return status == "ON"

@bot.message_handler(func=lambda message: is_maintenance_active() and message.from_user.id not in ADMIN_IDS)
def maintenance_blocker_msg(message: Message):
    """Intercepta TODOS los mensajes si hay mantenimiento."""
    maint_text = get_setting("maintenance_msg")
    if not maint_text:
        maint_text = "⚠️ <b>SYSTEM MAINTENANCE</b>\n\nWe are updating the bot. Please wait."
    
    bot.reply_to(message, maint_text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: is_maintenance_active() and call.from_user.id not in ADMIN_IDS)
def maintenance_blocker_call(call: CallbackQuery):
    """Intercepta TODOS los botones si hay mantenimiento."""
    maint_text = get_setting("maintenance_msg")
    if not maint_text:
        maint_text = "⚠️ Maintenance Mode Active."
        
    bot.answer_callback_query(call.id, "⚠️ Maintenance Mode", show_alert=True)
    # Opcional: Editar el mensaje para mostrar el aviso
    # bot.edit_message_text(maint_text, call.message.chat.id, call.message.message_id, parse_mode="HTML")