# bot.py
from telegram import Bot
from signal_generator import get_trade_signal

TELEGRAM_TOKEN = '…'
bot = Bot(token=TELEGRAM_TOKEN)
CHAT_ID    = '@your_channel_or_group'

# Only EUR/USD
MONITORED  = ['EUR/USD']

def check_and_alert():
    for sym in MONITORED:
        sig = get_trade_signal(sym)
        if not sig:
            continue

        icon = '🟢' if sig['side']=='BUY' else '🔴'
        text = (
            f"{icon} {sig['side']} {sig['symbol']} @ {sig['price']:.4f}\n"
            f"SL: {sig['sl']:.4f}   TP: {sig['tp']:.4f}\n"
            f"Confidence: {sig['confidence']:.2f}"
        )
        bot.send_message(CHAT_ID, text)

if __name__ == "__main__":
    check_and_alert()