import logging
import requests
import pandas as pd
import numpy as np
import datetime
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import math
import random  # Temporary for demo purposes

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# API keys - replace with your actual keys
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Function to get forex data from Alpha Vantage
def get_forex_data(from_currency='EUR', to_currency='USD', interval='5min', output_size='full'):
    try:
        time_series_url = f'https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={from_currency}&to_symbol={to_currency}&interval={interval}&outputsize={output_size}&apikey={ALPHA_VANTAGE_API_KEY}'
        time_series_response = requests.get(time_series_url)
        time_series_data = time_series_response.json()
        
        if "Time Series FX" in time_series_data:
            # Convert to DataFrame
            raw_data = time_series_data[f"Time Series FX ({interval})"]
            df = pd.DataFrame.from_dict(raw_data, orient='index')
            
            # Convert string values to float
            for col in df.columns:
                df[col] = df[col].astype(float)
                
            # Rename columns
            df.columns = ['open', 'high', 'low', 'close']
            
            # Sort index by date
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            return df
        else:
            error_message = time_series_data.get("Error Message", "Unknown error")
            logger.error(f"Error in get_forex_data: {error_message}")
            return None
    except Exception as e:
        logger.error(f"Error in get_forex_data: {str(e)}")
        return None

# Technical indicators
def add_technical_indicators(df):
    """Add technical indicators to the dataframe"""
    if df is None or len(df) < 50:
        return None
    
    # Copy the dataframe to avoid modifying the original
    df = df.copy()
    
    # Moving Averages
    df['ma_20'] = df['close'].rolling(window=20).mean()
    df['ma_50'] = df['close'].rolling(window=50).mean()
    
    # Exponential Moving Averages
    df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
    
    # MACD (Moving Average Convergence Divergence)
    df['macd'] = df['ema_12'] - df['ema_26']
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # RSI (Relative Strength Index) - 14 period
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands - 20 period, 2 standard deviations
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    std_dev = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (std_dev * 2)
    df['bb_lower'] = df['bb_middle'] - (std_dev * 2)
    
    # ADX (Average Directional Index) - 14 period
    # Calculate +DI and -DI
    df['high_diff'] = df['high'].diff()
    df['low_diff'] = df['low'].diff().abs()
    
    # Calculate +DM and -DM
    df['+dm'] = np.where((df['high_diff'] > 0) & (df['high_diff'] > df['low_diff']), df['high_diff'], 0)
    df['-dm'] = np.where((df['low_diff'] > 0) & (df['low_diff'] > df['high_diff']), df['low_diff'], 0)
    
    # Calculate TR (True Range)
    df['tr'] = np.maximum(df['high'] - df['low'], 
                         np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                  abs(df['low'] - df['close'].shift(1))))
    
    # Calculate smoothed TR, +DM, and -DM (14-period smoothed)
    for i in range(1, len(df)):
        if i < 14:
            df.loc[df.index[i], 'smoothed_tr'] = df.loc[:df.index[i], 'tr'].sum()
            df.loc[df.index[i], 'smoothed_+dm'] = df.loc[:df.index[i], '+dm'].sum()
            df.loc[df.index[i], 'smoothed_-dm'] = df.loc[:df.index[i], '-dm'].sum()
        else:
            df.loc[df.index[i], 'smoothed_tr'] = df.loc[df.index[i-1], 'smoothed_tr'] - \
                                            (df.loc[df.index[i-1], 'smoothed_tr'] / 14) + df.loc[df.index[i], 'tr']
            df.loc[df.index[i], 'smoothed_+dm'] = df.loc[df.index[i-1], 'smoothed_+dm'] - \
                                             (df.loc[df.index[i-1], 'smoothed_+dm'] / 14) + df.loc[df.index[i], '+dm']
            df.loc[df.index[i], 'smoothed_-dm'] = df.loc[df.index[i-1], 'smoothed_-dm'] - \
                                             (df.loc[df.index[i-1], 'smoothed_-dm'] / 14) + df.loc[df.index[i], '-dm']
    
    # Calculate +DI and -DI
    df['+di'] = 100 * df['smoothed_+dm'] / df['smoothed_tr']
    df['-di'] = 100 * df['smoothed_-dm'] / df['smoothed_tr']
    
    # Calculate DX (Directional Index)
    df['dx'] = 100 * abs(df['+di'] - df['-di']) / (df['+di'] + df['-di'])
    
    # Calculate ADX (14-period smoothed DX)
    df['adx'] = df['dx'].rolling(window=14).mean()
    
    # Stochastic Oscillator
    df['lowest_14'] = df['low'].rolling(window=14).min()
    df['highest_14'] = df['high'].rolling(window=14).max()
    df['%k'] = 100 * ((df['close'] - df['lowest_14']) / (df['highest_14'] - df['lowest_14']))
    df['%d'] = df['%k'].rolling(window=3).mean()
    
    # Drop NaN rows after calculating all indicators
    df = df.dropna()
    
    return df

# Function to analyze and generate trading signals
def generate_trading_signal(df, pair):
    if df is None or len(df) < 50:
        return None, None
    
    # Get the latest data point
    latest = df.iloc[-1]
    previous = df.iloc[-2]
    
    # Trading signals based on various indicators
    signals = {
        'ma_cross': 0,
        'rsi': 0,
        'macd': 0,
        'bollinger': 0,
        'adx': 0,
        'stoch': 0
    }
    
    # 1. Moving Average Crossover
    if latest['ma_20'] > latest['ma_50'] and previous['ma_20'] <= previous['ma_50']:
        signals['ma_cross'] = 1  # Bullish signal
    elif latest['ma_20'] < latest['ma_50'] and previous['ma_20'] >= previous['ma_50']:
        signals['ma_cross'] = -1  # Bearish signal
    
    # 2. RSI Signal
    if latest['rsi'] < 30:
        signals['rsi'] = 1  # Oversold - bullish signal
    elif latest['rsi'] > 70:
        signals['rsi'] = -1  # Overbought - bearish signal
    
    # 3. MACD Signal
    if latest['macd'] > latest['macd_signal'] and previous['macd'] <= previous['macd_signal']:
        signals['macd'] = 1  # Bullish crossover
    elif latest['macd'] < latest['macd_signal'] and previous['macd'] >= previous['macd_signal']:
        signals['macd'] = -1  # Bearish crossover
    
    # 4. Bollinger Bands
    if latest['close'] < latest['bb_lower']:
        signals['bollinger'] = 1  # Price below lower band - bullish signal
    elif latest['close'] > latest['bb_upper']:
        signals['bollinger'] = -1  # Price above upper band - bearish signal
    
    # 5. ADX Strength
    if latest['adx'] > 25:
        if latest['+di'] > latest['-di']:
            signals['adx'] = 1  # Strong trend and +DI > -DI - bullish signal
        elif latest['+di'] < latest['-di']:
            signals['adx'] = -1  # Strong trend and +DI < -DI - bearish signal
    
    # 6. Stochastic Oscillator
    if latest['%k'] < 20 and latest['%k'] > latest['%d']:
        signals['stoch'] = 1  # Oversold and %K crossing above %D - bullish signal
    elif latest['%k'] > 80 and latest['%k'] < latest['%d']:
        signals['stoch'] = -1  # Overbought and %K crossing below %D - bearish signal
    
    # Calculate overall signal and confidence
    signal_values = list(signals.values())
    overall_signal = sum(signal_values)
    total_signals = len([s for s in signal_values if s != 0])
    
    if total_signals == 0:
        return None, None
    
    confidence = abs(overall_signal) / total_signals
    
    # Generate entry price, stop loss, and take profit
    current_price = latest['close']
    
    # Decision: Buy, Sell, or Hold
    if overall_signal > 0:
        direction = "BUY"
        stop_loss = current_price - (current_price * 0.005)  # 0.5% below entry
        take_profit = current_price + (current_price * 0.015)  # 1.5% above entry
    elif overall_signal < 0:
        direction = "SELL"
        stop_loss = current_price + (current_price * 0.005)  # 0.5% above entry
        take_profit = current_price - (current_price * 0.015)  # 1.5% below entry
    else:
        return None, None
    
    # Create signal message
    if direction == "BUY":
        emoji = "🟢"
    else:
        emoji = "🔴"
    
    message = f"{emoji} {direction} {pair} @ {current_price:.4f}\n"
    message += f"SL: {stop_loss:.4f}   TP: {take_profit:.4f}\n"
    message += f"Confidence: {confidence:.2f}"
    
    return message, confidence

# Function to check for and send trading signals
def check_and_send_signals(context: CallbackContext):
    job = context.job
    chat_id = job.context['chat_id']
    min_confidence = job.context.get('min_confidence', 0.3)
    pairs = job.context.get('pairs', ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD'])
    
    for pair in pairs:
        from_currency, to_currency = pair.split('/')
        
        # Get forex data
        df = get_forex_data(from_currency, to_currency, interval='15min')
        if df is not None:
            # Add technical indicators
            df_with_indicators = add_technical_indicators(df)
            
            # Generate trading signal
            signal_message, confidence = generate_trading_signal(df_with_indicators, pair)
            
            # Send signal if confidence is above threshold
            if signal_message is not None and confidence >= min_confidence:
                context.bot.send_message(chat_id=chat_id, text=signal_message)
                
                # Log the signal
                logger.info(f"Signal sent for {pair}: {signal_message}")

# Command handlers
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Hello! I am your forex trading signal bot.\n\n'
        'Commands:\n'
        '/start - Display this help message\n'
        '/signals - Start receiving trading signals\n'
        '/stop - Stop receiving trading signals\n'
        '/check EUR USD - Check for signals on EUR/USD now\n'
        '/settings - Display current settings\n'
        '/confidence 0.4 - Set minimum confidence threshold (0.1-0.9)\n'
        '/pairs EUR/USD GBP/USD - Set pairs to monitor'
    )

def check_signals_command(update: Update, context: CallbackContext):
    """Check for signals immediately for a specific pair"""
    from_currency = 'EUR'  # Default
    to_currency = 'USD'    # Default
    
    if context.args and len(context.args) >= 2:
        from_currency = context.args[0].upper()
        to_currency = context.args[1].upper()
    
    pair = f"{from_currency}/{to_currency}"
    
    update.message.reply_text(f"Checking for signals on {pair}...")
    
    # Get forex data
    df = get_forex_data(from_currency, to_currency, interval='15min')
    if df is not None:
        # Add technical indicators
        df_with_indicators = add_technical_indicators(df)
        
        # Generate trading signal
        signal_message, confidence = generate_trading_signal(df_with_indicators, pair)
        
        if signal_message is not None:
            update.message.reply_text(signal_message)
        else:
            update.message.reply_text(f"No clear signals for {pair} at this time.")
    else:
        update.message.reply_text(f"Could not retrieve data for {pair}. Please try again later.")

def start_signals(update: Update, context: CallbackContext):
    """Start sending trading signals"""
    chat_id = update.effective_chat.id
    
    # Default settings
    settings = {
        'chat_id': chat_id,
        'min_confidence': 0.3,
        'pairs': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD']
    }
    
    # Stop any existing jobs
    for job in context.job_queue.get_jobs_by_name(f"signals_{chat_id}"):
        job.schedule_removal()
    
    # Schedule signal checking every 15 minutes
    context.job_queue.run_repeating(
        check_and_send_signals,
        interval=900,  # 15 minutes in seconds
        first=10,  # Start after 10 seconds
        context=settings,
        name=f"signals_{chat_id}"
    )
    
    update.message.reply_text(
        "You will now receive trading signals when opportunities arise. "
        "Signals are analyzed every 15 minutes.\n\n"
        "Use /stop to stop receiving signals."
    )

def stop_signals(update: Update, context: CallbackContext):
    """Stop sending trading signals"""
    chat_id = update.effective_chat.id
    
    # Stop all signal jobs for this chat
    for job in context.job_queue.get_jobs_by_name(f"signals_{chat_id}"):
        job.schedule_removal()
    
    update.message.reply_text("Trading signals have been stopped.")

def set_confidence(update: Update, context: CallbackContext):
    """Set the minimum confidence threshold for signals"""
    chat_id = update.effective_chat.id
    
    if not context.args:
        update.message.reply_text("Please provide a confidence value between 0.1 and 0.9.")
        return
    
    try:
        confidence = float(context.args[0])
        if confidence < 0.1 or confidence > 0.9:
            update.message.reply_text("Confidence must be between 0.1 and 0.9.")
            return
        
        # Update confidence in all signal jobs
        for job in context.job_queue.get_jobs_by_name(f"signals_{chat_id}"):
            job.context['min_confidence'] = confidence
        
        update.message.reply_text(f"Confidence threshold set to {confidence:.1f}.")
    except ValueError:
        update.message.reply_text("Invalid confidence value. Please provide a number between 0.1 and 0.9.")

def set_pairs(update: Update, context: CallbackContext):
    """Set the currency pairs to monitor"""
    chat_id = update.effective_chat.id
    
    if not context.args:
        update.message.reply_text("Please provide at least one currency pair like EUR/USD.")
        return
    
    pairs = []
    for pair in context.args:
        # Validate pair format
        if '/' in pair and len(pair.split('/')) == 2:
            pairs.append(pair.upper())
    
    if not pairs:
        update.message.reply_text("No valid pairs provided. Format should be like EUR/USD.")
        return
    
    # Update pairs in all signal jobs
    for job in context.job_queue.get_jobs_by_name(f"signals_{chat_id}"):
        job.context['pairs'] = pairs
    
    update.message.reply_text(f"Monitoring pairs: {', '.join(pairs)}")

def show_settings(update: Update, context: CallbackContext):
    """Show current settings"""
    chat_id = update.effective_chat.id
    
    # Get settings from job
    jobs = context.job_queue.get_jobs_by_name(f"signals_{chat_id}")
    
    if not jobs:
        update.message.reply_text("Signal service is not active. Use /signals to start.")
        return
    
    job = jobs[0]
    settings = job.context
    
    message = "Current settings:\n\n"
    message += f"Minimum confidence: {settings.get('min_confidence', 0.3):.1f}\n"
    message += f"Monitoring pairs: {', '.join(settings.get('pairs', ['EUR/USD']))}\n"
    message += f"Check interval: 15 minutes"
    
    update.message.reply_text(message)

def handle_message(update: Update, context: CallbackContext):
    """Handle regular messages"""
    text = update.message.text.lower()
    update.message.reply_text(
        "I'm your forex signal bot. Use /start to see available commands."
    )

def main():
    # Create the Updater
    updater = Updater(TELEGRAM_BOT_TOKEN)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("check", check_signals_command))
    dispatcher.add_handler(CommandHandler("signals", start_signals))
    dispatcher.add_handler(CommandHandler("stop", stop_signals))
    dispatcher.add_handler(CommandHandler("confidence", set_confidence))
    dispatcher.add_handler(CommandHandler("pairs", set_pairs))
    dispatcher.add_handler(CommandHandler("settings", show_settings))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start the Bot
    updater.start_polling()
    logging.info("Bot started")
    
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()