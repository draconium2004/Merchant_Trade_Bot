# fetcher.py
import pandas as pd
import time

import ccxt
from alpha_vantage.foreignexchange import ForeignExchange

from config import ALPHA_VANTAGE_API_KEY

class DataFetcher:
    def __init__(self):
        self.crypto_exchanges = {
            'binance': ccxt.binance(),
            'kraken': ccxt.kraken(),
            # add more if desired
        }
        self.fx_client = ForeignExchange(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')

    def get_ohlcv(self, pair: str, timeframe: str = '1h', limit: int = 200) -> pd.DataFrame:
        """
        Returns a DataFrame with columns: ['open','high','low','close','volume'], indexed by datetime (UTC).
        Detects crypto (if both symbols in ccxt markets) else uses Alpha Vantage for forex.
        """
        base, quote = pair.upper().split('/')
        symbol = f"{base}/{quote}"

        # 1) Try crypto
        for name, ex in self.crypto_exchanges.items():
            markets = [m['symbol'] for m in ex.load_markets().values()]
            if symbol in markets:
                df = pd.DataFrame(
                    ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit),
                    columns=['timestamp','open','high','low','close','volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                return df

        # 2) Fallback to Forex via Alpha Vantage
        # Map timeframe to function
        mapping = {
            '1min': '1min',
            '5min': '5min',
            '15min': '15min',
            '30min': '30min',
            '60min': '60min',
            'daily': 'Daily'
        }
        interval = mapping.get(timeframe, '60min')
        data, _ = self.fx_client.get_currency_exchange_intraday(
            from_symbol=base,
            to_symbol=quote,
            interval=interval,
            outputsize='compact'
        )
        df = data.rename(columns={
            '1. open':'open',
            '2. high':'high',
            '3. low':'low',
            '4. close':'close'
        })
        df.index = pd.to_datetime(df.index)
        # Alpha Vantage intraday has no volume for FX—fill zeros
        df['volume'] = 0.0
        # Ensure descending to ascending
        df = df.sort_index()
        time.sleep(12)  # respect API rate limits
        return df
