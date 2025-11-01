import os
import threading
import time
from flask import Flask

app = Flask(__name__)

print("🎯 TRADING BOT ATTIVO - MODALITÀ SICURA!")

def simple_bot():
    """Bot semplice che monitora senza API Keys"""
    import requests
    
    while True:
        try:
            # API PUBBLICA - nessuna key needed
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {"symbol": "BTCUSDT"}
            response = requests.get(url, params=params)
            data = response.json()
            price = float(data['price'])
            
            print(f"✅ BTC/USDT: {price:.2f}$ - {time.strftime('%H:%M:%S')}")
            
            # Aspetta 30 secondi
            time.sleep(30)
            
        except Exception as e:
            print(f"❌ Errore: {e}")
            time.sleep(60)

@app.route('/')
def home():
    return """
    <h1>🤖 Trading Bot ATTIVO</h1>
    <p>Monitoraggio Bitcoin in tempo reale</p>
    <p><strong>Modalità:</strong> PAPER TRADING SICURO</p>
    <p><a href="/status">Controlla Stato</a></p>
    """

@app.route('/status')
def status():
    return {
        "status": "🟢 TRADING ATTIVO",
        "message": "Bot in esecuzione",
        "mode": "PAPER TRADING SICURO",
        "symbol": "BTCUSDT",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    # Avvia il bot in background
    bot_thread = threading.Thread(target=simple_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    print("🌐 Server web in avvio...")
    app.run(host='0.0.0.0', port=8000, debug=False)
