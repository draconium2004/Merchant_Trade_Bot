import yfinance as yf
import pandas as pd

def get_trade_signal(symbol):
    try:
        df = yf.download(symbol, period="1mo", interval="1h", progress=False)

        if df is None or df.empty:
            print(f"[WARN] No data returned for {symbol}")
            return None

        # Simple Moving Average Crossover Strategy
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()

        # Last two rows for crossover detection
        if df[['SMA_20', 'SMA_50']].isnull().values.any():
            return None  # Not enough data yet

        latest = df.iloc[-1]
        previous = df.iloc[-2]

        # BUY Signal: Short MA crosses above Long MA
        if previous['SMA_20'] < previous['SMA_50'] and latest['SMA_20'] > latest['SMA_50']:
            return {'signal': 1, 'price': latest['Close'], 'strategy': 'SMA_Crossover'}

        # SELL Signal: Short MA crosses below Long MA
        elif previous['SMA_20'] > previous['SMA_50'] and latest['SMA_20'] < latest['SMA_50']:
            return {'signal': -1, 'price': latest['Close'], 'strategy': 'SMA_Crossover'}

        # HOLD/No signal
        return {'signal': 0, 'price': latest['Close'], 'strategy': 'SMA_Crossover'}

    except Exception as e:
        print(f"[ERROR] Signal generation failed for {symbol}: {e}")
        return None