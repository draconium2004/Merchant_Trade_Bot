from signal_generator import get_trade_signal
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

import os

# Get token from environment variable
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
CHAT_ID = "@your_channel"
MONITORED = ["EUR/USD"]

# Setup bot and updater
bot = Bot(token=TOKEN)
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# START command handler
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Draco Tower is online and monitoring the market!")

# Register /start command
dispatcher.add_handler(CommandHandler("start", start))

# Function to check and alert
def check_and_alert():
    for sym in MONITORED:
        sig = get_trade_signal(sym)
        if not sig:
            continue
        icon = '🟢' if sig['signal'] == 1 else '🔴' if sig['signal'] == -1 else '⚪️'
        text = (
            f"{icon} Signal for {sym} @ {sig['price']:.4f}\n"
            f"Strategy: {sig['strategy']}"
        )
        bot.send_message(CHAT_ID, text)

# Run the bot
if __name__ == "__main__":
    check_and_alert()  # Optional: Run alert once on startup
    updater.start_polling()
    updater.idle()