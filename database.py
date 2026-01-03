import psycopg2
from config import DATABASE_URL

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
