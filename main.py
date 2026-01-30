import time
import logging
from config import bot
from database import init_db
from keep_alive import start_server

# ==========================================
# IMPORTAR TODOS LOS HANDLERS
# ==========================================
# Aquí cargamos toda la lógica del bot. 
# Si creas un archivo nuevo, agrégalo a esta lista.
import handlers.start       # Bienvenida y lógica de Referidos
import handlers.callbacks   # Menús, Botones y Twilio Debugger
import handlers.payments    # Hoodpay y Pagos
import handlers.admin       # Comandos de Admin extra
import handlers.keys        # Sistema de Keys
import handlers.utils       # Utilidades varias
import handlers.call        # Lógica de llamadas /call
import handlers.scripts     # 🆕 MERCADO DE SCRIPTS (/myscripts, /shop)
import handlers.profile     # Perfil de usuario
import handlers.sms         # Lógica de /sms
import handlers.cvv         # Lógica de /cvv
import handlers.live        # Panel en vivo

# Configuración básica de logs
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("🚀 INICIANDO SISTEMA BIGFATOTP...")
    
    # 1. Inicializar Base de Datos (Crear tablas nuevas si faltan)
    try:
        init_db()
    except Exception as e:
        print(f"🔴 Error Database: {e}")
    
    # 2. Iniciar Servidor Web (Flask para recibir llamadas de Twilio)
    try:
        start_server()
    except Exception as e:
        print(f"🔴 Error Server: {e}")

    # 3. Limpieza de Webhooks (Vital para evitar conflictos al reiniciar)
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception: 
        pass

    print("--- 🤖 Bot Online y Escuchando ---")
    
    # 4. Bucle Infinito (Anti-Caídas)
    while True:
        try:
            # infinity_polling reconecta automáticamente si se cae el internet
            bot.infinity_polling(
                skip_pending=True, 
                allowed_updates=["message", "callback_query"], 
                timeout=60, 
                long_polling_timeout=60
            )
        except Exception as e:
            error_str = str(e)
            
            # Error 409: Significa que tienes dos bots corriendo con el mismo Token
            if "Conflict" in error_str or "409" in error_str:
                print("🔴 Conflicto 409 detectado. Esperando 15s para reintentar...")
                time.sleep(15)
            
            # Error de Timeout: Problema de red momentáneo
            elif "ReadTimeout" in error_str or "ConnectionError" in error_str:
                print("⚠️ Red inestable. Reconectando en 3s...")
                time.sleep(3)
                
            else:
                print(f"⚠️ Error desconocido: {e}")
                time.sleep(5)