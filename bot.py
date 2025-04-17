# bot.py
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import TELEGRAM_TOKEN
from fetcher import DataFetcher
from analyzer import AnalysisEngine

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

fetcher = DataFetcher()

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /analyze <PAIR> <TIMEFRAME>\nExample: /analyze EUR/USD 1h")
            return

        pair, timeframe = args
        await update.message.chat.send_action("typing")

        df = fetcher.get_ohlcv(pair, timeframe, limit=200)
        df = AnalysisEngine.add_indicators(df)
        result = AnalysisEngine.generate_signal(df)

        text = (
            f"*{pair.upper()} Analysis* ({timeframe})\n"
            f"Last Price: `{result['price']}`\n"
            f"RSI: `{result['rsi']}`\n"
            f"MACD: `{result['macd']}` ⇨ Signal: `{result['macd_signal']}`\n"
            f"*Suggestion*: `{result['side']}`\n"
        )
        if result['sl'] and result['tp']:
            text += f"Stop Loss: `{result['sl']}`\nTake Profit: `{result['tp']}`"

        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error("Error in /analyze: %s", e, exc_info=True)
        await update.message.reply_text("Sorry, something went wrong. Please try again later.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("analyze", analyze))

    logger.info("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
