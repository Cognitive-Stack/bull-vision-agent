import re
from collections import defaultdict
from typing import Any, Optional

from loguru import logger
from telegram import Update
from telegram.constants import ParseMode

from app.bot.agent import BullVisionAgent
from app.bot.bot import bot, get_user_context
from app.controllers import news_controller
from app.controllers.portfolio import setup_portfolio, user_has_portfolio

# In-memory state for portfolio setup (user_id -> setup state)
portfolio_setup_states = defaultdict(dict)


async def handle_telegram_update(update_data: dict, servers, db):
    """Handle incoming Telegram updates"""
    try:
        update = Update.de_json(update_data, bot)
        logger.info(f"Received Telegram update: {update}")
        if update.message:
            user_id = update.message.from_user.id
            if user_id in portfolio_setup_states:
                await handle_portfolio_setup(update, db)
            elif update.message.text and update.message.text.startswith("/"):
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
    elif command == "/setup_portfolio":
        user_id = update.message.from_user.id
        portfolio_setup_states[user_id] = {"step": "portfolio_size"}
        await update.message.reply_text("Let's set up your portfolio!\nWhat is your portfolio size (in VND)?")


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
            logger.info(f"Tool call item name: {tool_call_item.raw_item.name}")
            logger.info(f"Tool call item arguments: {tool_call_item.raw_item.arguments}")
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
        # Check if user has a portfolio
        user_id = update.message.from_user.id
        portfolio = await user_has_portfolio(user_id, db)
        if not portfolio:
            await update.message.reply_text(
                "You need to set up your portfolio before I can assist you. "
                "Please use the /setup_portfolio command to get started."
            )
            return

        # Get or create user context
        user_context = await get_user_context(user_id)

        # Add user message to context
        user_context.add_message("user", update.message.text)

        # Use BullVisionAgent directly
        agent = BullVisionAgent(context=user_context, servers=servers, portfolio_context=portfolio)
        result = await agent.run(update.message.text)

        # Get the agent's response
        response = result.final_output
        logger.info(f"Response: {response}")

        # Get search-stock-news tool output and store news if available
        search_stock_output_item = get_tool_call_output(result, "search-stock-news")
        if search_stock_output_item:
            logger.info(f"Search stock output item: {search_stock_output_item}")
            await news_controller.store_fetched_news(search_stock_output_item, db)
        
        # Get analyze-stock tool output and store news if available
        # analyze_stock_output_item = get_tool_call_output(result, "analyze-stock")
        # if analyze_stock_output_item:   
        #     logger.info(f"Analyze stock output item: {analyze_stock_output_item}")

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


async def handle_portfolio_setup(update: Update, db):
    user_id = update.message.from_user.id
    state = portfolio_setup_states[user_id]
    text = update.message.text.strip()

    if state["step"] == "portfolio_size":
        try:
            state["portfolio_size"] = int(text.replace(",", ""))
        except ValueError:
            await update.message.reply_text("Please enter a valid number for your portfolio size (in VND).")
            return
        state["step"] = "current_exposure"
        await update.message.reply_text("What is your current exposure? (e.g. 40% invested, 60% cash)")
    elif state["step"] == "current_exposure":
        # Simple parsing, you may want to improve this
        state["current_exposure"] = text
        state["step"] = "strategy_preference"
        await update.message.reply_text("What is your strategy preference?")
    elif state["step"] == "strategy_preference":
        state["strategy_preference"] = text
        state["step"] = "goal"
        await update.message.reply_text("What is your investment goal?")
    elif state["step"] == "goal":
        state["goal"] = text
        state["step"] = "max_hold_per_swing"
        await update.message.reply_text("What is the maximum hold period per swing?")
    elif state["step"] == "max_hold_per_swing":
        state["max_hold_per_swing"] = text

        # All data collected, save to DB
        await setup_portfolio(
            user_id,
            db,
            portfolio_size=state["portfolio_size"],
            current_exposure=state["current_exposure"],
            strategy_preference=state["strategy_preference"],
            goal=state["goal"],
            max_hold_per_swing=state["max_hold_per_swing"]
        )
        await update.message.reply_text("Your portfolio has been set up successfully!")
        del portfolio_setup_states[user_id]
