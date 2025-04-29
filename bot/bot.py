import os
from datetime import datetime

from dotenv import load_dotenv
from telegram import Bot

from bot.context import TradingContext

# Load environment variables
load_dotenv()

# Get bot token from environment
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables")

# Create bot instance
bot = Bot(token=BOT_TOKEN)

# Store user contexts
user_contexts = {}

async def get_user_context(user_id: int) -> TradingContext:
    """Get or create a context for a user"""
    if user_id not in user_contexts:
        # Create new context for the user
        user_contexts[user_id] = TradingContext(user_id=user_id)
    return user_contexts[user_id] 