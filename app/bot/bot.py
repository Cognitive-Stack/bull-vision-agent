from telegram import Bot

from app.bot.context import TradingContext
from app.core.settings import get_settings

# Load environment variables
settings = get_settings()

# Store user contexts
user_contexts = {}

async def get_user_context(user_id: int) -> TradingContext:
    """Get or create a context for a user"""
    if user_id not in user_contexts:
        # Create new context for the user
        user_contexts[user_id] = TradingContext(user_id=user_id)
    return user_contexts[user_id]

# Create a single Bot instance
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
