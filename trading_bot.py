import os
import time
import requests
import json
from datetime import datetime

# Configurazione
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
SYMBOL = "BTCUSDT"
INVESTIMENTO = 10  # 10€ per trade

print("🎯 TRADING BOT ATTIVO!")

def get_btc_price():
    """Prendi il prezzo corrente di BTC"""
    try:
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": SYMBOL}
        response = requests.get(url, params=params)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print(f"❌ Errore prezzo: {e}")
        return None

def simple_strategy(current_price, previous_prices):
    """Strategia semplice: compra se scende, vendi se sale"""
    if len(previous_prices) < 2:
        return "HOLD"
    
    price_change = current_price - previous_prices[-2]
    change_percent = (price_change / previous_prices[-2]) * 100
    
    if change_percent < -1:  # Se scende dell'1%
        return "BUY"
    elif change_percent > 1:  # Se sale dell'1%
        return "SELL"
    else:
        return "HOLD"

def paper_trade(action, price):
    """Simula un trade (SICUREZZA!)"""
    print(f"📊 {action} segnale a {price:.2f}€")
    print(f"💸 Trade simulato: {action} {INVESTIMENTO}€ di {SYMBOL}")
    print("🔒 MODALITÀ PAPER TRADING - Nessun ordine reale!")
    return True

def run_bot():
    """Loop principale del bot"""
    prices = []
    
    while True:
        try:
            # 1. Prendi il prezzo
            current_price = get_btc_price()
            if current_price:
                prices.append(current_price)
                print(f"⏰ {datetime.now().strftime('%H:%M:%S')} | 💰 {SYMBOL}: {current_price:.2f}€")
                
                # 2. Strategia
                if len(prices) >= 5:  # Aspetta 5 dati
                    action = simple_strategy(current_price, prices)
                    
                    # 3. Esegui (paper trading)
                    if action in ["BUY", "SELL"]:
                        paper_trade(action, current_price)
            
            # Mantieni solo ultimi 10 prezzi
            if len(prices) > 10:
                prices = prices[-10:]
                
            # Aspetta 30 secondi
            time.sleep(30)
            
        except Exception as e:
            print(f"❌ Errore bot: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
