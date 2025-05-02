import json
import re

from agents import Runner
from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from typing import List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.bot.agent import run_with_server

# from bot.agent import BullVisionAgent
from app.bot.bot import bot, get_user_context
from app.controllers import news_controller


async def handle_telegram_update(update_data: dict, servers, db):
    """Handle incoming Telegram updates"""
    try:
        # Create Update object from the webhook data
        update = Update.de_json(update_data, bot)
        logger.info(f"Received Telegram update: {update}")
        if update.message:
            if update.message.text and update.message.text.startswith("/"):
                await handle_command(update)
            else:
                await handle_message(update, servers, db)
    except Exception as e:
        logger.error(f"Error handling Telegram update: {str(e)}")


async def handle_command(update: Update):
    """Handle bot commands"""
    command = update.message.text.split()[0].lower()

    if command == "/start":
        await update.message.reply_text(
            "Welcome to Bull Vision! I'm your AI-powered trading assistant. "
            "I can help you analyze stocks, provide market insights, and suggest trading strategies. "
            "How can I help you today?"
        )
    elif command == "/help":
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
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


def get_tool_call_output(result: Any, tool_name: str) -> Optional[Any]:
    """
    Get the tool call output for a specific tool from the agent result.
    
    Args:
        result: The agent result containing tool calls and outputs
        tool_name: The name of the tool to find
        
    Returns:
        The tool call output item if found, None otherwise
    """
    try:
        # Find the tool call item
        tool_call_item = next(
            (item for item in result.new_items 
             if item.type == "tool_call_item" and item.raw_item.name == tool_name),
            None
        )

        # Find matching tool call output item with same call_id
        if tool_call_item:
            return next(
                (item for item in result.new_items 
                 if item.type == "tool_call_output_item" 
                 and item.raw_item.get('call_id', None) == tool_call_item.raw_item.call_id),
                None
            )
        return None
    except Exception as e:
        logger.error(f"Error getting tool call output for {tool_name}: {str(e)}")
        return None


async def handle_message(update: Update, servers, db):
    """Handle regular messages using the Bull Vision agent"""
    try:
        # Get or create user context
        user_context = await get_user_context(update.message.from_user.id)

        # Add user message to context
        user_context.add_message("user", update.message.text)

        # Run with the provided server
        result = await run_with_server(update.message.text, user_context, servers)

        # Get the agent's response
        response = result.final_output
        logger.info(f"Response: {response}")

        # Get search-stock-news tool output and store news if available
        search_stock_output_item = get_tool_call_output(result, "search-stock-news")
        if search_stock_output_item:
            logger.info(f"Search stock output item: {search_stock_output_item}")
            await news_controller.store_fetched_news(search_stock_output_item, db)
        
        # Get analyze-stock tool output and store news if available
        analyze_stock_output_item = get_tool_call_output(result, "analyze-stock")
        if analyze_stock_output_item:   
            logger.info(f"Analyze stock output item: {analyze_stock_output_item}")

        # Add bot's response to context
        user_context.add_message("bot", response)
        # logger.info(f"User context messages:\n{user_context.get_conversation_history()}")

        # Send the response back to the user
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}")
        await update.message.reply_text(
            "I'm sorry, I encountered an error while processing your request. "
            "Please try again later or contact support if the issue persists."
        )
