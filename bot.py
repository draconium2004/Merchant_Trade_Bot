# main.py or bot.py
import time
from signal_generator import get_trade_signal
from telegram import Bot

bot = Bot(token="YOUR_BOT_TOKEN")
CHAT_ID = "@your_channel"
MONITORED = ["EUR/USD"]

def check_and_alert():
    for sym in MONITORED:
        sig = get_trade_signal(sym)
        if not sig:
            continue
        icon = '🟢' if sig['side'] == 'BUY' else '🔴'
        text = (
            f"{icon} {sig['side']} {sig['symbol']} @ {sig['price']:.4f}\n"
            f"SL: {sig['sl']:.4f}   TP: {sig['tp']:.4f}\n"
            f"Confidence: {sig['confidence']:.2f}"
        )
        bot.send_message(CHAT_ID, text)

# Loop forever (every 1 hour)
while True:
    check_and_alert()
    time.sleep(3600)