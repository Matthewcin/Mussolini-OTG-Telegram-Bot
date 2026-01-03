from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is running!"

def run():
    # Render assigns the port via the PORT environment variable. Default is 8080.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def start_server():
    """Starts the web server in a separate thread."""
    t = Thread(target=run)
    t.start()
