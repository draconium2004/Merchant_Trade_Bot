import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")