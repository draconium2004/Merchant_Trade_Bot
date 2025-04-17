# signal_generator.py
import pandas as pd
import yfinance as yf
from models.rf_model import generate_signal

# Only EUR/USD
_YF_MAP = {
    'EUR/USD': 'EURUSD=X',
}

def fetch_latest_ohlcv(symbol: str, period: str = '5d', interval: str = '1h') -> pd.DataFrame:
    yf_ticker = _YF_MAP[symbol]  # now only 'EUR/USD'
    df = yf.download(yf_ticker, period=period, interval=interval, progress=False)
    df = df.rename(columns={
        'Open':'open','High':'high','Low':'low','Close':'close','Volume':'volume'
    })[['open','high','low','close','volume']]
    return df

# sl_tp_levels() stays the same

def get_trade_signal(symbol: str):
    df = fetch_latest_ohlcv(symbol)
    out = generate_signal(df)
    if out['signal'] == 0:
        return None
    last_price = df['close'].iloc[-1]
    levels = sl_tp_levels(last_price, df)
    return {
        'symbol': symbol,
        'side':   'BUY' if out['signal']==1 else 'SELL',
        'price':  last_price,
        'sl':     levels['sl'],
        'tp':     levels['tp'],
        'confidence': out['prob_up']
    }