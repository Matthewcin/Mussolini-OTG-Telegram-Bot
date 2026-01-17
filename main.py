import config
from database import init_db
from keep_alive import start_server
# Importamos el bot desde config para poder manipularlo
from config import bot 

# ==========================================
# IMPORT HANDLERS
# ==========================================
import handlers.start
import handlers.admin
import handlers.keys
import handlers.callbacks
import handlers.utils
import handlers.payments 

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("1/4 Initializing Render ...")
    
    # --- BLINDAJE ANTI-CONFLICTO ---
    try:
        print("🧹 Eliminando Webhooks viejos...")
        bot.remove_webhook() # Forzamos a Telegram a olvidar el Webhook
        import time
        time.sleep(1) # Le damos un respiro de 1 segundo
    except Exception as e:
        print(f"⚠️ Warning limpiando webhook: {e}")
    # -------------------------------

    print("2/4 Initializing Neon Console (Database) ...")
    init_db()
    
    print("3/4 Initializing Web Server (Hoodpay Listener) ...")
    start_server()
    
    print("🟢 All Good - Bot is Online and Running...")
    
    # Usamos allowed_updates para ahorrar datos y evitar conflictos raros
    bot.infinity_polling(skip_pending=True, allowed_updates=["message", "callback_query", "pre_checkout_query", "successful_payment"])

