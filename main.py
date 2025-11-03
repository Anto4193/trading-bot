import os
import threading
import time
from flask import Flask

app = Flask(__name__)

print("🤖 TRADING BOT ATTIVO - MODALITÀ IBIRIDA")

def simple_bot():
    """Bot semplice di monitoraggio"""
    import requests
    
    while True:
        try:
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {"symbol": "BTCUSDT"}
            response = requests.get(url, params=params)
            data = response.json()
            price = float(data['price'])
            
            print(f"✅ BTC/USDT: {price:.2f}$ - {time.strftime('%H:%M:%S')}")
            
            time.sleep(300)  # 5 minuti
            
        except Exception as e:
            print(f"❌ Errore monitoraggio: {e}")
            time.sleep(60)

def ml_bot():
    """Bot ML avanzato"""
    try:
        from ml_trading import ml_trading_bot
        ml_trading_bot()
    except Exception as e:
        print(f"❌ Errore ML bot: {e}")

@app.route('/')
def home():
    return """
    <h1>🤖 Trading Bot ATTIVO</h1>
    <p>Monitoraggio + Machine Learning</p>
    <p><strong>Modalità:</strong> PAPER TRADING IBIRIDO</p>
    <p><a href="/status">Controlla Stato</a></p>
    <p><em>🧠 ML Bot in esecuzione</em></p>
    """

@app.route('/status')
def status():
    return {
        "status": "🟢 TRADING ATTIVO",
        "mode": "IBIRIDO (Monitoraggio + ML)",
        "symbol": "BTCUSDT",
        "timestamp": time.time(),
        "ml_enabled": True
    }

if __name__ == "__main__":
    # Avvia bot semplice in background
    simple_thread = threading.Thread(target=simple_bot)
    simple_thread.daemon = True
    simple_thread.start()
    
    # Avvia bot ML in background
    ml_thread = threading.Thread(target=ml_bot)
    ml_thread.daemon = True
    ml_thread.start()
    
    print("🌐 Server web in avvio...")
    app.run(host='0.0.0.0', port=8000, debug=False)
