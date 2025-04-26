import os
import logging
from telegram import Bot
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get bot token from environment
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables")

# Create bot instance
bot = Bot(token=BOT_TOKEN) 