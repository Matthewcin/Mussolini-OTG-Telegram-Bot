import psycopg2
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
            
            # 1. Tabla Usuarios
            cur.execute("""
                CREATE TABLE IF NOT EXISTS otp_users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    subscription_end TIMESTAMP DEFAULT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    referred_by BIGINT,
                    wallet_balance DECIMAL(10, 2) DEFAULT 0.00
                );
            """)
            
            # 2. Tabla Licencias
            cur.execute("""
                CREATE TABLE IF NOT EXISTS otp_licenses (
                    key_code TEXT PRIMARY KEY,
                    duration_days INT NOT NULL,
                    status TEXT DEFAULT 'active',
                    used_by BIGINT,
                    credits_amount DECIMAL(10, 2) DEFAULT 0.00,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 3. Tabla Scripts Personales (Lo que usa el usuario)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS otp_scripts (
                    user_id BIGINT,
                    service_name TEXT,
                    language TEXT DEFAULT 'en-US',
                    script_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, service_name)
                );
            """)

            # 4. Tabla Mercado (Scripts en Venta/Gratis)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS otp_market (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    script_text TEXT NOT NULL,
                    language TEXT DEFAULT 'en-US',
                    price DECIMAL(10, 2) DEFAULT 0.00,
                    is_premium BOOLEAN DEFAULT FALSE,
                    author_id BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 5. Tabla Compras (Historial)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS otp_purchases (
                    user_id BIGINT,
                    script_id INT,
                    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, script_id)
                );
            """)
            
            # Migraciones de seguridad
            try:
                cur.execute("ALTER TABLE otp_users ADD COLUMN IF NOT EXISTS wallet_balance DECIMAL(10, 2) DEFAULT 0.00;")
                conn.commit()
            except: conn.rollback()
            
            conn.commit()
            cur.close()
            conn.close()
            print("🟢 Database Connected & Tables Ready.")
        except Exception as e:
            print(f"🔴 Error Initializing DB: {e}")

# ==========================================
# 💰 WALLET FUNCTIONS
# ==========================================

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
        except Exception as e:
            print(f"Deduct Error: {e}")
    return False

# ==========================================
# USER & SUB FUNCTIONS
# ==========================================

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
                cur.execute("""
                    INSERT INTO otp_users (user_id, username, first_name, last_name, referred_by, wallet_balance) 
                    VALUES (%s, %s, %s, %s, %s, 0.00) 
                """, (user.id, user.username, user.first_name, user.last_name, referrer_id))
            else:
                cur.execute("""
                    UPDATE otp_users 
                    SET username=%s, first_name=%s, last_name=%s 
                    WHERE user_id=%s
                """, (user.username, user.first_name, user.last_name, user.id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB Register Error: {e}")
    return is_new_user

def add_subscription_days(user_id, days):
    """Suma días a la suscripción del usuario."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT subscription_end FROM otp_users WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
            current_end = result[0] if result else None
            now = datetime.now()
            
            if current_end and current_end > now:
                new_end = current_end + timedelta(days=days)
            else:
                new_end = now + timedelta(days=days)
            
            cur.execute("UPDATE otp_users SET subscription_end = %s WHERE user_id = %s", (new_end, user_id))
            conn.commit()
            cur.close()
            conn.close()
            return True, new_end
        except: return False, None
    return False, None

def check_subscription(user_id):
    if user_id in ADMIN_IDS: return True
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT subscription_end FROM otp_users WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        if result and result[0]:
            return result[0] > datetime.now()
        return False
    except: return False

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

def get_user_info(user_id):
    """Obtiene toda la info del usuario para el perfil."""
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

# --- SCRIPT FUNCTIONS ---

def save_user_script(user_id, service, lang, text):
    """Guarda o actualiza un script personal."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO otp_scripts (user_id, service_name, language, script_text)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, service_name)
                DO UPDATE SET language=EXCLUDED.language, script_text=EXCLUDED.script_text;
            """, (user_id, service.lower(), lang, text))
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