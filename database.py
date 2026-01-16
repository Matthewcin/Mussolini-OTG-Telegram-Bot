import psycopg2
from config import DATABASE_URL
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
            
            # Users Table
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
            
            # Licenses Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS otp_licenses (
                    key_code TEXT PRIMARY KEY,
                    duration_days INT NOT NULL,
                    status TEXT DEFAULT 'active', -- Options: active, used
                    used_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            print("🟢 Database connected and tables ready.")
        except Exception as e:
            print(f"🔴 Error Initializing DB: {e}")

def register_user(user):
    """Registers or updates a user in the database."""
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

# ESTA ES LA FUNCIÓN QUE FALTABA Y CAUSABA EL ERROR
def add_subscription_days(user_id, days):
    """Adds subscription time to a user (used by Payments & Keys)."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # 1. Check current subscription status
            cur.execute("SELECT subscription_end FROM otp_users WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
            
            current_end = result[0] if result else None
            now = datetime.now()
            
            # 2. Calculate new end date
            if current_end and current_end > now:
                # User has active time, add to existing
                new_end = current_end + timedelta(days=days)
            else:
                # User is expired or new, start from NOW
                new_end = now + timedelta(days=days)
            
            # 3. Update DB
            cur.execute("UPDATE otp_users SET subscription_end = %s WHERE user_id = %s", (new_end, user_id))
            conn.commit()
            cur.close()
            conn.close()
            return True, new_end
        except Exception as e:
            print(f"Subscription Update Error: {e}")
            return False, None
    return False, None
