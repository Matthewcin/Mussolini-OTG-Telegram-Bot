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

# Intercept Messages
@bot.message_handler(func=lambda message: is_maintenance_active() and message.from_user.id not in ADMIN_IDS)
def maintenance_blocker_msg(message: Message):
    """Intercepts ALL messages if maintenance is active."""
    maint_text = get_setting("maintenance_msg")
    if not maint_text:
        maint_text = "⚠️ <b>SYSTEM MAINTENANCE</b>\n\nWe are updating the bot. Please wait."
    
    try:
        bot.reply_to(message, maint_text, parse_mode="HTML")
    except: pass

# Intercept Callbacks (Buttons)
@bot.callback_query_handler(func=lambda call: is_maintenance_active() and call.from_user.id not in ADMIN_IDS)
def maintenance_blocker_call(call: CallbackQuery):
    """Intercepts ALL buttons if maintenance is active."""
    bot.answer_callback_query(call.id, "⚠️ Maintenance Mode Active", show_alert=True)