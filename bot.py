# bot.py
from telegram import Bot
from signal_generator import get_trade_signal

TELEGRAM_TOKEN = '…'
bot = Bot(token=TELEGRAM_TOKEN)
CHAT_ID    = '@your_channel_or_group'

MONITORED = ['BTCUSDT','ETHUSDT','SOLUSDT']  # expand as desired

def check_and_alert():
    for sym in MONITORED:
        sig = get_trade_signal(sym)
        if sig:
            text = (
                f"{sig['side']} {sig['symbol']} @ {sig['price']}\n"
                f"SL: {sig['sl']}  TP: {sig['tp']}\n"
                f"Confidence: {sig['confidence']:.2f}"
            )
            bot.send_message(CHAT_ID, text)

if __name__ == "__main__":
    # schedule this every hour (e.g. via APScheduler or a cron job)
    check_and_alert()