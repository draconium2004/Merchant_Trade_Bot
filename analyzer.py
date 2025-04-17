# analyzer.py
import pandas as pd
import numpy as np

from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands, AverageTrueRange

class AnalysisEngine:
    @staticmethod
    def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['rsi'] = RSIIndicator(df['close']).rsi()
        macd = MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        bb = BollingerBands(df['close'])
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['atr'] = AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
        return df.dropna()

    @staticmethod
    def generate_signal(df: pd.DataFrame) -> dict:
        latest = df.iloc[-1]
        prev    = df.iloc[-2]

        rsi, macd, signal, atr, price = \
            latest['rsi'], latest['macd'], latest['macd_signal'], latest['atr'], latest['close']

        # MACD cross
        macd_cross_up = prev['macd'] < prev['macd_signal'] and macd > signal
        macd_cross_dn = prev['macd'] > prev['macd_signal'] and macd < signal

        # Basic logic
        if rsi < 30 and macd_cross_up:
            side = "BUY"
            sl = price - atr
            tp = price + 2 * atr
        elif rsi > 70 and macd_cross_dn:
            side = "SELL"
            sl = price + atr
            tp = price - 2 * atr
        else:
            side = "WAIT"
            sl = tp = None

        return {
            "side": side,
            "price": round(price, 6),
            "rsi": round(rsi, 2),
            "macd": round(macd, 6),
            "macd_signal": round(signal, 6),
            "sl": round(sl, 6) if sl else None,
            "tp": round(tp, 6) if tp else None
        }
