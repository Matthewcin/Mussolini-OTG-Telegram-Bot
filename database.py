import psycopg2
import uuid
from config import DATABASE_URL, ADMIN_IDS
from datetime import datetime, timedelta

def get_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"🔴 Database Error: {e}")
        return None

def init_db():
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # 1. Users
            cur.execute("""CREATE TABLE IF NOT EXISTS otp_users (user_id BIGINT PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, subscription_end TIMESTAMP DEFAULT NULL, is_admin BOOLEAN DEFAULT FALSE, referred_by BIGINT, wallet_balance DECIMAL(10, 2) DEFAULT 0.00);""")
            # 2. Licenses
            cur.execute("""CREATE TABLE IF NOT EXISTS otp_licenses (key_code TEXT PRIMARY KEY, duration_days INT NOT NULL, status TEXT DEFAULT 'active', used_by BIGINT, credits_amount DECIMAL(10, 2) DEFAULT 0.00, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""")
            # 3. Scripts
            cur.execute("""CREATE TABLE IF NOT EXISTS otp_scripts (user_id BIGINT, service_name TEXT, language TEXT DEFAULT 'en-US', script_text TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (user_id, service_name));""")
            # 4. Market
            cur.execute("""CREATE TABLE IF NOT EXISTS otp_market (id SERIAL PRIMARY KEY, title TEXT NOT NULL, service_name TEXT NOT NULL, script_text TEXT NOT NULL, language TEXT DEFAULT 'en-US', price DECIMAL(10, 2) DEFAULT 0.00, is_premium BOOLEAN DEFAULT FALSE, author_id BIGINT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, payout_pref TEXT DEFAULT 'credits', payout_wallet TEXT DEFAULT NULL);""")
            # 5. Purchases
            cur.execute("""CREATE TABLE IF NOT EXISTS otp_purchases (user_id BIGINT, script_id INT, purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (user_id, script_id));""")
            # 6. Plans
            cur.execute("""CREATE TABLE IF NOT EXISTS otp_plans (id SERIAL PRIMARY KEY, price DECIMAL(10, 2) NOT NULL UNIQUE, reward_balance DECIMAL(10, 2) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""")
            
            # 7. BOT SETTINGS (NUEVO)
            # Guarda config global: maintenance_mode, maintenance_msg, changelog_text
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bot_settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT
                );
            """)

            # Default Plans Logic
            cur.execute("SELECT COUNT(*) FROM otp_plans")
            if cur.fetchone()[0] == 0:
                cur.execute("INSERT INTO otp_plans (price, reward_balance) VALUES (10.00, 10.00), (25.00, 30.00), (50.00, 65.00)")
            
            conn.commit()
            cur.close()
            conn.close()
            print("🟢 Database Connected & Tables Ready.")
        except Exception as e:
            print(f"🔴 Init DB Error: {e}")

# ... (MANTÉN TUS FUNCIONES ANTIGUAS: get_user_balance, register_user, etc.) ...
# ... (POR BREVEDAD, ASUMO QUE ESTÁN AQUÍ. NO LAS BORRES) ...
# ... (Solo agrego las NUEVAS funciones abajo) ...

def get_user_balance(user_id):
    if user_id in ADMIN_IDS: return 9999.00
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT wallet_balance FROM otp_users WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
            conn.close()
            return float(result[0]) if result else 0.00
        except: pass
    return 0.00

def add_balance(user_id, amount):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("UPDATE otp_users SET wallet_balance = wallet_balance + %s WHERE user_id = %s", (amount, user_id))
            conn.commit()
            conn.close()
            return True
        except: pass
    return False

def deduct_balance(user_id, cost):
    if user_id in ADMIN_IDS: return True
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT wallet_balance FROM otp_users WHERE user_id = %s", (user_id,))
            res = cur.fetchone()
            current = float(res[0]) if res else 0.00
            if current >= cost:
                new_bal = current - cost
                cur.execute("UPDATE otp_users SET wallet_balance = %s WHERE user_id = %s", (new_bal, user_id))
                conn.commit()
                conn.close()
                return True
            else:
                conn.close()
                return False
        except: pass
    return False

def register_user(user, referrer_id=None):
    conn = get_connection()
    is_new_user = False
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM otp_users WHERE user_id = %s", (user.id,))
            exists = cur.fetchone()
            if not exists:
                is_new_user = True
                cur.execute("INSERT INTO otp_users (user_id, username, first_name, last_name, referred_by, wallet_balance) VALUES (%s, %s, %s, %s, %s, 0.00)", (user.id, user.username, user.first_name, user.last_name, referrer_id))
            else:
                cur.execute("UPDATE otp_users SET username=%s, first_name=%s, last_name=%s WHERE user_id=%s", (user.username, user.first_name, user.last_name, user.id))
            conn.commit()
            conn.close()
        except: pass
    return is_new_user

def check_subscription(user_id):
    if user_id in ADMIN_IDS: return True
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT subscription_end FROM otp_users WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        conn.close()
        if result and result[0]: return result[0] > datetime.now()
        return False
    except: return False

def add_subscription_days(user_id, days):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT subscription_end FROM otp_users WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
            current_end = result[0] if result else None
            now = datetime.now()
            if current_end and current_end > now: new_end = current_end + timedelta(days=days)
            else: new_end = now + timedelta(days=days)
            cur.execute("UPDATE otp_users SET subscription_end = %s WHERE user_id = %s", (new_end, user_id))
            conn.commit()
            conn.close()
            return True, new_end
        except: return False, None
    return False, None

def get_user_info(user_id):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT subscription_end, joined_at, referred_by, wallet_balance FROM otp_users WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
            conn.close()
            return result 
        except: pass
    return None

def get_referral_count(user_id):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM otp_users WHERE referred_by = %s", (user_id,))
            result = cur.fetchone()
            conn.close()
            return result[0] if result else 0
        except: pass
    return 0

def get_available_services(user_id):
    conn = get_connection()
    services = []
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT service_name FROM otp_scripts WHERE user_id = %s", (user_id,))
            my_scripts = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT service_name FROM otp_market WHERE price = 0 OR is_premium = FALSE")
            free_scripts = [row[0] for row in cur.fetchall()]
            defaults = ["Amazon", "PayPal", "WhatsApp", "Google", "Facebook", "Apple", "BankOfAmerica", "Chase", "Instagram", "Uber"]
            all_services = set([s.capitalize() for s in my_scripts + free_scripts + defaults])
            services = sorted(list(all_services))
            conn.close()
        except: pass
    return services

def get_market_script_by_name(service_name):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, title, price, is_premium, script_text, service_name, language FROM otp_market WHERE service_name ILIKE %s ORDER BY price ASC LIMIT 1", (service_name,))
            result = cur.fetchone()
            conn.close()
            return result
        except: pass
    return None

def save_user_script(user_id, service, lang, text):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO otp_scripts (user_id, service_name, language, script_text) VALUES (%s, %s, %s, %s) ON CONFLICT (user_id, service_name) DO UPDATE SET language=EXCLUDED.language, script_text=EXCLUDED.script_text;", (user_id, service.lower(), lang, text))
            conn.commit()
            conn.close()
            return True
        except: pass
    return False

def get_user_script(user_id, service):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT script_text, language FROM otp_scripts WHERE user_id = %s AND service_name = %s", (user_id, service.lower()))
            result = cur.fetchone()
            conn.close()
            return result 
        except: pass
    return None

def get_all_user_scripts(user_id):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT service_name, language FROM otp_scripts WHERE user_id = %s", (user_id,))
            results = cur.fetchall()
            conn.close()
            return results
        except: pass
    return []

def delete_user_script(user_id, service):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM otp_scripts WHERE user_id = %s AND service_name = %s", (user_id, service.lower()))
            conn.commit()
            conn.close()
            return True
        except: pass
    return False

def manage_plan(action, price, reward=0):
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        if action == "add":
            cur.execute("INSERT INTO otp_plans (price, reward_balance) VALUES (%s, %s) ON CONFLICT (price) DO UPDATE SET reward_balance = EXCLUDED.reward_balance", (price, reward))
        elif action == "del":
            cur.execute("DELETE FROM otp_plans WHERE price = %s", (price,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Plan DB Error: {e}")
        return False

def get_all_plans():
    conn = get_connection()
    plans = []
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, price, reward_balance FROM otp_plans ORDER BY price ASC")
            plans = cur.fetchall()
            conn.close()
        except: pass
    return plans

def get_plan_by_id(plan_id):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT price, reward_balance FROM otp_plans WHERE id = %s", (plan_id,))
            result = cur.fetchone()
            conn.close()
            return result
        except: pass
    return None

def create_license(days):
    key_code = "KEY-" + str(uuid.uuid4())[:8].upper()
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO otp_licenses (key_code, duration_days, status) VALUES (%s, %s, 'active')", (key_code, days))
            conn.commit()
            conn.close()
            return key_code
        except Exception as e:
            print(f"Key Gen Error: {e}")
    return None

# ==========================================
# 🆕 SETTINGS & BROADCAST FUNCTIONS
# ==========================================
def get_setting(key):
    conn = get_connection()
    val = None
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT setting_value FROM bot_settings WHERE setting_key = %s", (key,))
            res = cur.fetchone()
            val = res[0] if res else None
            conn.close()
        except: pass
    return val

def set_setting(key, value):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO bot_settings (setting_key, setting_value) VALUES (%s, %s) ON CONFLICT (setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value", (key, value))
            conn.commit()
            conn.close()
            return True
        except: pass
    return False

def get_all_users_ids():
    conn = get_connection()
    ids = []
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM otp_users")
            ids = [r[0] for r in cur.fetchall()]
            conn.close()
        except: pass
    return ids