from telebot.types import Message
from config import bot
from database import save_user_script, get_all_user_scripts, delete_user_script, check_subscription

# Supported Languages (Neural TTS)
LANGUAGES = {
    "en": "en-US",    # English (US)
    "es": "es-MX",    # Spanish (Mexico)
    "es-es": "es-ES", # Spanish (Spain)
    "pt": "pt-BR",    # Portuguese (Brazil)
    "fr": "fr-FR",    # French
    "de": "de-DE",    # German
    "it": "it-IT"     # Italian
}

TEMPLATE_MSG = """
📝 **SCRIPT MAKER TEMPLATE**

Create custom scripts with Neural Voices.

**Command:**
`/setscript [service] [lang] [text]`

**Available Languages:**
🇺🇸 `en` (English US)
🇲🇽 `es` (Spanish Latin)
🇪🇸 `es-es` (Spanish Spain)
🇧🇷 `pt` (Portuguese)
🇫🇷 `fr` (French)
🇮🇹 `it` (Italian)

💡 **Example 1 (English):**
`/setscript Amazon en Hello, this is Amazon Security. We blocked a suspicious attempt. Enter the code sent to your mobile.`

💡 **Example 2 (Spanish):**
`/setscript PayPal es Hola, hablamos de PayPal. Ingrese su código de seguridad.`
"""

@bot.message_handler(commands=['template', 'help_scripts'])
def show_template(message):
    bot.reply_to(message, TEMPLATE_MSG, parse_mode="Markdown")

@bot.message_handler(commands=['setscript'])
def set_script(message: Message):
    # 1. Verify Subscription
    if not check_subscription(message.chat.id):
        return bot.reply_to(message, "💎 **Premium Feature:** You need an active plan to create custom scripts.\nUse `/start` -> `Buy Plan`.")

    args = message.text.split(maxsplit=3)
    # args[0]=/setscript, args[1]=service, args[2]=lang, args[3]=text
    
    if len(args) < 4:
        return bot.reply_to(message, "❌ **Error:** Missing arguments.\n\nUse `/template` to see examples.")
    
    service = args[1]
    lang_code = args[2].lower()
    text = args[3]
    
    # Validate Language
    if lang_code not in LANGUAGES:
        return bot.reply_to(message, f"⚠️ **Invalid Language.**\nSupported: `{', '.join(LANGUAGES.keys())}`", parse_mode="Markdown")
    
    twilio_lang = LANGUAGES[lang_code]
    
    if save_user_script(message.chat.id, service, twilio_lang, text):
        bot.reply_to(message, f"✅ **Script Saved Successfully!**\n\n🎯 Service: `{service}`\n🗣️ Voice: `{twilio_lang}`\n📜 Text: _{text}_", parse_mode="Markdown")
    else:
        bot.reply_to(message, "🔴 **Database Error:** Could not save script.")

@bot.message_handler(commands=['myscripts'])
def list_scripts(message):
    # 1. Verify Subscription
    if not check_subscription(message.chat.id):
        return bot.reply_to(message, "💎 **Premium Feature:** You need an active plan.")

    scripts = get_all_user_scripts(message.chat.id)
    if not scripts:
        return bot.reply_to(message, "📭 **No custom scripts found.**\nUse `/template` to create one.")
    
    msg = "📂 **MY CUSTOM SCRIPTS**\n\n"
    for s in scripts:
        # s[0] is service_name, s[1] is language
        msg += f"🔹 **{s[0].capitalize()}** ({s[1]})\n"
    
    msg += "\nTo delete: `/delscript [service]`"
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['delscript'])
def delete_script(message):
    args = message.text.split()
    if len(args) < 2: return bot.reply_to(message, "Usage: `/delscript [service]`")
    
    service = args[1]
    if delete_user_script(message.chat.id, service):
        bot.reply_to(message, f"🗑️ Script for `{service}` deleted. Default script will be used.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Script not found.")
