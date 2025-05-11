import os
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
from loguru import logger
from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    set_default_openai_client,
    set_tracing_disabled,
)
from loguru import logger
from mcphub import MCPHub
from openai import AsyncAzureOpenAI

from app.bot.context import TradingContext
from app.bot.tools import (
    get_all_symbols,
    get_balance_sheet,
    get_cash_flow,
    get_company_overview,
    get_financial_ratios,
    get_fund_listings,
    get_income_statement,
    get_intraday_ticks,
    get_market_indices,
    get_price_board,
    get_sjc_gold_price,
    get_stock_context,
    get_stocks_by_industry,
    get_vcb_exchange_rate,
    screen_stocks,
)
from app.prompts.agent import BULL_VISION_PROMPT
from app.prompts.trading_expert import TRADING_EXPERT_PROMPT
from app.prompts.user_input import USER_INPUT_TEMPLATE
from app.core.settings import get_settings

set_tracing_disabled(disabled=True)

# Initialize MCPHub
hub = MCPHub()

# Use get_settings to access environment variables
settings = get_settings()

# Azure OpenAI configuration
deployment = settings.AZURE_OPENAI_DEPLOYMENT

openai_client = AsyncAzureOpenAI(
    api_key=settings.AZURE_OPENAI_API_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
)

set_default_openai_client(openai_client)

@dataclass
class ConversationMessage:
    """Represents a single message in the conversation history."""
    timestamp: datetime
    input_text: str
    response: str
    error: Optional[str] = None

class BullVisionAgent:
    def __init__(self, context: TradingContext, servers=None, portfolio_context: dict = None, profile_context: dict = None):
        self.context = context
        self.servers = servers or []
        self.portfolio_context = portfolio_context or {}
        self.profile_context = profile_context or {}
        self._conversation_history: List[ConversationMessage] = []
        self._max_history_size = 10

    @property
    def conversation_history(self) -> List[ConversationMessage]:
        """Get the conversation history."""
        return self._conversation_history

    def _add_to_history(self, message: ConversationMessage) -> None:
        """Add a message to the conversation history, maintaining the size limit."""
        try:
            self._conversation_history.append(message)
            if len(self._conversation_history) > self._max_history_size:
                self._conversation_history = self._conversation_history[-self._max_history_size:]
        except Exception as e:
            logger.error(f"Error adding message to history: {e}")

    def _format_conversation_history(self) -> str:
        """Format the conversation history for the input template."""
        if not self._conversation_history:
            return "No previous conversation history."
            
        formatted_history = []
        for msg in self._conversation_history:
            formatted_history.append(
                f"Time: {msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"User: {msg.input_text}\n"
                f"Assistant: {msg.response}\n"
            )
        return "\n".join(formatted_history)

    def _format_user_input(self, input_text: str) -> str:
        """Format the user input with conversation history and context."""
        try:
            return USER_INPUT_TEMPLATE.format(
                conversation_history=self._format_conversation_history(),
                current_input=input_text
            )
        except Exception as e:
            logger.error(f"Error formatting user input: {e}")
            return input_text

    def get_prompt(self):
        try:
            prompt = BULL_VISION_PROMPT.format(
                profile_context=self.profile_context,
                portfolio_context=self.portfolio_context,
                current_date=datetime.now().strftime("%Y-%m-%d")
            )
            logger.info(f"Prompt: {prompt}")
            return prompt
        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            return "Sorry, there was an error generating the prompt."

    async def create_agent(self):
        try:
            # Create the trading expert sub-agent
            trading_expert = Agent[TradingContext](
                name="Trading Expert",
                instructions=self.get_trading_expert_prompt(),
                output_type=str,
                model=OpenAIChatCompletionsModel(
                    model=deployment,
                    openai_client=openai_client,
                ),
                tools=[
                    get_stock_context,
                    get_all_symbols,
                    get_price_board,
                    get_company_overview,
                    get_balance_sheet,
                    get_income_statement,
                    get_cash_flow,
                    get_financial_ratios,
                    get_market_indices,
                    screen_stocks,
                    get_intraday_ticks,
                    get_fund_listings,
                    get_vcb_exchange_rate,
                    get_sjc_gold_price,
                    get_stocks_by_industry,
                ],
                mcp_servers=self.servers,
            )

            # Create the main Bull Vision agent with trading expert as a handoff
            return Agent[TradingContext](
                name="Bull Vision",
                instructions=self.get_prompt(),
                output_type=str,
                model=OpenAIChatCompletionsModel(
                    model=deployment,
                    openai_client=openai_client,
                ),
                tools=[
                    get_stock_context,
                    get_all_symbols,
                    get_price_board,
                    get_company_overview,
                    get_balance_sheet,
                    get_income_statement,
                    get_cash_flow,
                    get_financial_ratios,
                    get_market_indices,
                    screen_stocks,
                    get_intraday_ticks,
                    get_fund_listings,
                    get_vcb_exchange_rate,
                    get_sjc_gold_price,
                    get_stocks_by_industry,
                ],
                handoffs=[trading_expert],
                mcp_servers=self.servers,
            )
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            return None

    def get_trading_expert_prompt(self) -> str:
        """Get the prompt for the trading expert agent."""
        try:
            prompt = TRADING_EXPERT_PROMPT.format(
                profile_context=self.profile_context,
                portfolio_context=self.portfolio_context,
                current_date=datetime.now().strftime("%Y-%m-%d")
            )
            logger.info(f"Trading Expert Prompt: {prompt}")
            return prompt
        except Exception as e:
            logger.error(f"Error generating trading expert prompt: {e}")
            return "Sorry, there was an error generating the trading expert prompt."

    async def run(self, input_text: str) -> str:
        """
        Run the agent with the given input text and track the conversation.
        
        Args:
            input_text: The user's input text
            
        Returns:
            str: The agent's response
        """
        try:
            agent = await self.create_agent()
            if agent is None:
                error_msg = "Sorry, there was an error initializing the agent."
                return error_msg

            # Format input with conversation history
            formatted_input = self._format_user_input(input_text)
            logger.info(f"Formatted input: {formatted_input}")
            
            # Run the agent with formatted input
            response = await Runner.run(starting_agent=agent, input=formatted_input, context=self.context)
            
            # Add successful conversation to history
            self._add_to_history(ConversationMessage(
                timestamp=datetime.now(),
                input_text=input_text,
                response=response.final_output
            ))
            
            return response.final_output
            
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            return "Sorry, there was an error processing your request."

