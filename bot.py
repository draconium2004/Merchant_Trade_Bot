import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import datetime

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Alpha Vantage API key - replace with your own
ALPHA_VANTAGE_API_KEY = "63SF5BK099IJ0R42"

# Function to get forex data from Alpha Vantage
async def get_forex_data(from_currency='EUR', to_currency='USD'):
    try:
        # For real-time exchange rate
        url = f'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_currency}&to_currency={to_currency}&apikey={ALPHA_VANTAGE_API_KEY}'
        response = requests.get(url)
        data = response.json()
        
        if "Realtime Currency Exchange Rate" in data:
            rate_data = data["Realtime Currency Exchange Rate"]
            exchange_rate = float(rate_data["5. Exchange Rate"])
            last_refreshed = rate_data["6. Last Refreshed"]
            
            # For historical data to calculate changes
            time_series_url = f'https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={from_currency}&to_symbol={to_currency}&apikey={ALPHA_VANTAGE_API_KEY}'
            time_series_response = requests.get(time_series_url)
            time_series_data = time_series_response.json()
            
            analysis_result = f"{from_currency}/{to_currency} Current Rate: {exchange_rate:.4f} (Updated: {last_refreshed})\n"
            
            if "Time Series FX (Daily)" in time_series_data:
                daily_data = time_series_data["Time Series FX (Daily)"]
                dates = list(daily_data.keys())
                
                if len(dates) > 1:
                    today_data = daily_data[dates[0]]
                    yesterday_data = daily_data[dates[1]]
                    
                    today_close = float(today_data["4. close"])
                    yesterday_close = float(yesterday_data["4. close"])
                    
                    daily_change = today_close - yesterday_close
                    daily_percent = (daily_change / yesterday_close) * 100
                    
                    analysis_result += f"Daily Change: {daily_change:.4f} ({daily_percent:.2f}%)\n"
                
                if len(dates) >= 7:
                    week_ago_data = daily_data[dates[6]]
                    week_ago_close = float(week_ago_data["4. close"])
                    
                    weekly_change = today_close - week_ago_close
                    weekly_percent = (weekly_change / week_ago_close) * 100
                    
                    analysis_result += f"Weekly Change: {weekly_change:.4f} ({weekly_percent:.2f}%)\n"
                
                if len(dates) >= 30:
                    month_ago_data = daily_data[dates[29]]
                    month_ago_close = float(month_ago_data["4. close"])
                    
                    monthly_change = today_close - month_ago_close
                    monthly_percent = (monthly_change / month_ago_close) * 100
                    
                    analysis_result += f"Monthly Change: {monthly_change:.4f} ({monthly_percent:.2f}%)\n"
            
            return analysis_result
        else:
            error_message = data.get("Error Message", "Unknown error")
            return f"Error fetching {from_currency}/{to_currency} rate: {error_message}"
    except Exception as e:
        logger.error(f"Error in get_forex_data: {str(e)}")
        return f"Error fetching {from_currency}/{to_currency} rate: {str(e)}"

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Hello! I am your forex bot powered by Alpha Vantage.\n\n'
        'Commands:\n'
        '/forex EUR USD - Get EUR/USD exchange rate\n'
        '/forex GBP JPY - Get GBP/JPY exchange rate\n'
        'Or just type: forex EUR USD'
    )

async def forex_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from_currency = 'EUR'  # Default from currency
    to_currency = 'USD'    # Default to currency
    
    if context.args and len(context.args) >= 2:
        from_currency = context.args[0].upper()
        to_currency = context.args[1].upper()
    
    await update.message.reply_text(f"Fetching data for {from_currency}/{to_currency}...")
    result = await get_forex_data(from_currency, to_currency)
    await update.message.reply_text(result)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text.startswith('forex '):
        parts = text.split()
        from_currency = 'EUR'  # Default
        to_currency = 'USD'    # Default
        
        if len(parts) >= 3:
            from_currency = parts[1].upper()
            to_currency = parts[2].upper()
        
        await update.message.reply_text(f"Fetching data for {from_currency}/{to_currency}...")
        result = await get_forex_data(from_currency, to_currency)
        await update.message.reply_text(result)
    else:
        await update.message.reply_text(
            "I'm your forex bot. Use /forex EUR USD to get exchange rate data or simply type: forex EUR USD"
        )

# Function to send daily updates to subscribed users
async def send_daily_update(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    currency_pair = job.data
    
    from_currency, to_currency = currency_pair.split('/')
    result = await get_forex_data(from_currency, to_currency)
    
    await context.bot.send_message(chat_id=chat_id, text=f"📊 Daily Update 📊\n\n{result}")

# Command to subscribe to daily updates
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    from_currency = 'EUR'
    to_currency = 'USD'
    
    if context.args and len(context.args) >= 2:
        from_currency = context.args[0].upper()
        to_currency = context.args[1].upper()
    
    currency_pair = f"{from_currency}/{to_currency}"
    
    # Remove existing jobs for this chat_id and currency pair
    current_jobs = context.job_queue.get_jobs_by_name(f"{chat_id}_{currency_pair}")
    for job in current_jobs:
        job.schedule_removal()
    
    # Schedule a job to send updates daily at 9:00 AM
    context.job_queue.run_daily(
        send_daily_update,
        time=datetime.time(hour=9, minute=0, second=0),
        days=(0, 1, 2, 3, 4, 5, 6),  # All days of the week
        chat_id=chat_id,
        name=f"{chat_id}_{currency_pair}",
        data=currency_pair
    )
    
    await update.message.reply_text(f"You are now subscribed to daily updates for {currency_pair}. You will receive updates every day at 9:00 AM.")

# Command to unsubscribe from daily updates
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if context.args and len(context.args) >= 2:
        from_currency = context.args[0].upper()
        to_currency = context.args[1].upper()
        currency_pair = f"{from_currency}/{to_currency}"
        
        # Remove jobs for this chat_id and currency pair
        current_jobs = context.job_queue.get_jobs_by_name(f"{chat_id}_{currency_pair}")
        for job in current_jobs:
            job.schedule_removal()
        
        await update.message.reply_text(f"You are now unsubscribed from daily updates for {currency_pair}.")
    else:
        # Remove all jobs for this chat_id
        for job in context.job_queue.jobs():
            if job.name.startswith(f"{chat_id}_"):
                job.schedule_removal()
        
        await update.message.reply_text("You are now unsubscribed from all daily updates.")

def main():
    # Create the Application
    application = Application.builder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("forex", forex_command))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    application.run_polling()
    logging.info("Bot started")

if __name__ == '__main__':
    main()