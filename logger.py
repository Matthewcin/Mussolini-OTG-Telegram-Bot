import requests
import traceback
import logging # <--- Importante para guardar en archivo
from config import LOG_BOT_TOKEN, LOG_CHANNEL_ID

# ==========================================
# 1. CONFIGURACIÓN DE ARCHIVO LOCAL (bot.log)
# ==========================================
# Esto crea el archivo que leerá el botón "Logs" del panel
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def send_log(text, level="INFO"):
    """
    Función híbrida:
    1. Guarda en bot.log (para el Panel Admin).
    2. Envía al Canal de Telegram (para notificaciones en vivo).
    """
    
    # --- PARTE A: GUARDAR EN ARCHIVO LOCAL ---
    try:
        # Quitamos asteriscos de Markdown para que el log de texto se vea limpio
        clean_text = text.replace("**", "").replace("__", "").replace("`", "")
        log_entry = f"[{level}] {clean_text}"
        
        if level == "ERROR":
            logging.error(log_entry)
        else:
            logging.info(log_entry)
    except: 
        pass # Si falla el archivo, no romper el bot

    # --- PARTE B: ENVIAR A TELEGRAM (TU CÓDIGO ORIGINAL) ---
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
    
    # 1. Guardar Traceback completo en archivo local
    logging.error(f"EXCEPTION in {context}: {str(e)}\n{tb}")

    # 2. Enviar a Telegram (Recortado para que no exceda el límite)
    if len(tb) > 3500: tb = tb[:3500] + "..."
    msg = f"Excepción en: `{context}`\nError: `{str(e)}`\n\nCode:\n```\n{tb}\n```"
    
    # Llamamos a send_log con nivel ERROR (esto enviará la alerta al canal)
    # Nota: No llamamos a logging.error aquí de nuevo porque send_log ya lo hace.
    # Pero para Telegram pasamos el mensaje formateado.
    
    if LOG_BOT_TOKEN and LOG_CHANNEL_ID:
        url = f"https://api.telegram.org/bot{LOG_BOT_TOKEN}/sendMessage"
        formatted_text = f"🔴 **[ERROR]**\n{msg}"
        payload = {"chat_id": LOG_CHANNEL_ID, "text": formatted_text, "parse_mode": "Markdown"}
        try: requests.post(url, json=payload, timeout=5)
        except: pass
