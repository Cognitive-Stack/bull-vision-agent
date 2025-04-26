import os
import logging
from dotenv import load_dotenv
from bot.bot import bot

logger = logging.getLogger(__name__)

async def startup_event():
    """Register Telegram webhook URL on application startup"""
    try:
        load_dotenv()
        webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
        
        if not webhook_url:
            logger.error("TELEGRAM_WEBHOOK_URL not set in environment variables")
            return
            
        await bot.set_webhook(url=webhook_url)
        logger.info(f"Successfully registered webhook URL: {webhook_url}")
    except Exception as e:
        logger.error(f"Error registering webhook: {str(e)}") 