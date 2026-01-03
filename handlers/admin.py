import secrets
from telebot.types import Message
from config import bot, ADMIN_IDS
from database import get_connection

# ==========================================
# 🛠️ SYSTEM COMMANDS
# ==========================================

@bot.message_handler(commands=['version'])
def cmd_version(message: Message):
    """
    Shows the current bot version and system status.
    """
    if message.from_user.id not in ADMIN_IDS:
        return # Ignore non-admins

    text = (
        "**SYSTEM VERSION INFO**\n"
        "━━━━━━━━━━━━━━━━\n"
        "⚙️ **Build:** `v1.2.0 (Stable)`\n"
        "📅 **Last Update:** Jan 2, 2026 // 1:40 GMT-3 (Argentina Time Zone)\n"
        "☁️ **Server:** Render Cloud (Linux CMD Prompt Based)\n"
        "🗄 **Database:** Neon Console (PostgreSQL 16 Based)\n"
        "🐍 **Python:** 3.11+\n"
        "🔐 **Security:** SSL Mode Required\n"
        "━━━━━━━━━━━━━━━━\n"
        "🗣️ **Note:** Nothing to Say atm :D"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['log'])
def cmd_log(message: Message):
    """
    Displays the development changelog (Dec 31 - Jan 2).
    """
    if message.from_user.id not in ADMIN_IDS:
        return # Ignore non-admins

    log_text = """
📜 **DEVELOPMENT ACTIVITY LOG**
*Period: Dec 31, 2025 - Jan 2, 2026*

━━━━━━━━━━━━━━━━━━━━━━━━

🗓 **December 31: Architecture & Planning**
• **Core System Design:** Analyzed `BIGFATOTP` requirements and defined the SaaS architecture.
• **Security Protocols:** Designed the License Key validation system logic to prevent unauthorized access.
• **Database Schema:** Drafted the Entity-Relationship model for `Users` and `Licenses` to ensure scalability.
• **API Research:** Evaluated VoIP providers and defined Webhook endpoints for future call routing.

🗓 **January 1: Backend & Database Implementation**
• **Neon DB Integration:** Successfully connected the Python backend to PostgreSQL (Neon Tech) using persistent connection pooling.
•  **Table Migration:** Executed SQL scripts to create `otp_users` and `otp_licenses` with `ON CONFLICT` constraints for data integrity.
• **Environment Security:** Implemented `.env` variable handling to protect API Keys and Database Credentials from leaks.
• **User Management:** Coded the `register_user` logic to automatically track new users and admin privileges.

🗓 **January 2: UI/UX, Refactoring & Deployment**
• **Cloud Deployment:** Configured **Render** environment. Solved complex `NoneType` environment variable errors and successfully deployed the build.
• **Modular Refactoring:** Rewrote the entire codebase into a Professional Modular Structure (`handlers/`, `config.py`, `database.py`) for enterprise-level maintainability.
• **GUI & UX Design:** Implemented the "Premium" menu interface with Inline Buttons (Status, Buy, Enter Key).
• **Keep-Alive Server:** Engineered a Flask micro-server to bypass Render's port binding limitations, ensuring 99.9% Uptime.
• **License Logic:** Finalized the `Redeem Key` algorithm with date calculation and automatic subscription activation.

━━━━━━━━━━━━━━━━━━━━━━━━
🟢 **TOTAL STATUS:** CORE SYSTEM DEPLOYED & LIVE.
    """
    bot.reply_to(message, log_text, parse_mode="Markdown")

# ==========================================
# KEY GENERATION
# ==========================================

@bot.message_handler(commands=['create'])
def create_key(message: Message):
    """
    Creates a new license key.
    Usage: /create [days]
    """
    if message.from_user.id not in ADMIN_IDS:
        return 
        
    try:
        days = int(message.text.split()[1])
        new_key = f"KEY-{secrets.token_hex(4).upper()}"
        
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO otp_licenses (key_code, duration_days) VALUES (%s, %s)", (new_key, days))
            conn.commit()
            conn.close()
            bot.reply_to(message, f"🟢 **Key Created Successfully**\n\n🔢 Code: `{new_key}`\n⏳ Duration: {days} days", parse_mode="Markdown")
    except IndexError:
        bot.reply_to(message, "🟠 **Usage Error:**\nPlease specify days.\nExample: `/create 30`")
    except Exception as e:
        bot.reply_to(message, f"🔴 Error: {e}")
