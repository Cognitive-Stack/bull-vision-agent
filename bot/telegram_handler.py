import logging
from agents import Runner
from telegram import Update
from bot.bot import bot, get_user_context
from bot.agent import bull_vision_agent

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
        await update.message.reply_text("""
Available commands:
/start - Start the bot
/help - Show this help message

You can ask me about:
- Stock analysis (e.g., "Analyze AAPL")
- Market news (e.g., "What's the latest news about Tesla?")
- Trading strategies (e.g., "What's your view on the current market?")
""")

async def handle_message(update: Update):
    """Handle regular messages using the Bull Vision agent"""
    try:
        # Get or create user context
        user_context = await get_user_context(update.message.from_user.id)
        logger.info(f"User context: {user_context}")
        print(f"User context: {user_context}")
        # Add user message to context
        user_context.add_message('user', update.message.text)
        
        # Run the agent with the context
        result = await Runner.run(
            starting_agent=bull_vision_agent,
            input=update.message.text,
            context=user_context
        )
        
        # Get the agent's response
        response = result.final_output
        
        # Add bot's response to context
        user_context.add_message('bot', response)
        
        # Send the response back to the user
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}")
        await update.message.reply_text("I'm sorry, I encountered an error while processing your request. Please try again later.") 