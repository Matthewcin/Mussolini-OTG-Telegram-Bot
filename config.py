import os
import telebot
from dotenv import load_dotenv

# Cargar .env (solo funciona en local, en Render no hace nada y está bien)
load_dotenv()

# ==========================================
# ⚙️ DIAGNÓSTICO (Esto nos dirá el problema en los logs)
# ==========================================
print("--- INICIANDO CONFIGURACIÓN ---")

# Intentamos obtener el token
API_TOKEN = os.getenv('API_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

# Imprimimos en la consola de Render qué encontró (SIN mostrar el token real por seguridad)
if API_TOKEN is None:
    print("❌ ERROR FATAL: Render dice que 'API_TOKEN' no existe o está vacío.")
else:
    print(f"✅ API_TOKEN encontrado. Longitud: {len(API_TOKEN)} caracteres.")

if DATABASE_URL is None:
    print("❌ ERROR FATAL: Render dice que 'DATABASE_URL' no existe.")
else:
    print("✅ DATABASE_URL encontrado.")

print("--- FIN DIAGNÓSTICO ---")

# ==========================================
# ⚙️ INICIALIZACIÓN
# ==========================================

# Si el token es None, esto fallará aquí, pero ya habremos visto el mensaje de error arriba
if API_TOKEN:
    bot = telebot.TeleBot(API_TOKEN)
else:
    # Esto evita el error "NoneType is not iterable" y muestra un error claro
    raise ValueError("¡Deteniendo bot! Falta la variable de entorno API_TOKEN")
