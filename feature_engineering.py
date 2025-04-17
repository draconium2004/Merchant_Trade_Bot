# feature_engineering.py
import pandas as pd

def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input: raw OHLCV DataFrame with datetime index and columns
           ['open','high','low','close','volume']
    Output: df with added indicator columns and no NaNs.
    """
    df = df.copy()
    df['return'] = df['close'].pct_change()
    df['ma20']   = df['close'].rolling(20).mean()
    df['ma50']   = df['close'].rolling(50).mean()
    # RSI
    diff = df['close'].diff()
    gain = diff.clip(lower=0).rolling(14).mean()
    loss = -diff.clip(upper=0).rolling(14).mean()
    df['rsi'] = 100 - 100 / (1 + gain / loss)
    return df.dropna()