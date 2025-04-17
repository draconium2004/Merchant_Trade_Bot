# signal_generator.py
import pandas as pd
from models.rf_model import generate_signal

def fetch_latest_ohlcv(symbol: str, limit: int = 100) -> pd.DataFrame:
    """
    Replace this stub with your exchange API client.
    Must return a DataFrame indexed by timestamp with
    ['open','high','low','close','volume'].
    """
    # e.g. return binance_client.get_klines(symbol, interval='1h', limit=limit)
    pass

def sl_tp_levels(last_close: float, df_ohlcv: pd.DataFrame) -> dict:
    """
    Example: use ATR for volatility‐based SL/TP.
    """
    high_low = df_ohlcv['high'] - df_ohlcv['low']
    atr = high_low.rolling(14).mean().iloc[-1]
    return {
        'sl': round(last_close - 1.5 * atr, 4),
        'tp': round(last_close + 2   * atr, 4)
    }

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