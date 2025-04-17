from ta.momentum import RSIIndicator
from ta.trend import MACD

class AnalysisEngine:
    def analyze(self, df):
        rsi = RSIIndicator(df['close']).rsi()
        macd = MACD(df['close'])
        df['rsi'] = rsi
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        return df