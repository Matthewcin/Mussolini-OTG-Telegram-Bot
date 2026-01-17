import time
import logging
from config import bot
from database import init_db
from keep_alive import start_server
from telebot.apihelper import ApiTelegramException

# Importamos todos los handlers
import handlers.start
import handlers.callbacks
import handlers.payments 
import handlers.admin
import handlers.keys

# Configurar logs básicos
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("🚀 INICIANDO SISTEMA MUSSOLINI-OTP...")

    # 1. Base de Datos
    print("--- 1. Conectando DB ---")
    init_db()

    # 2. Servidor Web (Flask para Hoodpay)
    print("--- 2. Arrancando Servidor Web ---")
    start_server()

    # 3. Limpieza de Webhooks (Por si acaso)
    print("--- 3. Limpiando Webhooks ---")
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception as e:
        print(f"⚠️ Aviso: {e}")

    # 4. BUCLE INFINITO DE CONEXIÓN (La Solución al 409)
    print("--- 4. Iniciando Bot con Auto-Reconexión ---")
    
    while True:
        try:
            print("📡 Conectando con Telegram...")
            # skip_pending=True borra mensajes viejos acumulados para no saturar
            bot.infinity_polling(skip_pending=True, allowed_updates=["message", "callback_query"], timeout=60, long_polling_timeout=60)
        
        except Exception as e:
            # Si ocurre un error, analizamos cuál es
            error_str = str(e)
            
            if "Conflict" in error_str or "409" in error_str:
                print("🔴 CONFLICTO DETECTADO (409): Otra instancia está corriendo.")
                print("⏳ Esperando 15 segundos a que la versión vieja se cierre...")
                time.sleep(15) # Esperamos a que Render mate al bot viejo
            
            elif "Connection" in error_str:
                print("🟠 Error de Conexión. Reintentando en 5 seg...")
                time.sleep(5)
                
            else:
                print(f"⚠️ Error desconocido en Polling: {e}")
                print("🔄 Reiniciando servicio en 5 segundos...")
                time.sleep(5)
