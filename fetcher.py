import ccxt
import pandas as pd
from datetime import datetime

class DataFetcher:
    def __init__(self):
        self.exchange = ccxt.binance()

    def fetch_ohlcv(self, symbol='BTC/USDT', timeframe='1h', limit=100):
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df