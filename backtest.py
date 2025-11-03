import pandas as pd
import requests
import numpy as np
from datetime import datetime, timedelta
import json
import time

print("📊 AVVIO BACKTESTING 7 ANNI...")

# Configurazione
INITIAL_BALANCE = 50  # 50€
COMMISSION = 0.001    # 0.1% commissioni Binance

# Coppie per testare (ideali per piccoli capitali)
CRYPTO_PAIRS = [
    "BTCUSDT",    # Bitcoin (referenza)
    "ADAUSDT",    # Cardano ~0.30€
    "MATICUSDT",  # Polygon ~0.50€
    "XRPUSDT",    # Ripple ~0.50€
    "DOGEUSDT",   # Dogecoin ~0.10€
    "DOTUSDT",    # Polkadot ~5€
    "AVAXUSDT",   # Avalanche ~15€
    "LINKUSDT",   # Chainlink ~12€
]

def download_historical_data(symbol, years=7):
    """Scarica dati storici da Binance"""
    print(f"📥 Scaricando dati per {symbol}...")
    
    all_data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    
    current_start = start_date
    
    while current_start < end_date:
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": "1d",  # Dati giornalieri
                "startTime": int(current_start.timestamp() * 1000),
                "endTime": int(end_date.timestamp() * 1000),
                "limit": 1000
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if not data:
                break
                
            all_data.extend(data)
            
            # Aggiorna data di inizio per prossima richiesta
            last_timestamp = data[-1][0]
            current_start = datetime.fromtimestamp(last_timestamp / 1000)
            
            # Rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Errore download {symbol}: {e}")
            break
    
    if not all_data:
        return None
    
    # Converti in DataFrame
    df = pd.DataFrame(all_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    
    # Converti timestamp e prezzi
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['volume'] = df['volume'].astype(float)
    
    # Rimuovi duplicati
    df = df.drop_duplicates('timestamp')
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"✅ {symbol}: {len(df)} giorni di dati")
    return df

def calculate_rsi(prices, period=14):
    """Calcola RSI"""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gains = pd.Series(gains).rolling(period).mean()
    avg_losses = pd.Series(losses).rolling(period).mean()
    
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    return rsi

def improved_strategy(prices, rsi_values=None):
    """Strategia migliorata con multiple condizioni"""
    if len(prices) < 20:
        return "HOLD"
    
    current_price = prices[-1]
    
    # Media mobile 20 periodi (lungo termine)
    sma_20 = np.mean(prices[-20:])
    # Media mobile 5 periodi (breve termine)
    sma_5 = np.mean(prices[-5:])
    
    # Trend: SMA5 sopra SMA20 = trend rialzista
    uptrend = sma_5 > sma_20
    
    # Calcola RSI se disponibile
    oversold = False
    overbought = False
    if rsi_values is not None and len(rsi_values) > 0:
        current_rsi = rsi_values[-1]
        oversold = current_rsi < 30
        overbought = current_rsi > 70
    
    # STRATEGIA 1: Trend Following con RSI
    if uptrend and not overbought:
        # In uptrend, compra sui pullback
        if current_price < sma_5 * 0.98:  # -2% dalla media breve
            return "BUY"
    elif not uptrend and not oversold:
        # In downtrend, vendi sui rimbalzi
        if current_price > sma_5 * 1.02:  # +2% dalla media breve
            return "SELL"
    
    return "HOLD"

def run_backtest(df, initial_balance=50, strategy_type="improved"):
    """Esegue backtesting completo"""
    balance = initial_balance
    position = 0  # 0 = no position, 1 = long
    entry_price = 0
    trades = []
    prices = df['close'].tolist()
    
    # Calcola RSI per la strategia
    rsi_values = calculate_rsi(prices).tolist() if len(prices) > 14 else None
    
    for i in range(len(prices)):
        if i < 20:  # Aspetta dati sufficienti
            continue
            
        current_data = prices[:i+1]
        current_rsi = rsi_values[:i+1] if rsi_values else None
        current_price = prices[i]
        current_date = df.iloc[i]['timestamp']
        
        # Segnale della strategia
        if strategy_type == "improved":
            action = improved_strategy(current_data, current_rsi)
        
        # GESTIONE TRADE
        if action == "BUY" and position == 0:
            # ENTRATA LONG
            position = 1
            entry_price = current_price
            trades.append({
                'type': 'BUY',
                'price': current_price,
                'date': current_date,
                'balance_before': balance
            })
            
        elif action == "SELL" and position == 1:
            # USCITA LONG
            profit_percent = (current_price - entry_price) / entry_price
            # Applica commissioni
            profit_percent -= COMMISSION * 2  # Entrata + uscita
            
            balance = balance * (1 + profit_percent)
            position = 0
            
            trades.append({
                'type': 'SELL',
                'price': current_price,
                'profit_percent': profit_percent * 100,
                'balance_after': balance,
                'date': current_date
            })
    
    # Chiudi eventuale posizione aperta
    if position == 1:
        profit_percent = (prices[-1] - entry_price) / entry_price - COMMISSION * 2
        balance = balance * (1 + profit_percent)
        trades.append({
            'type': 'SELL_FINAL',
            'price': prices[-1],
            'profit_percent': profit_percent * 100,
            'balance_after': balance,
            'date': df.iloc[-1]['timestamp']
        })
    
    # CALCOLA STATISTICHE
    total_return = (balance - initial_balance) / initial_balance * 100
    
    profitable_trades = [t for t in trades if t.get('profit_percent', 0) > 0]
    win_rate = len(profitable_trades) / len([t for t in trades if t.get('profit_percent') is not None]) * 100 if trades else 0
    
    # Drawdown
    equity_curve = [initial_balance]
    current_equity = initial_balance
    for trade in trades:
        if 'balance_after' in trade:
            current_equity = trade['balance_after']
            equity_curve.append(current_equity)
    
    max_drawdown = 0
    peak = equity_curve[0]
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        drawdown = (peak - equity) / peak * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    return {
        'initial_balance': initial_balance,
        'final_balance': balance,
        'total_return_percent': total_return,
        'total_trades': len([t for t in trades if t.get('profit_percent') is not None]),
        'win_rate': win_rate,
        'max_drawdown': max_drawdown,
        'trades': trades,
        'equity_curve': equity_curve
    }

def analyze_results(results):
    """Analizza e stampa risultati"""
    print("\n" + "="*60)
    print("📈 RISULTATI BACKTESTING 7 ANNI")
    print("="*60)
    
    best_performer = None
    worst_performer = None
    
    for symbol, result in results.items():
        if result is None:
            continue
            
        print(f"\n🎯 {symbol}")
        print(f"   💰 Balance iniziale: {result['initial_balance']}€")
        print(f"   💰 Balance finale: {result['final_balance']:.2f}€")
        print(f"   📈 Ritorno totale: {result['total_return_percent']:+.2f}%")
        print(f"   🔢 Trade totali: {result['total_trades']}")
        print(f"   ✅ Win Rate: {result['win_rate']:.1f}%")
        print(f"   📉 Max Drawdown: {result['max_drawdown']:.1f}%")
        
        if best_performer is None or result['total_return_percent'] > best_performer[1]:
            best_performer = (symbol, result['total_return_percent'])
        if worst_performer is None or result['total_return_percent'] < worst_performer[1]:
            worst_performer = (symbol, result['total_return_percent'])
    
    if best_performer:
        print(f"\n🏆 MIGLIORE: {best_performer[0]} ({best_performer[1]:+.2f}%)")
    if worst_performer:
        print(f"💩 PEGGIORE: {worst_performer[0]} ({worst_performer[1]:+.2f}%)")
    
    # Raccomandazioni
    print(f"\n💡 RACCOMANDAZIONI per {INITIAL_BALANCE}€:")
    profitable_pairs = [(s, r) for s, r in results.items() 
                       if r and r['total_return_percent'] > 0 and r['win_rate'] > 50]
    
    if profitable_pairs:
        print("✅ COPPIE PROFITTEVOLI:")
        for symbol, result in sorted(profitable_pairs, key=lambda x: x[1]['total_return_percent'], reverse=True):
            print(f"   {symbol}: {result['total_return_percent']:+.2f}% (Win Rate: {result['win_rate']:.1f}%)")
    else:
        print("❌ Nessuna coppia profittevole trovata - strategia da migliorare")

def main():
    """Funzione principale"""
    print("🚀 BACKTESTING COMPARATIVO 7 ANNI")
    print(f"💰 Capitale iniziale: {INITIAL_BALANCE}€")
    print(f"📊 Coppie testate: {', '.join(CRYPTO_PAIRS)}")
    print("⏳ Questo potrebbe richiedere alcuni minuti...")
    
    results = {}
    
    for symbol in CRYPTO_PAIRS:
        try:
            # Scarica dati
            df = download_historical_data(symbol, years=7)
            if df is None or len(df) < 100:
                print(f"❌ Dati insufficienti per {symbol}")
                results[symbol] = None
                continue
            
            # Esegui backtest
            result = run_backtest(df, INITIAL_BALANCE, "improved")
            results[symbol] = result
            
        except Exception as e:
            print(f"❌ Errore con {symbol}: {e}")
            results[symbol] = None
    
    # Analizza risultati
    analyze_results(results)
    
    # Salva risultati dettagliati
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backtest_results_{timestamp}.json"
    
    # Converti per JSON
    json_results = {}
    for symbol, result in results.items():
        if result:
            json_results[symbol] = {
                k: v for k, v in result.items() 
                if k not in ['trades', 'equity_curve']  # Escludi dati grandi
            }
    
    with open(filename, 'w') as f:
        json.dump(json_results, f, indent=2, default=str)
    
    print(f"\n💾 Risultati salvati in: {filename}")

if __name__ == "__main__":
    main()
