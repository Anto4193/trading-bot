import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

print("🧠 ML TRADING BOT - VERSIONE SICURA")

class SimpleMLTrader:
    def __init__(self):
        self.model = None
        self.is_trained = False
        
    def calculate_simple_indicators(self, df):
        """Indicatori semplici senza dipendenze complesse"""
        prices = df['close'].astype(float)
        
        # 1. Media Mobile semplice
        df['sma_10'] = prices.rolling(10).mean()
        df['sma_30'] = prices.rolling(30).mean()
        
        # 2. RSI semplificato
        def simple_rsi(prices, period=14):
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
        
        df['rsi'] = simple_rsi(prices)
        
        # 3. Momentum semplice
        df['momentum_5'] = prices.pct_change(5)
        df['momentum_10'] = prices.pct_change(10)
        
        # 4. Volatilità
        df['volatility'] = prices.rolling(20).std()
        
        # 5. Posizione relativa
        df['price_vs_sma10'] = prices / df['sma_10']
        df['price_vs_sma30'] = prices / df['sma_30']
        
        return df
    
    def download_historical_data(self, symbol, days=180):
        """Download dati semplificato"""
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": "1d",
                "limit": min(days, 365)
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
    
    def simple_ml_strategy(self, df):
        """Strategia ML semplificata senza scikit-learn"""
        if len(df) < 40:
            return "HOLD", 0.5
        
        # Features semplici
        current = df.iloc[-1]
        prices = df['close'].values
        
        # 1. Trend (sma10 > sma30 = uptrend)
        trend_up = current['sma_10'] > current['sma_30']
        
        # 2. RSI conditions
        rsi_oversold = current['rsi'] < 35
        rsi_overbought = current['rsi'] > 65
        
        # 3. Momentum
        momentum_positive = current['momentum_5'] > 0
        
        # 4. Volatility adjustment
        high_volatility = current['volatility'] > np.median(df['volatility'].dropna())
        
        # Simple scoring system
        score = 0.5  # Neutral start
        
        # Bullish factors
        if trend_up:
            score += 0.2
        if rsi_oversold:
            score += 0.15
        if momentum_positive:
            score += 0.1
        if not high_volatility:
            score += 0.05
            
        # Bearish factors  
        if not trend_up:
            score -= 0.2
        if rsi_overbought:
            score -= 0.15
        if not momentum_positive:
            score -= 0.1
        if high_volatility:
            score -= 0.05
        
        # Normalize score
        score = max(0.1, min(0.9, score))
        
        # Decision
        if score > 0.7:
            return "BUY", score
        elif score < 0.3:
            return "SELL", score
        else:
            return "HOLD", score
    
    def run_ml_bot(self):
        """Bot ML semplificato"""
        print("🚀 AVVIO ML BOT SEMPLIFICATO")
        
        trade_count = 0
        
        while True:
            try:
                # Scarica dati
                df = self.download_historical_data("BTCUSDT", days=180)
                if df is None or len(df) < 40:
                    print("❌ Dati insufficienti")
                    time.sleep(300)
                    continue
                
                # Calcola indicatori
                df = self.calculate_simple_indicators(df)
                df = df.dropna()
                
                if len(df) < 40:
                    continue
                
                # Strategia ML semplificata
                signal, confidence = self.simple_ml_strategy(df)
                timestamp = datetime.now().strftime('%H:%M:%S')
                current_price = df.iloc[-1]['close']
                
                print(f"⏰ {timestamp} | 🧠 ML: {signal} (score: {confidence:.2f}) | 💰 ${current_price:.2f}")
                
                # Paper trading per segnali forti
                if signal in ["BUY", "SELL"] and confidence > 0.7:
                    print(f"💡 SEGNALE FORTE: {signal} (score: {confidence:.2f})")
                    print("💰 PAPER TRADE ESEGUITO")
                    trade_count += 1
                    print(f"📈 Trade totali ML: {trade_count}")
                
                # Aspetta 30 minuti
                time.sleep(1800)
                
            except Exception as e:
                print(f"❌ Errore ML bot: {e}")
                time.sleep(300)

def start_ml_bot():
    """Avvia il bot ML semplificato"""
    trader = SimpleMLTrader()
    trader.run_ml_bot()

if __name__ == "__main__":
    start_ml_bot()
