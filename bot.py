from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import TELEGRAM_TOKEN
from fetcher import DataFetcher
from analyzer import AnalysisEngine
from signal_generator import SignalGenerator
import asyncio

fetcher = DataFetcher()
analyzer = AnalysisEngine()
signal_gen = SignalGenerator()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to the Trading Bot!")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = fetcher.fetch_ohlcv()
    analyzed = analyzer.analyze(df)
    signal = signal_gen.generate_signal(analyzed)

    if signal:
        msg = f"""
*Signal Detected:*
Action: {signal['action']}
Pair: {signal['symbol']}
Entry: {signal['entry']:.2f}
SL: {signal['sl']:.2f}
TP: {signal['tp']:.2f}
        """
        await update.message.reply_text(msg, parse_mode='Markdown')
    else:
        await update.message.reply_text("No signal right now.")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))

async def hourly_job():
    while True:
        # Send signal to your chat ID (or broadcast logic)
        # (We can fetch chat ID dynamically or store in DB)
        await asyncio.sleep(3600)

app.run_polling()
