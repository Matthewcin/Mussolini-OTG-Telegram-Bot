import config
from database import init_db
from keep_alive import start_server

# ==========================================
# 📥 IMPORT HANDLERS (LOGIC)
# ==========================================
# We must import these modules so the bot "knows" they exist.
import handlers.start
import handlers.admin
import handlers.callbacks 

# ==========================================
# 🚀 MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("⏳ Initializing Systems...")
    
    # 1. Initialize Database
    init_db()
    
    # 2. Start Web Server (For Render)
    # This prevents Render from crashing due to "Port binding error"
    start_server()
    
    # 3. Start Bot Polling
    print("🤖 Bot is Online and Running...")
    config.bot.infinity_polling()
