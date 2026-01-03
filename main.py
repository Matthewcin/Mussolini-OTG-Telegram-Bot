import config
from database import init_db
from keep_alive import start_server

# ==========================================
# HANDLERS
# ==========================================
import handlers.start
import handlers.admin
import handlers.callbacks 

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("Initializing Systems...")
    
    # Initialize Database
    init_db()
    
    # Start Web Server (For Render in this Case...)
    start_server()
    
    # 3. Start Bot
    print("Bot is Online and Running...")
    config.bot.infinity_polling()

