import requests
import traceback
from config import LOG_BOT_TOKEN, LOG_CHANNEL_ID

def send_log(text, level="INFO"):
    """
    Envía un mensaje al canal de logs.
    Niveles: INFO (🟢), WARNING (⚠️), ERROR (🔴), PAYMENT (💰)
    """
    if not LOG_BOT_TOKEN or not LOG_CHANNEL_ID:
        # Si no están configurados, no hacemos nada (para no romper el bot)
        return

    # Emojis según el nivel
    if level == "INFO": icon = "ℹ️"
    elif level == "SUCCESS": icon = "🟢"
    elif level == "WARNING": icon = "⚠️"
    elif level == "ERROR": icon = "🔴"
    elif level == "PAYMENT": icon = "💸"
    else: icon = "📢"

    # Formato del mensaje
    formatted_text = f"{icon} **[{level}]**\n{text}"

    url = f"https://api.telegram.org/bot{LOG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": LOG_CHANNEL_ID,
        "text": formatted_text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        # Enviamos con timeout corto para no bloquear el bot si Telegram va lento
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass # Si falla el log, no queremos que se caiga el bot principal

def log_error(e, context="General"):
    """
    Envía un error detallado (Traceback) al canal.
    """
    tb = traceback.format_exc()
    # Cortamos el error si es muy largo para que quepa en Telegram
    if len(tb) > 3500: tb = tb[:3500] + "..."
    
    msg = f"Excepción en: `{context}`\nError: `{str(e)}`\n\nCode:\n```\n{tb}\n```"
    send_log(msg, level="ERROR")
