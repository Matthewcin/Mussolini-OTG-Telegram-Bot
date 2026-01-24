import time
import logging
from config import bot
from database import init_db
from keep_alive import start_server

# IMPORTAR TODOS LOS HANDLERS (AQUÍ ESTABA EL ERROR ANTES)
import handlers.start
import handlers.callbacks
import handlers.payments 
import handlers.admin
import handlers.keys
import handlers.utils  
import handlers.call   

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("🚀 INICIANDO SISTEMA MUSSOLINI-OTP...")
    
    init_db()
    start_server()

    # Limpiar Webhooks viejos
    try:
        bot.remove_webhook()
        time.sleep(1)
    except: pass

    # Bucle Anti-Crash (Error 409)
    print("--- Bot Escuchando ---")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, allowed_updates=["message", "callback_query"], timeout=60, long_polling_timeout=60)
        except Exception as e:
            error_str = str(e)
            if "Conflict" in error_str or "409" in error_str:
                print("🔴 Conflicto 409. Esperando 15s...")
                time.sleep(15)
            else:
                print(f"⚠️ Error: {e}")
                time.sleep(5)
