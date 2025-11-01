import os
import threading
from flask import Flask
from trading_bot import run_bot

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>🤖 Trading Bot ATTIVO</h1>
    <p>Il bot sta monitorando i mercati!</p>
    <p><a href="/status">Controlla Stato</a></p>
    <p><a href="/stop">Ferma Bot</a></p>
    """

@app.route('/status')
def status():
    return {
        "status": "🟢 TRADING ATTIVO",
        "message": "Bot in esecuzione",
        "symbol": "BTCUSDT",
        "mode": "PAPER TRADING"
    }

@app.route('/stop')
def stop():
    return "🛑 Bot fermato (funzione non implementata)"

def start_bot():
    print("🎯 Avvio trading bot in background...")
    run_bot()

if __name__ == "__main__":
    # Avvia il bot in un thread separato
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Avvia il server web
    app.run(host='0.0.0.0', port=8000, debug=False)
