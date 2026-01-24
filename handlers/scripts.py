from telebot.types import Message
from config import bot
from database import save_user_script, get_all_user_scripts, delete_user_script, check_subscription

# Lista de idiomas soportados por Twilio (Voces Neurales)
# Esto asegura que la "traducción" tenga acento nativo
LANGUAGES = {
    "en": "en-US",    # Inglés (Alice)
    "es": "es-MX",    # Español Latino (México)
    "es-es": "es-ES", # Español España
    "pt": "pt-BR",    # Portugués Brasil
    "fr": "fr-FR",    # Francés
    "de": "de-DE",    # Alemán
    "it": "it-IT"     # Italiano
}

TEMPLATE_MSG = """
📝 **SCRIPT MAKER TEMPLATE**

Crea scripts con voces nativas (Neural TTS).

**Comando:**
`/setscript [servicio] [idioma] [texto]`

**Idiomas disponibles:**
🇺🇸 `en` (Inglés)
🇲🇽 `es` (Español Latino)
🇪🇸 `es-es` (Español España)
🇧🇷 `pt` (Portugués)
🇫🇷 `fr` (Francés)
🇮🇹 `it` (Italiano)

💡 **Ejemplo 1 (Latinoamérica):**
`/setscript Amazon es Hola, le llamamos de Amazon. Detectamos un cargo extraño de una Laptop. Ingrese el código enviado a su SMS para cancelar la orden.`

💡 **Ejemplo 2 (Brasil):**
`/setscript Nubank pt Olá, aqui é o Nubank. Detectamos uma tentativa de acesso na sua conta.`
"""

@bot.message_handler(commands=['template', 'help_scripts'])
def show_template(message):
    bot.reply_to(message, TEMPLATE_MSG, parse_mode="Markdown")

@bot.message_handler(commands=['setscript'])
def set_script(message: Message):
    # 1. Verificar si es usuario Premium
    if not check_subscription(message.chat.id):
        return bot.reply_to(message, "💎 **Feature Premium:** Necesitas un plan activo para crear scripts personalizados.\nUsa `/start` -> `Buy Plan`.")

    args = message.text.split(maxsplit=3)
    # args[0]=/setscript, args[1]=service, args[2]=lang, args[3]=text
    
    if len(args) < 4:
        return bot.reply_to(message, "❌ **Error:** Faltan datos.\n\nUsa `/template` para ver ejemplos.")
    
    service = args[1]
    lang_code = args[2].lower()
    text = args[3]
    
    # Validar idioma
    if lang_code not in LANGUAGES:
        return bot.reply_to(message, f"⚠️ Idioma no soportado.\nUsa: `{', '.join(LANGUAGES.keys())}`", parse_mode="Markdown")
    
    twilio_lang = LANGUAGES[lang_code]
    
    if save_user_script(message.chat.id, service, twilio_lang, text):
        bot.reply_to(message, f"✅ **Script Guardado Exitosamente!**\n\n🎯 Servicio: `{service}`\n🗣️ Voz: `{twilio_lang}`\n📜 Texto: _{text}_", parse_mode="Markdown")
    else:
        bot.reply_to(message, "🔴 Error de base de datos.")

@bot.message_handler(commands=['myscripts'])
def list_scripts(message):
    # 1. Verificar suscripción
    if not check_subscription(message.chat.id):
        return bot.reply_to(message, "💎 Necesitas un plan activo.")

    scripts = get_all_user_scripts(message.chat.id)
    if not scripts:
        return bot.reply_to(message, "📭 No tienes scripts personalizados.\nUsa `/template` para crear uno.")
    
    msg = "📂 **MY CUSTOM SCRIPTS**\n\n"
    for s in scripts:
        # s[0] es service_name, s[1] es language
        msg += f"🔹 **{s[0].capitalize()}** ({s[1]})\n"
    
    msg += "\nPara borrar: `/delscript [servicio]`"
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['delscript'])
def delete_script(message):
    args = message.text.split()
    if len(args) < 2: return bot.reply_to(message, "Uso: `/delscript [servicio]`")
    
    service = args[1]
    if delete_user_script(message.chat.id, service):
        bot.reply_to(message, f"🗑️ Script de `{service}` eliminado. Se usará el default.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ No se encontró ese script.")
