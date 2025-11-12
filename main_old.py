import os
import threading
import time
from flask import Flask

app = Flask(__name__)

print("🤖 TRADING BOT ATTIVO - ML OTTIMIZZATO")

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
    """Bot ML OTTIMIZZATO - più bilanciato"""
    try:
        # Import qui per evitare errori all'avvio
        import pandas as pd
        import numpy as np
        import requests
        from datetime import datetime
        
        print("🧠 INIZIALIZZAZIONE ML BOT OTTIMIZZATO")
        print("🔧 Soglie: BUY > 0.6, SELL < 0.4 (prima: 0.7/0.3)")
        
        class OptimizedMLTrader:
            def __init__(self):
                self.trade_count = 0
                self.buy_signals = 0
                self.sell_signals = 0
            
            def calculate_advanced_indicators(self, df):
                """Indicatori avanzati e ottimizzati"""
                prices = df['close'].astype(float)
                
                # 1. Media Mobile ottimizzata
                df['sma_10'] = prices.rolling(10).mean()
                df['sma_30'] = prices.rolling(30).mean()
                df['sma_5'] = prices.rolling(5).mean()  # Aggiunta
                
                # 2. RSI migliorato
                def improved_rsi(prices, period=14):
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
                
                df['rsi'] = improved_rsi(prices)
                
                # 3. Momentum avanzato
                df['momentum_5'] = prices.pct_change(5)
                df['momentum_10'] = prices.pct_change(10)
                df['momentum_3'] = prices.pct_change(3)  # Aggiunta
                
                # 4. Volatilità e volume
                df['volatility'] = prices.rolling(20).std()
                if 'volume' in df.columns:
                    df['volume_sma'] = df['volume'].rolling(20).mean()
                    df['volume_ratio'] = df['volume'] / df['volume_sma']
                else:
                    df['volume_ratio'] = 1.0
                
                # 5. Posizione relativa avanzata
                df['price_vs_sma5'] = prices / df['sma_5']
                df['price_vs_sma10'] = prices / df['sma_10']
                df['price_vs_sma30'] = prices / df['sma_30']
                df['sma_ratio_5_10'] = df['sma_5'] / df['sma_10']
                df['sma_ratio_10_30'] = df['sma_10'] / df['sma_30']
                
                return df
            
            def download_historical_data(self, symbol, days=200):
                """Download dati con più history"""
                try:
                    url = "https://api.binance.com/api/v3/klines"
                    params = {
                        "symbol": symbol,
                        "interval": "1d",
                        "limit": min(days, 400)
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
                    print(f"❌ Errore download {symbol}: {e}")
                    return None
            
            def optimized_ml_strategy(self, df):
                """Strategia ML OTTIMIZZATA - più bilanciata"""
                if len(df) < 40:
                    return "HOLD", 0.5
                
                # Features avanzate
                current = df.iloc[-1]
                prices = df['close'].values
                
                # 1. Trend multiplo
                trend_up_short = current['sma_5'] > current['sma_10']
                trend_up_medium = current['sma_10'] > current['sma_30']
                strong_uptrend = trend_up_short and trend_up_medium
                strong_downtrend = not trend_up_short and not trend_up_medium
                
                # 2. RSI conditions avanzate
                rsi_oversold = current['rsi'] < 32  # Più sensibile
                rsi_overbought = current['rsi'] > 68  # Più sensibile
                rsi_neutral = 40 <= current['rsi'] <= 60
                
                # 3. Momentum avanzato
                momentum_very_positive = current['momentum_3'] > 0.02  # 2% in 3 giorni
                momentum_very_negative = current['momentum_3'] < -0.02
                
                # 4. Volatility e volume
                high_volatility = current['volatility'] > np.percentile(df['volatility'].dropna(), 70)
                volume_spike = current['volume_ratio'] > 1.3
                
                # 5. Posizione prezzi
                price_above_all_sma = (current['price_vs_sma5'] > 1 and 
                                      current['price_vs_sma10'] > 1 and 
                                      current['price_vs_sma30'] > 1)
                price_below_all_sma = (current['price_vs_sma5'] < 1 and 
                                      current['price_vs_sma10'] < 1 and 
                                      current['price_vs_sma30'] < 1)
                
                # 🎯 SISTEMA DI SCORING OTTIMIZZATO
                score = 0.5  # Neutral start
                
                # 🔥 BULLISH FACTORS (più aggressivi)
                if strong_uptrend:
                    score += 0.25  # ERA 0.2
                if rsi_oversold and trend_up_short:
                    score += 0.3   # NUOVO: Combo potente
                if rsi_oversold:
                    score += 0.2   # ERA 0.15
                if momentum_very_positive:
                    score += 0.15  # NUOVO
                if volume_spike and trend_up_short:
                    score += 0.2   # NUOVO: Volume + trend
                if price_above_all_sma and rsi_neutral:
                    score += 0.15  # NUOVO: Breakout con RSI ok
                    
                # 🐻 BEARISH FACTORS (più bilanciati)  
                if strong_downtrend:
                    score -= 0.25  # ERA 0.2
                if rsi_overbought and not trend_up_short:
                    score -= 0.3   # NUOVO: Combo potente
                if rsi_overbought:
                    score -= 0.2   # ERA 0.15
                if momentum_very_negative:
                    score -= 0.15  # NUOVO
                if volume_spike and not trend_up_short:
                    score -= 0.2   # NUOVO: Volume + downtrend
                if price_below_all_sma and rsi_neutral:
                    score -= 0.15  # NUOVO: Breakdown con RSI ok
                
                # 🎯 NORMALIZZAZIONE
                score = max(0.1, min(0.9, score))
                
                # 🚀 DECISIONE OTTIMIZZATA
                if score > 0.6:    # OTTIMIZZATO: ERA 0.7 → più BUY
                    return "BUY", score
                elif score < 0.4:  # OTTIMIZZATO: ERA 0.3 → più SELL
                    return "SELL", score
                else:
                    return "HOLD", score
            
            def run_optimized_bot(self):
                """Bot ML ottimizzato"""
                print("🚀 AVVIO ML BOT OTTIMIZZATO")
                print("🎯 Soglie: BUY > 0.6, SELL < 0.4")
                
                while True:
                    try:
                        # Scarica dati
                        df = self.download_historical_data("BTCUSDT", days=200)
                        if df is None or len(df) < 40:
                            print("❌ Dati insufficienti per ML")
                            time.sleep(300)
                            continue
                        
                        # Calcola indicatori avanzati
                        df = self.calculate_advanced_indicators(df)
                        df = df.dropna()
                        
                        if len(df) < 40:
                            continue
                        
                        # Strategia ML ottimizzata
                        signal, confidence = self.optimized_ml_strategy(df)
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        current_price = df.iloc[-1]['close']
                        
                        # Statistiche
                        if signal == "BUY":
                            self.buy_signals += 1
                        elif signal == "SELL":
                            self.sell_signals += 1
                        
                        print(f"⏰ {timestamp} | 🧠 ML: {signal} (score: {confidence:.2f}) | 💰 ${current_price:.2f}")
                        print(f"📊 Stat: BUY={self.buy_signals}, SELL={self.sell_signals}, HOLD={max(0, self.trade_count - self.buy_signals - self.sell_signals)}")
                        
                        # Paper trading per segnali forti
                        if signal in ["BUY", "SELL"] and confidence > 0.65:  # Soglia leggermente più bassa
                            print(f"💡 SEGNALE FORTE: {signal} (score: {confidence:.2f})")
                            print("💰 PAPER TRADE ESEGUITO")
                            self.trade_count += 1
                            print(f"📈 Trade totali ML: {self.trade_count}")
                        
                        # Aspetta 30 minuti
                        time.sleep(1800)
                        
                    except Exception as e:
                        print(f"❌ Errore ML bot: {e}")
                        time.sleep(300)
        
        # Avvia il trader ML ottimizzato
        trader = OptimizedMLTrader()
        trader.run_optimized_bot()
        
    except Exception as e:
        print(f"❌ Errore inizializzazione ML bot: {e}")

@app.route('/')
def home():
    return """
    <h1>🤖 Trading Bot ATTIVO</h1>
    <p>ML OTTIMIZZATO - Soglie: BUY > 0.6, SELL < 0.4</p>
    <p><strong>Modalità:</strong> PAPER TRADING AGGRESSIVO</p>
    <p><a href="/status">Controlla Stato</a></p>
    <p><em>🧠 ML Bot Ottimizzato in esecuzione</em></p>
    """

@app.route('/status')
def status():
    return {
        "status": "🟢 TRADING ATTIVO",
        "mode": "ML OTTIMIZZATO (BUY > 0.6, SELL < 0.4)",
        "symbol": "BTCUSDT",
        "timestamp": time.time(),
        "ml_enabled": True,
        "version": "OTTIMIZZATO"
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
