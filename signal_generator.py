class SignalGenerator:
    def generate_signal(self, df):
        last = df.iloc[-1]
        if last['rsi'] < 30 and last['macd'] > last['macd_signal']:
            return {
                'action': 'BUY',
                'symbol': 'BTC/USDT',
                'entry': last['close'],
                'sl': last['close'] * 0.98,
                'tp': last['close'] * 1.05
            }
        return None
