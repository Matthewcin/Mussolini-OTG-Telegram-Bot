import config
from database import init_db
from keep_alive import start_server

# Importar los handlers para que el bot "sepa" que existen
import handlers.start
import handlers.keys
import handlers.callbacks 

if __name__ == "__main__":
    print("⏳ Iniciando sistemas...")
    init_db()         # 1. Base de datos
    start_server()    # 2. Web Server para Render
    
    print("🤖 Bot Online!")
    config.bot.infinity_polling() # 3. Arrancar bot
