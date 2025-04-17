import yfinance as yf
import pandas as pd

def map_yahoo_symbol(symbol):
    if '/' in symbol:
        return symbol.replace('/', '') + "=X"
    return symbol

def get_trade_signal(symbol):
    try:
        symbol = map_yahoo_symbol(symbol)
        df = yf.download(symbol, period="1mo", interval="1h", progress=False)

        if df is None or df.empty:
            print(f"[WARN] No data returned for {symbol}")
            return None

        # Your strategy continues here...

        # Simple Moving Average Crossover Strategy
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()

        if df[['SMA_20', 'SMA_50']].isnull().values.any():
            return None

        latest = df.iloc[-1]
        previous = df.iloc[-2]

        if previous['SMA_20'] < previous['SMA_50'] and latest['SMA_20'] > latest['SMA_50']:
            return {
                'signal': 1,
                'price': latest['Close'],
                'symbol': symbol,
                'sl': latest['Close'] * 0.98,
                'tp': latest['Close'] * 1.02,
                'confidence': 0.75,
                'strategy': 'SMA_Crossover'
            }

        elif previous['SMA_20'] > previous['SMA_50'] and latest['SMA_20'] < latest['SMA_50']:
            return {
                'signal': -1,
                'price': latest['Close'],
                'symbol': symbol,
                'sl': latest['Close'] * 1.02,
                'tp': latest['Close'] * 0.98,
                'confidence': 0.75,
                'strategy': 'SMA_Crossover'
            }

        return {
            'signal': 0,
            'price': latest['Close'],
            'symbol': symbol,
            'sl': None,
            'tp': None,
            'confidence': 0.5,
            'strategy': 'SMA_Crossover'
        }

    except Exception as e:
        print(f"[ERROR] Signal generation failed for {symbol}: {e}")
        return None