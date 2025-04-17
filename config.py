# config.py
import os

from dotenv import load_dotenv

load_dotenv()  # reads .env file if present

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("Please set TELEGRAM_TOKEN in environment")
if not ALPHA_VANTAGE_API_KEY:
    raise ValueError("Please set ALPHA_VANTAGE_API_KEY in environment")
