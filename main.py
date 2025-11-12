import os
import threading
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from flask import Flask

app = Flask(__name__)

print("🤖 TRADING BOT PRO - MULTI-CRYPTO + TRAILING STOP")

# ==================== CONFIGURAZIONE PROFESSIONALE ====================
MONEY_MANAGEMENT = {
    'initial_capital': 50,
    'position_size': 0.02,           # 2% per trade
    'max_daily_trades': 3,           # Max 3 trade/giorno
    'max_daily_loss': 0.02,          # 2% loss giornaliera max
    'max_drawdown': 0.05,            # 5% drawdown totale
    'stop_loss': 0.015,              # 1.5% stop loss
    'take_profit': 0.025,            # 2.5% take profit
    'trailing_stop': 0.03,           # 3% trailing stop
    'trailing_activation': 0.02,     # Si attiva dopo +2% di profitto
    'use_trailing_stop': True,       # Trailing stop attivo
    'risk_reward_ratio': 1.67,       # 1:1.67
    'trading_hours': [8, 22],        # Solo ore attive (8 AM - 10 PM)
    'weekend_trading': False
}

CRYPTO_PORTFOLIO = [
    {"symbol": "BTCUSDT", "weight": 0.3, "allocation": 15},
    {"symbol": "ETHUSDT", "weight": 0.2, "allocation": 10},
    {"symbol": "ADAUSDT", "weight": 0.15, "allocation": 7.5},
    {"symbol": "DOTUSDT", "weight": 0.15, "allocation": 7.5},
    {"symbol": "MATICUSDT", "weight": 0.1, "allocation": 5},
    {"symbol": "AVAXUSDT", "weight": 0.1, "allocation": 5}
]

# ==================== TRADER PROFESSIONALE ====================
class ProfessionalTrader:
    def __init__(self):
        self.paper_balance = MONEY_MANAGEMENT['initial_capital']
        self.daily_trades = 0
        self.daily_pnl = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.open_positions = {}
        self.daily_reset_hour = -1
        
        print("💰 MONEY MANAGEMENT PRO ATTIVO")
        print(f"   • Capitale: {self.paper_balance}€")
        print(f"   • Position Size: {MONEY_MANAGEMENT['position_size']*100}%")
        print(f"   • Stop Loss: {MONEY_MANAGEMENT['stop_loss']*100}%")
        print(f"   • Take Profit: {MONEY_MANAGEMENT['take_profit']*100}%")
        print(f"   • Trailing Stop: {MONEY_MANAGEMENT['trailing_stop']*100}%")
        print(f"   • Max Daily Trades: {MONEY_MANAGEMENT['max_daily_trades']}")
        print("🎯 PORTFOLIO MULTI-CRYPTO:")
        for crypto in CRYPTO_PORTFOLIO:
            print(f"   • {crypto['symbol']}: {crypto['weight']*100}%")
    
    def can_trade(self):
        """Controlla se possiamo fare trading"""
        current_time = datetime.now()
        current_hour = current_time.hour
        
        # Reset daily counters se è un nuovo giorno
        if current_hour != self.daily_reset_hour:
            self.daily_trades = 0
            self.daily_pnl = 0
            self.daily_reset_hour = current_hour
            print("🔄 Reset contatori giornalieri")
            
        # Controllo ore trading
        start_hour, end_hour = MONEY_MANAGEMENT['trading_hours']
        if not (start_hour <= current_hour <= end_hour):
            return False, f"Fuori orario trading ({start_hour}:00-{end_hour}:00)"
            
        # Controllo weekend
        if MONEY_MANAGEMENT['weekend_trading'] == False and current_time.weekday() >= 5:
            return False, "Trading weekend disattivato"
            
        # Controllo daily trades
        if self.daily_trades >= MONEY_MANAGEMENT['max_daily_trades']:
            return False, f"Daily trade limit raggiunto ({self.daily_trades}/{MONEY_MANAGEMENT['max_daily_trades']})"
            
        # Controllo daily loss
        max_daily_loss = MONEY_MANAGEMENT['max_daily_loss'] * MONEY_MANAGEMENT['initial_capital']
        if self.daily_pnl <= -max_daily_loss:
            return False, f"Daily loss limit raggiunto ({self.daily_pnl:.2f}€)"
            
        return True, "OK"
    
    def calculate_position_size(self, symbol):
        """Calcola dimensione posizione basata su peso crypto"""
        crypto_config = next((c for c in CRYPTO_PORTFOLIO if c['symbol'] == symbol), None)
        if crypto_config:
            base_size = self.paper_balance * MONEY_MANAGEMENT['position_size']
            return base_size * crypto_config['weight']
        return self.paper_balance * MONEY_MANAGEMENT['position_size']
    
    def update_trailing_stop(self, symbol, current_price):
        """Aggiorna trailing stop dinamicamente"""
        if symbol in self.open_positions:
            position = self.open_positions[symbol]
            
            # Inizializza max_price se non esiste
            if 'max_price' not in position:
                position['max_price'] = current_price
            else:
                position['max_price'] = max(position['max_price'], current_price)
            
            # Attiva trailing solo dopo profitto minimo
            profit_from_entry = (position['max_price'] - position['entry_price']) / position['entry_price']
            if profit_from_entry >= MONEY_MANAGEMENT['trailing_activation']:
                new_stop = position['max_price'] * (1 - MONEY_MANAGEMENT['trailing_stop'])
                
                # Aggiorna solo se il nuovo stop è più alto del precedente
                if new_stop > position['stop_loss']:
                    position['stop_loss'] = new_stop
                    current_profit = (current_price - position['entry_price']) / position['entry_price'] * 100
                    print(f"🎯 Trailing Stop {symbol} aggiornato: {new_stop:.2f}$ (+{current_profit:.1f}%)")
    
    def check_position_management(self, symbol, current_price):
        """Gestisce stop loss, trailing stop e take profit"""
        if symbol in self.open_positions:
            position = self.open_positions[symbol]
            
            # Aggiorna trailing stop
            if MONEY_MANAGEMENT['use_trailing_stop']:
                self.update_trailing_stop(symbol, current_price)
            
            # STOP LOSS / TRAILING STOP
            if current_price <= position['stop_loss']:
                reason = "TRAILING_STOP" if MONEY_MANAGEMENT['use_trailing_stop'] and position['stop_loss'] > position['entry_price'] * (1 - MONEY_MANAGEMENT['stop_loss']) else "STOP_LOSS"
                self.close_position(symbol, current_price, reason)
                return True
                
            # TAKE PROFIT
            elif current_price >= position['take_profit']:
                self.close_position(symbol, current_price, "TAKE_PROFIT")
                return True
                
        return False
    
    def close_position(self, symbol, current_price, reason):
        """Chiude una posizione"""
        position = self.open_positions[symbol]
        profit_percent = (current_price - position['entry_price']) / position['entry_price']
        profit_amount = position['position_size'] * profit_percent
        
        self.paper_balance += position['position_size'] + profit_amount
        self.daily_pnl += profit_amount
        
        if profit_amount > 0:
            self.winning_trades += 1
            
        # Statistiche dettagliate
        hold_time = (datetime.now() - position['entry_time']).total_seconds() / 3600  # ore
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        print(f"💰 USCITA {reason}: {symbol}")
        print(f"   • Profitto: {profit_percent*100:+.2f}% ({profit_amount:+.2f}€)")
        print(f"   • Durata: {hold_time:.1f}h")
        print(f"   • Daily PnL: {self.daily_pnl:.2f}€")
        print(f"   • Win Rate: {win_rate:.1f}%")
        print(f"   • Balance: {self.paper_balance:.2f}€")
        
        del self.open_positions[symbol]
    
    def execute_paper_trade(self, symbol, signal, price, confidence):
        """Esegue trade con gestione avanzata"""
        can_trade, reason = self.can_trade()
        if not can_trade:
            print(f"⏸️  Trading sospeso: {reason}")
            return False
            
        position_size = self.calculate_position_size(symbol)
        
        if signal == "BUY" and symbol not in self.open_positions:
            # ENTRATA LONG con trailing stop
            self.open_positions[symbol] = {
                'type': 'LONG',
                'entry_price': price,
                'position_size': position_size,
                'stop_loss': price * (1 - MONEY_MANAGEMENT['stop_loss']),
                'take_profit': price * (1 + MONEY_MANAGEMENT['take_profit']),
                'max_price': price,  # Per trailing stop
                'entry_time': datetime.now()
            }
            self.paper_balance -= position_size
            self.daily_trades += 1
            self.total_trades += 1
            
            print(f"💰 ENTRATA LONG: {symbol}")
            print(f"   • Size: {position_size:.2f}€")
            print(f"   • Entry: {price:.2f}$")
            print(f"   • Stop Loss: {self.open_positions[symbol]['stop_loss']:.2f}$")
            print(f"   • Take Profit: {self.open_positions[symbol]['take_profit']:.2f}$")
            if MONEY_MANAGEMENT['use_trailing_stop']:
                print(f"   • Trailing Stop: {MONEY_MANAGEMENT['trailing_stop']*100}% (attivo dopo +{MONEY_MANAGEMENT['trailing_activation']*100}%)")
            print(f"   • Daily Trades: {self.daily_trades}/{MONEY_MANAGEMENT['max_daily_trades']}")
            return True
            
        elif signal == "SELL" and symbol in self.open_positions:
            # USCITA MANUALE
            self.close_position(symbol, price, "MANUAL_EXIT")
            return True
            
        return False

    def monitor_open_positions(self):
        """Monitora le posizioni aperte per stop loss/take profit"""
        for symbol in list(self.open_positions.keys()):
            try:
                # Prendi prezzo corrente
                current_price = get_current_price(symbol)
                if current_price:
                    self.check_position_management(symbol, current_price)
            except Exception as e:
                print(f"❌ Errore monitoraggio {symbol}: {e}")

# ==================== FUNZIONI DI SUPPORTO ====================
def get_current_price(symbol):
    """Ottiene prezzo corrente di una crypto"""
    try:
        url = "https://api.binance.com/api/v3/ticker/price"
        response = requests.get(url, params={"symbol": symbol}, timeout=10)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print(f"❌ Errore prezzo {symbol}: {e}")
        return None

def download_crypto_data(symbol, days=100):
    """Download dati storici crypto"""
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": "1d",
            "limit": min(days, 200)
        }
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if not data:
            return None
            
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        return df.sort_values('timestamp').dropna()
        
    except Exception as e:
        print(f"❌ Download {symbol} failed: {e}")
        return None

def calculate_rsi(prices, period=14):
    """Calcola RSI"""
    deltas = prices.diff()
    gains = deltas.where(deltas > 0, 0)
    losses = -deltas.where(deltas < 0, 0)
    
    avg_gains = gains.rolling(period).mean()
    avg_losses = losses.rolling(period).mean()
    
    # Evita divisione per zero
    avg_losses = avg_losses.where(avg_losses != 0, 0.0001)
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_advanced_indicators(df):
    """Calcola indicatori tecnici avanzati"""
    prices = df['close'].astype(float)
    
    # Medie mobili
    df['sma_10'] = prices.rolling(10).mean()
    df['sma_30'] = prices.rolling(30).mean()
    df['sma_5'] = prices.rolling(5).mean()
    
    # RSI
    df['rsi'] = calculate_rsi(prices)
    
    # Momentum
    df['momentum_5'] = prices.pct_change(5)
    df['momentum_10'] = prices.pct_change(10)
    df['momentum_3'] = prices.pct_change(3)
    
    # Volatilità
    df['volatility'] = prices.rolling(20).std()
    
    # Posizione relativa
    df['price_vs_sma5'] = prices / df['sma_5']
    df['price_vs_sma10'] = prices / df['sma_10']
    df['price_vs_sma30'] = prices / df['sma_30']
    
    return df

def optimized_ml_strategy(df):
    """Strategia ML OTTIMIZZATA - più reattiva"""
    if len(df) < 40:
        return "HOLD", 0.5
        
    current = df.iloc[-1]
    
    # Sistema di scoring ottimizzato
    score = 0.5
    
    # Trend analysis
    trend_up_short = current['sma_5'] > current['sma_10']
    trend_up_medium = current['sma_10'] > current['sma_30']
    strong_uptrend = trend_up_short and trend_up_medium
    strong_downtrend = not trend_up_short and not trend_up_medium
    
    # RSI analysis
    rsi_oversold = current['rsi'] < 35
    rsi_overbought = current['rsi'] > 65
    rsi_neutral = 40 <= current['rsi'] <= 60
    
    # Momentum
    momentum_positive = current['momentum_5'] > 0
    momentum_strong = current['momentum_5'] > 0.02
    
    # Volatilità
    high_volatility = current['volatility'] > np.percentile(df['volatility'].dropna(), 70)
    
    # 🎯 LOGICA MIGLIORATA
    if strong_uptrend and rsi_oversold:
        score += 0.3
    elif strong_uptrend and rsi_neutral and momentum_positive:
        score += 0.2
    elif trend_up_short and rsi_oversold:
        score += 0.15
        
    if strong_downtrend and rsi_overbought:
        score -= 0.3
    elif strong_downtrend and rsi_neutral and not momentum_positive:
        score -= 0.2
    elif not trend_up_short and rsi_overbought:
        score -= 0.15
        
    # Aggiusta per volatilità
    if high_volatility:
        score -= 0.05
        
    score = max(0.1, min(0.9, score))
    
    # 🚀 SOGLIE PIÙ REATTIVE
    if score > 0.55:    # OTTIMIZZATO: era 0.6
        return "BUY", score
    elif score < 0.45:  # OTTIMIZZATO: era 0.4
        return "SELL", score
    else:
        return "HOLD", score

def analyze_crypto(symbol):
    """Analizza una crypto con ML ottimizzato"""
    try:
        # Download dati
        df = download_crypto_data(symbol, days=100)
        if df is None or len(df) < 40:
            return "HOLD", 0.5, 0
            
        # Calcola indicatori
        df = calculate_advanced_indicators(df)
        df = df.dropna()
        
        if len(df) < 40:
            return "HOLD", 0.5, 0
            
        current_price = df.iloc[-1]['close']
        signal, confidence = optimized_ml_strategy(df)
        
        return signal, confidence, current_price
        
    except Exception as e:
        print(f"❌ Errore analisi {symbol}: {e}")
        return "HOLD", 0.5, 0

# ==================== BOT PRINCIPALE ====================
def professional_bot():
    trader = ProfessionalTrader()
    
    print("🧠 AVVIO BOT PRO - MULTI-CRYPTO & TRAILING STOP")
    print("🎯 Soglie ottimizzate: BUY > 0.55, SELL < 0.45")
    
    monitor_count = 0
    
    while True:
        try:
            # Monitora posizioni aperte ogni 5 minuti
            monitor_count += 1
            if monitor_count >= 6:  # Ogni 30 minuti (6 × 5 minuti)
                trader.monitor_open_positions()
                monitor_count = 0
            
            # Analizza ogni crypto nel portfolio
            for crypto in CRYPTO_PORTFOLIO:
                symbol = crypto['symbol']
                
                # Analizza la crypto
                signal, confidence, price = analyze_crypto(symbol)
                
                if signal in ["BUY", "SELL"] and confidence > 0.6:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"⏰ {timestamp} | 🧠 {symbol}: {signal} (score: {confidence:.2f}) | 💰 ${price:.2f}")
                    trader.execute_paper_trade(symbol, signal, price, confidence)
            
            # Monitoraggio prezzo ogni 5 minuti
            time.sleep(300)
            
        except Exception as e:
            print(f"❌ Errore bot principale: {e}")
            time.sleep(60)

# ==================== MONITORAGGIO SEMPLICE ====================
def simple_monitor():
    """Monitoraggio semplice prezzi"""
    while True:
        try:
            for crypto in CRYPTO_PORTFOLIO:
                price = get_current_price(crypto['symbol'])
                if price:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"✅ {crypto['symbol']}: {price:.2f}$ - {timestamp}")
            
            time.sleep(300)  # 5 minuti
            
        except Exception as e:
            print(f"❌ Errore monitoraggio: {e}")
            time.sleep(60)

# ==================== WEB SERVER ====================
@app.route('/')
def home():
    return """
    <h1>🤖 Trading Bot PRO</h1>
    <p>Multi-Crypto + Money Management + Trailing Stop</p>
    <p><strong>Portafoglio:</strong> BTC, ETH, ADA, DOT, MATIC, AVAX</p>
    <p><strong>Risk Management:</strong> 2% per trade, Trailing Stop 3%</p>
    <p><strong>ML Ottimizzato:</strong> Soglie BUY > 0.55, SELL < 0.45</p>
    <p><a href="/status">Status</a></p>
    """

@app.route('/status')
def status():
    return {
        "status": "🟢 TRADING ATTIVO",
        "mode": "MULTI-CRYPTO PRO + TRAILING STOP",
        "portfolio": [crypto['symbol'] for crypto in CRYPTO_PORTFOLIO],
        "money_management": {
            "position_size": f"{MONEY_MANAGEMENT['position_size']*100}%",
            "stop_loss": f"{MONEY_MANAGEMENT['stop_loss']*100}%",
            "trailing_stop": f"{MONEY_MANAGEMENT['trailing_stop']*100}%",
            "max_daily_trades": MONEY_MANAGEMENT['max_daily_trades']
        },
        "timestamp": time.time()
    }

# ==================== AVVIO APPLICAZIONE ====================
if __name__ == "__main__":
    # Avvia bot professionale in background
    pro_bot_thread = threading.Thread(target=professional_bot)
    pro_bot_thread.daemon = True
    pro_bot_thread.start()
    
    # Avvia monitoraggio semplice in background
    monitor_thread = threading.Thread(target=simple_monitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    print("🌐 Server web in avvio...")
    app.run(host='0.0.0.0', port=8000, debug=False)
