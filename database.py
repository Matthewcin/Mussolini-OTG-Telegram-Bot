import psycopg2
from config import DATABASE_URL, ADMIN_IDS # <--- IMPORTAMOS ADMIN_IDS
from datetime import datetime, timedelta

def get_connection():
    """Establishes connection to Neon DB."""
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"🔴 Database Error: {e}")
        return None

def init_db():
    """Initializes tables if they do not exist."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Tabla Usuarios
            cur.execute("""
                CREATE TABLE IF NOT EXISTS otp_users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    subscription_end TIMESTAMP DEFAULT NULL,
                    is_admin BOOLEAN DEFAULT FALSE
                );
            """)
            
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

def register_user(user):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO otp_users (user_id, username, first_name, last_name) 
                VALUES (%s, %s, %s, %s) 
                ON CONFLICT (user_id) 
                DO UPDATE SET username=EXCLUDED.username, first_name=EXCLUDED.first_name, last_name=EXCLUDED.last_name;
            """, (user.id, user.username, user.first_name, user.last_name))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Registration Error: {e}")

def add_subscription_days(user_id, days):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            cur.execute("SELECT subscription_end FROM otp_users WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
            
            current_end = result[0] if result else None
            now = datetime.now()
            
            # Si ya tenía tiempo, sumamos. Si no, empezamos desde ahora.
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

# ==========================================
# 🔍 FUNCIÓN CORREGIDA (Check Subscription)
# ==========================================
def check_subscription(user_id):
    """
    Verifica si el usuario tiene acceso.
    1. Si es ADMIN -> TRUE (Siempre pasa)
    2. Si es USUARIO -> Revisa fecha en DB
    """
    
    # 1. ADMIN BYPASS (Tú eres el dueño, no necesitas pagar)
    if user_id in ADMIN_IDS:
        print(f"🛡️ Admin Bypass activado para {user_id}")
        return True

    conn = get_connection()
    if not conn: return False
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT subscription_end FROM otp_users WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result and result[0]:
            expiration = result[0]
            now = datetime.now()
            
            # Debug en consola para ver por qué falla
            is_active = expiration > now
            if not is_active:
                print(f"⛔ User {user_id} expired. Exp: {expiration} vs Now: {now}")
            
            return is_active
            
        print(f"⛔ User {user_id} has no subscription data.")
        return False
        
    except Exception as e:
        print(f"Error checking sub: {e}")
        return False

# --- FUNCIONES DE SCRIPTS (Mantenlas igual) ---
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
        except Exception as e:
            print(f"Error saving script: {e}")
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
        except Exception as e:
            print(f"Error fetching script: {e}")
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
        except Exception as e:
            print(f"Error listing scripts: {e}")
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
        except Exception as e:
            print(f"Error deleting script: {e}")
    return False
