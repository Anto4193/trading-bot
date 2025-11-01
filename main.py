import os
import time
import pandas as pd
from binance.client import Client
from flask import Flask

# Creiamo l'app Flask per Railway
app = Flask(__name__)

print("🤖 AVVIO TRADING BOT...")
print("🔐 Controllo API Keys...")

# Controlliamo se le API Keys sono presenti
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

if not api_key or not api_secret:
    print("❌ API Keys non trovate!")
    print("⚠️  Ricorda di impostarle su Railway")
else:
    print("✅ API Keys trovate!")
    
    # Inizializza il client Binance (SOLO LETTURA per ora)
    try:
        client = Client(api_key, api_secret)
        account = client.get_account()
        print(f"✅ Connesso a Binance!")
        print(f"💰 Saldo disponibile: ")
        
        # Mostra i saldi
        for balance in account['balances']:
            if float(balance['free']) > 0:
                print(f"   {balance['asset']}: {balance['free']}")
                
    except Exception as e:
        print(f"❌ Errore connessione: {e}")

@app.route('/')
def home():
    return """
    <h1>🤖 Trading Bot Funzionante!</h1>
    <p>Il bot è online e funziona correttamente!</p>
    <p><a href="/status">Controlla Stato</a></p>
    """

@app.route('/status')
def status():
    return {
        "status": "🟢 ONLINE",
        "message": "Bot in esecuzione",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    print("🌐 Server in avvio...")
    app.run(host='0.0.0.0', port=8000, debug=False)
