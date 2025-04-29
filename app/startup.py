import os

from dotenv import load_dotenv
from loguru import logger

# from bot.agent import initialize_agent
from bot.bot import bot


async def startup_event():
    """Initialize application components on startup"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Register Telegram webhook
        webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
        if not webhook_url:
            logger.error("TELEGRAM_WEBHOOK_URL not set in environment variables")
            return
            
        await bot.set_webhook(url=webhook_url)
        logger.info(f"Successfully registered webhook URL: {webhook_url}")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise 