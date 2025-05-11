from typing import Any, Dict, List

from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from fastapi import FastAPI

from app.bot.agent import BullVisionAgent
from app.bot.bot import bot
from app.bot.context import get_user_context, update_user_context
from app.controllers.portfolio import (
    setup_portfolio,
    setup_profile,
    user_has_portfolio,
    user_has_profile,
)


class TelegramHandler:
    def __init__(self, mcp_servers=None):
        self.mcp_servers = mcp_servers or []
        self.portfolio_setup_states = {}
        self.profile_setup_states = {}

    def set_mcp_servers(self, servers):
        """Set MCP servers for the handler"""
        self.mcp_servers = servers

    async def handle_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE, db=None, user_agents=None) -> None:
        """Main entry point for handling Telegram updates"""
        try:
            if update.message:
                if update.message.text and update.message.text.startswith('/'):
                    await self.handle_command(update, context)
                else:
                    await self.handle_message(update, context, db, user_agents)
            elif update.callback_query:
                await self.handle_callback_query(update.callback_query, context, db)
        except Exception as e:
            logger.error(f"Error handling update: {str(e)}")
            await self._send_error_message(update, "An error occurred while processing your request.")

    async def handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle bot commands"""
        try:
            command = update.message.text.split()[0].lower()
            if command == '/start':
                await self._handle_start_command(update)
            elif command == '/portfolio':
                await self._handle_portfolio_command(update)
            elif command == '/profile':
                await self._handle_profile_command(update)
            elif command == '/help':
                await self._handle_help_command(update)
            else:
                await update.message.reply_text("Unknown command. Use /help to see available commands.")
        except Exception as e:
            logger.error(f"Error handling command: {str(e)}")
            await self._send_error_message(update, "An error occurred while processing your command.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, db=None, user_agents=None) -> None:
        """Handle regular messages"""
        try:
            user_id = update.effective_user.id

            if user_id in self.portfolio_setup_states:
                await self.handle_portfolio_setup(update, context, db)
                return

            # Check if user has profile and portfolio in DB
            profile = await user_has_profile(user_id, db)
            portfolio = await user_has_portfolio(user_id, db)
            if not profile:
                await update.message.reply_text(
                    "Please set up your profile first using /profile command."
                )
                return

            if not portfolio:
                await update.message.reply_text(
                    "Please set up your portfolio first using /portfolio command."
                )
                return

            # Get user context
            user_context = get_user_context(user_id)
            
            # Get or create user agent
            if user_id not in user_agents:
                user_agents[user_id] = BullVisionAgent(
                    context=user_context,
                    servers=self.mcp_servers,
                    portfolio_context=portfolio,
                    profile_context=profile
                )
                logger.info(f"Created new agent for user {user_id}")
            
            # Get the user's agent
            agent = user_agents[user_id]
            
            # Process message
            response = await agent.run(update.message.text)
            logger.info(f"Response: {response}")

            # Send the response back to the user
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await self._send_error_message(update, "An error occurred while processing your message.")

    async def handle_callback_query(self, callback_query, context: ContextTypes.DEFAULT_TYPE, db=None) -> None:
        """Handle callback queries from inline keyboards"""
        try:
            user_id = callback_query.from_user.id
            data = callback_query.data

            if user_id in self.profile_setup_states:
                state = self.profile_setup_states[user_id]
                current_step = state.get('step')

                if current_step == 'risk_tolerance':
                    state['risk_tolerance'] = data
                    state['step'] = 'investment_horizon'
                    await self._ask_investment_horizon(callback_query.message)
                elif current_step == 'investment_horizon':
                    state['investment_horizon'] = data
                    state['step'] = 'investment_goals'
                    await self._ask_investment_goals(callback_query.message)
                elif current_step == 'investment_goals':
                    goals = state.get('investment_goals', [])
                    if data == 'DONE':
                        # Store profile in DB
                        await setup_profile(
                            user_id,
                            db,
                            state.get("risk_tolerance", ""),
                            state.get("investment_horizon", ""),
                            goals
                        )
                        await callback_query.message.edit_text(
                            "Your investor profile has been updated successfully! 🎯\n"
                            "You can now continue with portfolio setup using /portfolio command."
                        )
                        self.profile_setup_states.pop(user_id, None)
                    else:
                        if data in goals:
                            goals.remove(data)
                        else:
                            goals.append(data)
                        state['investment_goals'] = goals
                        await self._update_goals_keyboard(callback_query.message, goals)

            await callback_query.answer()
        except Exception as e:
            logger.error(f"Error handling callback query: {str(e)}")
            await self._send_error_message(callback_query.message, "An error occurred while processing your selection.")

    async def _handle_profile_command(self, update: Update) -> None:
        """Handle /profile command"""
        user_id = update.effective_user.id
        self.profile_setup_states[user_id] = {'step': 'risk_tolerance'}
        await self._ask_risk_tolerance(update.message)

    async def _ask_risk_tolerance(self, message) -> None:
        """Ask for risk tolerance"""
        keyboard = [
            [InlineKeyboardButton("Conservative 🔒", callback_data="conservative")],
            [InlineKeyboardButton("Moderate ⚖️", callback_data="moderate")],
            [InlineKeyboardButton("Aggressive 🚀", callback_data="aggressive")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(
            "What's your risk tolerance level?",
            reply_markup=reply_markup
        )

    async def _ask_investment_horizon(self, message) -> None:
        """Ask for investment horizon"""
        keyboard = [
            [InlineKeyboardButton("Short Term (< 1 year) ⏱️", callback_data="short_term")],
            [InlineKeyboardButton("Medium Term (1-3 years) ⌛", callback_data="medium_term")],
            [InlineKeyboardButton("Long Term (> 3 years) 🗓️", callback_data="long_term")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.edit_text(
            "What's your investment horizon?",
            reply_markup=reply_markup
        )

    async def _ask_investment_goals(self, message) -> None:
        """Ask for investment goals"""
        keyboard = [
            [InlineKeyboardButton("Growth 📈", callback_data="growth")],
            [InlineKeyboardButton("Value 💎", callback_data="value")],
            [InlineKeyboardButton("Dividend 💰", callback_data="dividend")],
            [InlineKeyboardButton("Done ✅", callback_data="DONE")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.edit_text(
            "Select your investment goals (you can select multiple):",
            reply_markup=reply_markup
        )

    async def _update_goals_keyboard(self, message, selected_goals: List[str]) -> None:
        """Update the goals keyboard with selected items"""
        goals = {
            "growth": "Growth 📈",
            "value": "Value 💎",
            "dividend": "Dividend 💰"
        }
        keyboard = []
        for goal, label in goals.items():
            display_label = f"✅ {label}" if goal in selected_goals else label
            keyboard.append([InlineKeyboardButton(display_label, callback_data=goal)])
        keyboard.append([InlineKeyboardButton("Done ✅", callback_data="DONE")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Only update if the markup or text is different
        current_markup = message.reply_markup
        current_text = message.text

        new_text = "Select your investment goals (you can select multiple):"

        # Compare current and new markup/text
        if current_text != new_text or str(current_markup) != str(reply_markup):
            await message.edit_text(
                new_text,
                reply_markup=reply_markup
            )
        # else: do nothing, to avoid the error

    async def _handle_help_command(self, update: Update) -> None:
        """Handle /help command"""
        help_text = (
            "Available commands:\n"
            "/start - Start the bot\n"
            "/portfolio - Set up or update your portfolio\n"
            "/profile - Set up or update your investor profile\n"
            "/help - Show this help message\n\n"
            "You can also ask me questions about stocks, market analysis, or portfolio management."
        )
        await update.message.reply_text(help_text)

    async def handle_portfolio_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE, db=None) -> None:
        """Handle portfolio setup process"""
        try:
            user_id = update.effective_user.id
            state = self.portfolio_setup_states.get(user_id)
            text = update.message.text.strip()

            if not state:
                # Start the portfolio setup process
                self.portfolio_setup_states[user_id] = {"step": "waiting_for_symbols"}
                await update.message.reply_text(
                    "Please enter the stock symbols for your portfolio (comma-separated).\n"
                    "Example: VNM, FPT, VIC"
                )
                return

            if state["step"] == "waiting_for_symbols":
                symbols = [s.strip().upper() for s in text.split(',')]
                if not symbols:
                    await update.message.reply_text("Please enter at least one valid symbol.")
                    return
                state["symbols"] = symbols
                state["step"] = "waiting_for_weights"
                await update.message.reply_text(
                    f"Please enter the weights for {', '.join(symbols)} (comma-separated).\n"
                    "Example: 0.4, 0.3, 0.3"
                )
            elif state["step"] == "waiting_for_weights":
                try:
                    weights = [float(w.strip()) for w in text.split(',')]
                    symbols = state.get('symbols', [])
                    if len(weights) != len(symbols):
                        await update.message.reply_text(
                            f"Please enter exactly {len(symbols)} weights."
                        )
                        return
                    if abs(sum(weights) - 1.0) > 0.001:
                        await update.message.reply_text(
                            "Weights must sum to 1.0. Please try again."
                        )
                        return
                    # Save to DB
                    await setup_portfolio(user_id, db, symbols, weights)
                    self.portfolio_setup_states.pop(user_id)
                    await update.message.reply_text(
                        "Portfolio updated successfully! You can now ask me questions about your portfolio."
                    )
                except ValueError:
                    await update.message.reply_text(
                        "Please enter valid numbers for weights."
                    )
        except Exception as e:
            logger.error(f"Error in portfolio setup: {str(e)}")
            await self._send_error_message(update, "An error occurred during portfolio setup.")
            self.portfolio_setup_states.pop(user_id, None)

    async def _handle_start_command(self, update: Update) -> None:
        """Handle /start command"""
        welcome_message = (
            "Welcome to Bull Vision Agent! 🚀\n\n"
            "I can help you analyze stocks and manage your portfolio.\n"
            "Use /portfolio to set up your portfolio or /help to see all available commands."
        )
        await update.message.reply_text(welcome_message)

    async def _handle_portfolio_command(self, update: Update) -> None:
        """Handle /portfolio command"""
        await self._start_portfolio_setup(update)

    async def _start_portfolio_setup(self, update: Update) -> None:
        """Start portfolio setup process"""
        user_id = update.effective_user.id
        self.portfolio_setup_states[user_id] = {
            'step': 'waiting_for_symbols',
            'symbols': []
        }
        await update.message.reply_text(
            "Please enter the stock symbols for your portfolio (comma-separated).\n"
            "Example: VNM, FPT, VIC"
        )

    async def _process_portfolio_symbols(self, update: Update) -> None:
        """Process portfolio symbols input"""
        user_id = update.effective_user.id
        symbols = [s.strip().upper() for s in update.message.text.split(',')]
        
        if not symbols:
            await update.message.reply_text("Please enter at least one valid symbol.")
            return

        self.portfolio_setup_states[user_id] = {
            'step': 'waiting_for_weights',
            'symbols': symbols
        }
        
        await update.message.reply_text(
            f"Please enter the weights for {', '.join(symbols)} (comma-separated).\n"
            "Example: 0.4, 0.3, 0.3"
        )

    async def _send_error_message(self, update: Update, message: str) -> None:
        """Send error message to user"""
        try:
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}")

# Create singleton instance
telegram_handler = TelegramHandler() 