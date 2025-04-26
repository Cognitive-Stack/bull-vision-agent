import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.bot import bot

logger = logging.getLogger(__name__)

async def handle_telegram_update(update_data: dict):
    """Process incoming Telegram updates"""
    try:
        # Create Update object from the webhook data
        update = Update.de_json(update_data, bot)
        
        if update.message:
            # Handle commands
            if update.message.text and update.message.text.startswith('/'):
                await handle_command(update)
            # Handle regular messages
            else:
                await handle_message(update)
                
    except Exception as e:
        logger.error(f"Error handling Telegram update: {str(e)}")

async def handle_command(update: Update):
    """Handle bot commands"""
    command = update.message.text.split()[0].lower()
    
    if command == '/start':
        await update.message.reply_text("Welcome to Bull Vision Agent! How can I help you today?")
    elif command == '/help':
        await update.message.reply_text("Available commands:\n/start - Start the bot\n/help - Show this help message")

async def handle_message(update: Update):
    """Handle regular messages"""
    # Add your message handling logic here
    await update.message.reply_text("I received your message!") 