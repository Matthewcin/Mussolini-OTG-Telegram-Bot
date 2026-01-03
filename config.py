import os
from telebot import TeleBot
from dotenv import load_dotenv

load_dotenv()

# Variables de Configuración
API_TOKEN = os.getenv('8527602486:AAE1P1COCYidG7oyjMWANvTMfjfVql2wtJc')
DATABASE_URL = os.getenv('postgresql://neondb_owner:npg_1LOXompPCH7U@ep-royal-glitter-acsbyxbr-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require')
ADMIN_IDS = [934491540] # Tu ID o lista de IDs

# Inicializamos el bot aquí para poder importarlo en otros archivos
bot = TeleBot(API_TOKEN)
