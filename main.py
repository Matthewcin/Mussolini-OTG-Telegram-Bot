import time
import logging
import os
from config import bot
from database import init_db
from keep_alive import start_server

# IMPORTAR MANTENIMIENTO PRIMERO
import handlers.maintenance 

# IMPORTAR RESTO
import handlers.start
import handlers.callbacks
import handlers.payments
import handlers.admin
import handlers.keys
import handlers.utils
import handlers.call
import handlers.scripts
import handlers.profile
import handlers.sms
import handlers.cvv
import handlers.live
import handlers.wizard

logging.basicConfig(level=logging.INFO)

def setup_historical_logs():
    log_file = "bot.log"
    if not os.path.exists(log_file):
        with open(log_file, "w") as f: f.write("System Init.\n")

if __name__ == "__main__":
    print("🚀 STARTING...")
    setup_historical_logs()
    try: init_db()
    except Exception as e: print(e)
    try: start_server()
    except Exception as e: print(e)
    try: bot.remove_webhook(); time.sleep(1)
    except: pass

    print("--- 🤖 BOT ONLINE (v31.0) ---")
    
    while True:
        try:
            bot.infinity_polling(skip_pending=True, allowed_updates=["message", "callback_query"], timeout=60, long_polling_timeout=60)
        except Exception as e:
            if "Conflict" in str(e): time.sleep(15)
            else: time.sleep(5)