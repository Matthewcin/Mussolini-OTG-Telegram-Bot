import time
import logging
from config import bot
from database import init_db
from keep_alive import start_server

# Importamos los handlers para que el bot sepa qué hacer
import handlers.start
import handlers.callbacks
import handlers.payments 
import handlers.admin
import handlers.keys
# (Asegúrate de importar todos tus handlers aquí)

# Configurar logs para ver qué pasa en la consola de Render
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("🚀 INICIANDO SISTEMA...")

    # 1. Base de Datos
    print("--- 1. Conectando DB ---")
    init_db()

    # 2. Servidor Web (Para escuchar a Hoodpay)
    print("--- 2. Arrancando Servidor Web (Flask) ---")
    start_server()

    # 3. LIMPIEZA DE CONEXIONES (EL ARREGLO MÁGICO)
    # Esto borra cualquier webhook viejo que esté bloqueando el chat
    print("--- 3. Limpiando Webhooks Viejos ---")
    try:
        bot.remove_webhook()
        time.sleep(1) # Damos un respiro a la API
        print("✅ Webhook eliminado correctamente.")
    except Exception as e:
        print(f"⚠️ Advertencia borrando webhook: {e}")

    # 4. Arrancar el Bot
    print("--- 4. Bot Escuchando (Polling) ---")
    try:
        # allowed_updates ayuda a filtrar basura y reduce conflictos
        bot.infinity_polling(skip_pending=True, allowed_updates=["message", "callback_query"])
    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN POLLING: {e}")
