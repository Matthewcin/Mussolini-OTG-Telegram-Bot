import config
from database import init_db
from keep_alive import start_server

# ==========================================
# IMPORT HANDLERS
# ==========================================
import handlers.start
import handlers.admin
import handlers.keys
import handlers.callbacks
import handlers.utils

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("1/3 Initializing Render ...")
    print("2/3 Initializing Neon Console (Database) ...")
    print("3/3 Initializing Uptime Robot ...")
    init_db()
    start_server()
    print("🟢 All Good - Bot is Online and Running...")
    config.bot.infinity_polling()
