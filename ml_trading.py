import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import time

print("🧠 TRADING BOT CON MACHINE LEARNING")

class MLTrader:
    def __init__(self):
        self.model = None
        self.is_trained = False
        
    def calculate_technical_indicators(self, df):
        """Calcola indicatori tecnici per features ML"""
        # Prezzi
        prices = df['close'].astype(float)
        
        # 1. Media Mobile 5 e 20 periodi
        df['sma_5'] = prices.rolling(5).mean()
        df['sma_20'] = prices.rolling(20).mean()
        
        # 2. RSI
        def compute_rsi(prices, period=14):
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gains = pd.Series(gains).rolling(period).mean()
            avg_losses = pd.Series(losses).rolling(period).mean()
            
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        df['rsi'] = compute_rsi(prices)
        
        # 3. MACD
        exp12 = prices.ewm(span=12).mean()
        exp26 = prices.ewm(span=26).mean()
        df['macd'] = exp12 - exp26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        # 4. Bollinger Bands
        df['bb_middle'] = prices.rolling(20).mean()
        bb_std = prices.rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (prices - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # 5. Volume (se disponibile)
        if 'volume' in df.columns:
            df['volume_sma'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
        else:
            df['volume_ratio'] = 1.0
        
        # 6. Momentum
        df['momentum_1'] = prices.pct_change(1)
        df['momentum_5'] = prices.pct_change(5)
        df['momentum_20'] = prices.pct_change(20)
        
        return df
    
    def create_features_target(self, df):
        """Crea features (X) e target (y) per il ML"""
        # Features tecniche
        features = [
            'rsi', 'macd', 'bb_position', 'volume_ratio',
            'momentum_1', 'momentum_5', 'momentum_20'
        ]
        
        # Aggiungi rapporti tra medie mobili
        df['sma_ratio_5_20'] = df['sma_5'] / df['sma_20']
        df['price_vs_sma5'] = df['close'] / df['sma_5']
        df['price_vs_sma20'] = df['close'] / df['sma_20']
        
        features.extend(['sma_ratio_5_20', 'price_vs_sma5', 'price_vs_sma20'])
        
        # Target: Prezzo sale (1) o scende (0) nei prossimi N giorni?
        future_days = 3  # Predizione per 3 giorni nel futuro
        df['future_price'] = df['close'].shift(-future_days)
        df['price_change'] = (df['future_price'] - df['close']) / df['close']
        
        # Classificazione: 1 se sale >1%, 0 se scende >-1%, 2 se stabile
        df['target'] = 2  # HOLD
        df.loc[df['price_change'] > 0.01, 'target'] = 1   # BUY
        df.loc[df['price_change'] < -0.01, 'target'] = 0  # SELL
        
        # Rimuovi righe con NaN
        df_clean = df.dropna()
        
        X = df_clean[features]
        y = df_clean['target']
        
        return X, y, df_clean
    
    def train_model(self, symbol="BTCUSDT", years=2):
        """Addestra il modello ML su dati storici"""
        print(f"📚 Addestramento modello su {symbol} ({years} anni)...")
        
        # Scarica dati
        df = self.download_historical_data(symbol, years)
        if df is None:
            print("❌ Errore download dati")
            return False
        
        # Calcola indicatori
        df = self.calculate_technical_indicators(df)
        
        # Crea features e target
        X, y, df_clean = self.create_features_target(df)
        
        if len(X) < 100:
            print("❌ Dati insufficienti per training")
            return False
        
        # Split training/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )
        
        # Addestra Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            min_samples_split=20
        )
        
        self.model.fit(X_train, y_train)
        
        # Valuta il modello
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Modello addestrato!")
        print(f"   📊 Accuracy: {accuracy:.2%}")
        print(f"   📈 Sample size: {len(X)} giorni")
        print(f"   🎯 Distribuzione target: {pd.Series(y).value_counts().to_dict()}")
        
        self.is_trained = True
        return True
    
    def download_historical_data(self, symbol, years=2):
        """Scarica dati storici (versione semplificata)"""
        try:
            # Per velocità, usiamo meno dati
            url = "https://api.binance.com/api/v3/klines"
            days = years * 365
            limit = min(days, 500)  # Massimo 500 punti
            
            params = {
                "symbol": symbol,
                "interval": "1d",
                "limit": limit
            }
            
            response = requests.get(url, params=params, timeout=10)
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
            
            return df.sort_values('timestamp')
            
        except Exception as e:
            print(f"❌ Errore download: {e}")
            return None
    
    def predict_signal(self, current_features):
        """Predice segnale di trading"""
        if not self.is_trained or self.model is None:
            return "HOLD", 0.0
        
        try:
            prediction = self.model.predict([current_features])[0]
            probabilities = self.model.predict_proba([current_features])[0]
            confidence = np.max(probabilities)
            
            signal_map = {0: "SELL", 1: "BUY", 2: "HOLD"}
            return signal_map[prediction], confidence
            
        except Exception as e:
            print(f"❌ Errore predizione: {e}")
            return "HOLD", 0.0
    
    def get_current_features(self, symbol="BTCUSDT"):
        """Ottiene features correnti per predizione"""
        try:
            # Scarica ultimi 50 giorni per calcolare indicatori
            df = self.download_historical_data(symbol, years=0.2)  # ~70 giorni
            if df is None:
                return None
            
            df = self.calculate_technical_indicators(df)
            
            # Prendi l'ultima riga (oggi)
            last_row = df.iloc[-1]
            
            features = [
                last_row['rsi'], last_row['macd'], last_row['bb_position'], last_row['volume_ratio'],
                last_row['momentum_1'], last_row['momentum_5'], last_row['momentum_20'],
                last_row['sma_ratio_5_20'], last_row['price_vs_sma5'], last_row['price_vs_sma20']
            ]
            
            return features
            
        except Exception as e:
            print(f"❌ Errore features: {e}")
            return None

def ml_trading_bot():
    """Bot di trading con ML"""
    trader = MLTrader()
    
    print("🧠 INIZIALIZZAZIONE ML TRADING BOT")
    print("=====================================")
    
    # Addestra il modello
    if not trader.train_model("BTCUSDT", years=2):
        print("❌ Fallito addestramento, uso strategia di fallback")
        return
    
    # Loop di trading
    print("\n🚀 AVVIO TRADING ML IN TEMPO REALE")
    print("=====================================")
    
    trade_count = 0
    
    while True:
        try:
            # Ottieni features correnti
            features = trader.get_current_features("BTCUSDT")
            if features is None:
                print("❌ Impossibile ottenere features, aspetta...")
                time.sleep(60)
                continue
            
            # Predici segnale
            signal, confidence = trader.predict_signal(features)
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            print(f"⏰ {timestamp} | 🧠 ML: {signal} (confidence: {confidence:.2f})")
            
            # Paper trading
            if signal in ["BUY", "SELL"] and confidence > 0.6:
                print(f"💡 SEGNALE FORTE: {signal} (confidence: {confidence:.2f})")
                print("💰 PAPER TRADE ESEGUITO")
                trade_count += 1
                print(f"📈 Trade totali ML: {trade_count}")
            
            # Aspetta 1 ora tra le predizioni (ML è più lento)
            time.sleep(3600)  # 1 ora
            
        except Exception as e:
            print(f"❌ Errore bot ML: {e}")
            time.sleep(300)  # Aspetta 5 minuti se errore

if __name__ == "__main__":
    ml_trading_bot()
