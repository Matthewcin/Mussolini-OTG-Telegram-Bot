import time
import logging
from config import bot
from database import init_db
from keep_alive import start_server

# IMPORTAR TODOS LOS HANDLERS
import handlers.start
import handlers.callbacks
import handlers.payments 
import handlers.admin
import handlers.keys
import handlers.utils  
import handlers.call
import handlers.scripts
import handlers.profile
import handlers.sms # <--- NUEVO
import handlers.cvv # <--- NUEVO

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("🚀 INICIANDO SISTEMA MUSSOLINI-OTP...")
    
    init_db()
    start_server()

    try:
        bot.remove_webhook()
        time.sleep(1)
    except: pass

    print("--- Bot Escuchando ---")
    
    while True:
        try:
            bot.infinity_polling(skip_pending=True, allowed_updates=["message", "callback_query"], timeout=60, long_polling_timeout=60)
        except Exception as e:
            error_str = str(e)
            if "Conflict" in error_str or "409" in error_str:
                print("🔴 Conflicto 409 detectado. Esperando 15s...")
                time.sleep(15)
            else:
                print(f"⚠️ Error: {e}")
                time.sleep(5)
