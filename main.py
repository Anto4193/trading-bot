import os
print("=== INIZIO BOT ===")
print("1. Import os check:", "os" in globals())

import time
from flask import Flask

print("2. Tutti gli import completati")

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Trading Bot FUNZIONANTE! ✅"

@app.route('/status')
def status():
    return {
        "status": "🟢 ONLINE", 
        "timestamp": time.time(),
        "api_keys": "presenti" if os.getenv('BINANCE_API_KEY') else "non presenti"
    }

if __name__ == "__main__":
    print("3. Server in avvio...")
    app.run(host='0.0.0.0', port=8000, debug=False)
