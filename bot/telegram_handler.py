import json
import re

from agents import Runner
from loguru import logger
from telegram import Update
from telegram.constants import ParseMode

# from bot.agent import BullVisionAgent
from bot.bot import bot, get_user_context
from bot.agent import run_with_server
from controllers import news_controller

async def handle_telegram_update(update_data: dict, server, db):
    """Handle incoming Telegram updates"""
    try:
        # Create Update object from the webhook data
        update = Update.de_json(update_data, bot)
        logger.info(f"Received Telegram update: {update}")
        if update.message:
            if update.message.text and update.message.text.startswith('/'):
                await handle_command(update)
            else:
                await handle_message(update, server, db)
    except Exception as e:
        logger.error(f"Error handling Telegram update: {str(e)}")

async def handle_command(update: Update):
    """Handle bot commands"""
    command = update.message.text.split()[0].lower()
    
    if command == '/start':
        await update.message.reply_text(
            "Welcome to Bull Vision! I'm your AI-powered trading assistant. "
            "I can help you analyze stocks, provide market insights, and suggest trading strategies. "
            "How can I help you today?"
        )
    elif command == '/help':
        await update.message.reply_text(
            "Available commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n\n"
            "You can ask me about:\n"
            "- Stock analysis and technical indicators\n"
            "- Market news and trends\n"
            "- Trading strategies and risk management\n"
            "- Portfolio optimization\n"
            "- Market sentiment analysis"
        )

def escape_markdown(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

async def handle_message(update: Update, server, db):
    """Handle regular messages using the Bull Vision agent"""
    try:
        # Get or create user context
        user_context = await get_user_context(update.message.from_user.id)
        
        # Add user message to context
        user_context.add_message('user', update.message.text)
        
        # Run with the provided server
        result = await run_with_server(
            update.message.text,
            user_context,
            server
        )
        
        # Get the agent's response
        response = result.final_output
        logger.info(f"Response: {response}")
        tool_call_output_item = next((item for item in result.new_items if item.type == 'tool_call_output_item'), None)
        if tool_call_output_item:
            await news_controller.store_fetched_news(tool_call_output_item, db)
        # Add bot's response to context
        user_context.add_message('bot', response)
        # logger.info(f"User context messages:\n{user_context.get_conversation_history()}")
        
        # Send the response back to the user
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}")
        await update.message.reply_text(
            "I'm sorry, I encountered an error while processing your request. "
            "Please try again later or contact support if the issue persists."
        ) 