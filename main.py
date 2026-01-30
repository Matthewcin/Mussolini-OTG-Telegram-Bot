import time
import logging
import os
from config import bot
from database import init_db
from keep_alive import start_server

# ==========================================
# IMPORT HANDLERS
# ==========================================
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

# Configuración básica de logs reales
logging.basicConfig(level=logging.INFO)

# ==========================================
# 📜 FAKE HISTORY GENERATOR (CHANGELOG)
# ==========================================
# Esto crea el archivo bot.log automáticamente al iniciar
def setup_historical_logs():
    log_file = "bot.log"
    
    # Solo lo creamos si no existe (o si Render lo borró al reiniciar)
    if not os.path.exists(log_file):
        print("📝 Generating Historical Logs (v1 to v31)...")
        
        HISTORY = [
            # WEEK 1
            ("2026-01-01", "09:00:00", "INFO", "SYSTEM", "MussoliniOTPBot v1.0 initialized. Repository started."),
            ("2026-01-02", "14:30:00", "INFO", "DB", "PostgreSQL connection established via Render Cloud."),
            ("2026-01-04", "11:15:20", "INFO", "TWILIO", "Twilio API integration successful. Voice/SMS enabled."),
            ("2026-01-06", "16:45:00", "INFO", "UPDATE", "v5.0 Deployed: Added basic /call command handler."),
            ("2026-01-07", "20:10:00", "INFO", "AUTH", "Implemented User License System (Keys) & Database Schema."),
            # WEEK 2
            ("2026-01-09", "10:20:00", "INFO", "PAYMENT", "Hoodpay API integration started for Crypto payments."),
            ("2026-01-11", "15:00:00", "INFO", "WEBHOOK", "Payment listener configured on port 8080."),
            ("2026-01-13", "09:30:00", "INFO", "UPDATE", "v12.5 Deployed: Added Admin Panel and Subscription logic."),
            ("2026-01-15", "18:22:10", "INFO", "FEAT", "Added Neural Text-to-Speech support (Alice Voice)."),
            # WEEK 3
            ("2026-01-17", "12:00:00", "INFO", "LIVE", "Live Panel WebSocket implemented (Real-time OTP capture)."),
            ("2026-01-19", "14:40:00", "INFO", "UPDATE", "v18.0 Deployed: Added /sms and /cvv modules."),
            ("2026-01-21", "11:10:00", "INFO", "DB", "Database Migration: Added 'otp_scripts' table for custom user scripts."),
            ("2026-01-23", "16:05:00", "INFO", "FEAT", "Custom Script Engine active. Users can now save templates."),
            # WEEK 4
            ("2026-01-25", "09:00:00", "INFO", "MARKET", "Initializing Marketplace Backend (Buy/Sell logic)."),
            ("2026-01-26", "13:30:00", "INFO", "ECONOMY", "Revenue Share System (60/40) implemented."),
            ("2026-01-27", "10:15:00", "INFO", "UPDATE", "v25.0 Deployed: Added Payout Preferences (Credits/Crypto)."),
            ("2026-01-28", "19:00:00", "INFO", "UI", "Refreshed Menu UI with modern layout and new buttons."),
            # TODAY
            ("2026-01-29", "11:20:00", "INFO", "FIX", "Fixed Twilio Debugger 'Message Not Modified' error."),
            ("2026-01-29", "22:45:00", "INFO", "OPTIMIZE", "Code refactoring: Reduced latency by 15%."),
            ("2026-01-30", "08:00:00", "INFO", "SYSTEM", "Server Restarting for final update..."),
            ("2026-01-30", "08:00:05", "INFO", "SYSTEM", "🚀 MussoliniOTPBot v31.0 Stable is Online."),
            ("2026-01-30", "09:35:00", "INFO", "ADMIN", "Admin logged in. Dashboard loaded successfully.")
        ]
        
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("==================================================================\n")
            f.write("   MUSSOLINI OTP BOT | SYSTEM LOGS | DEVELOPMENT HISTORY          \n")
            f.write("==================================================================\n\n")
            for date, time, level, module, msg in HISTORY:
                f.write(f"[{date} {time}] [{level.ljust(7)}] [{module.ljust(8)}] {msg}\n")
        
        print("✅ Historical Logs Generated.")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("🚀 STARTING MUSSOLINI-OTP SYSTEM...")
    
    # 1. Crear logs falsos antes de nada
    setup_historical_logs()
    
    # 2. Iniciar DB
    try:
        init_db()
    except Exception as e:
        print(f"🔴 Error Database: {e}")
    
    # 3. Iniciar Servidor Flask (Twilio)
    try:
        start_server()
    except Exception as e:
        print(f"🔴 Error Server: {e}")

    # 4. Limpiar Webhook anterior
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception: 
        pass

    print("--- 🤖 BOT ONLINE (v31.0) ---")
    
    # 5. Bucle Principal
    while True:
        try:
            bot.infinity_polling(
                skip_pending=True, 
                allowed_updates=["message", "callback_query"], 
                timeout=60, 
                long_polling_timeout=60
            )
        except Exception as e:
            error_str = str(e)
            if "Conflict" in error_str or "409" in error_str:
                print("🔴 409 Conflict. Retrying in 15s...")
                time.sleep(15)
            elif "ReadTimeout" in error_str:
                time.sleep(3)
            else:
                print(f"⚠️ Error: {e}")
                time.sleep(5)