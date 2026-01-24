import requests
import traceback
from config import LOG_BOT_TOKEN, LOG_CHANNEL_ID

def send_log(text, level="INFO"):
    if not LOG_BOT_TOKEN or not LOG_CHANNEL_ID: return

    if level == "INFO": icon = "ℹ️"
    elif level == "SUCCESS": icon = "🟢"
    elif level == "WARNING": icon = "⚠️"
    elif level == "ERROR": icon = "🔴"
    elif level == "PAYMENT": icon = "💸"
    else: icon = "📢"

    formatted_text = f"{icon} **[{level}]**\n{text}"
    url = f"https://api.telegram.org/bot{LOG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": LOG_CHANNEL_ID, "text": formatted_text, "parse_mode": "Markdown"}

    try: requests.post(url, json=payload, timeout=5)
    except: pass

def log_error(e, context="General"):
    tb = traceback.format_exc()
    if len(tb) > 3500: tb = tb[:3500] + "..."
    msg = f"Excepción en: `{context}`\nError: `{str(e)}`\n\nCode:\n```\n{tb}\n```"
    send_log(msg, level="ERROR")
