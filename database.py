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
            
            # Tabla Usuarios (Con columna referral)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS otp_users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    subscription_end TIMESTAMP DEFAULT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    referred_by BIGINT
                );
            """)
            
            # MIGRACIÓN AUTOMÁTICA (Por si la tabla ya existía sin la columna)
            try:
                cur.execute("ALTER TABLE otp_users ADD COLUMN IF NOT EXISTS referred_by BIGINT;")
                conn.commit()
            except:
                conn.rollback()

            # Tabla Licencias
            cur.execute("""
                CREATE TABLE IF NOT EXISTS otp_licenses (
                    key_code TEXT PRIMARY KEY,
                    duration_days INT NOT NULL,
                    status TEXT DEFAULT 'active',
                    used_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Tabla Scripts
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
            
            conn.commit()
            cur.close()
            conn.close()
            print("🟢 Database connected and tables ready.")
        except Exception as e:
            print(f"🔴 Error Initializing DB: {e}")

# --- USER FUNCTIONS ---

def register_user(user, referrer_id=None):
    """Registers user and tracks who invited them."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Primero intentamos insertar
            cur.execute("""
                INSERT INTO otp_users (user_id, username, first_name, last_name, referred_by) 
                VALUES (%s, %s, %s, %s, %s) 
                ON CONFLICT (user_id) 
                DO UPDATE SET username=EXCLUDED.username, first_name=EXCLUDED.first_name, last_name=EXCLUDED.last_name;
            """, (user.id, user.username, user.first_name, user.last_name, referrer_id))
            
            # Si ya existía, NO actualizamos el referrer (solo cuenta el primero)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Registration Error: {e}")

def get_user_info(user_id):
    """Obtiene toda la info del perfil."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT subscription_end, joined_at, referred_by FROM otp_users WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
            conn.close()
            return result # (sub_end, joined_at, referred_by)
        except Exception as e:
            print(f"Error fetching profile: {e}")
    return None

def get_referral_count(user_id):
    """Cuenta cuántas personas ha invitado este usuario."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM otp_users WHERE referred_by = %s", (user_id,))
            result = cur.fetchone()
            conn.close()
            return result[0] if result else 0
        except Exception as e:
            print(f"Error counting referrals: {e}")
    return 0

def add_subscription_days(user_id, days):
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
        except Exception as e:
            print(f"Subscription Update Error: {e}")
            return False, None
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
    except Exception:
        return False

# --- SCRIPT FUNCTIONS (Se mantienen igual) ---
def save_user_script(user_id, service, lang, text):
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
