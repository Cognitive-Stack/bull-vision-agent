import os
from datetime import datetime

from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    set_default_openai_client,
    set_tracing_disabled,
)
from dotenv import load_dotenv
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
    get_vcb_exchange_rate,
    screen_stocks,
)
from app.prompts.agent import BULL_VISION_PROMPT
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


class BullVisionAgent:
    def __init__(self, context: TradingContext, servers=None, portfolio_context: dict = None, profile_context: dict = None):
        self.context = context
        self.servers = servers or []
        self.portfolio_context = portfolio_context or {}
        self.profile_context = profile_context or {}

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
                ],
                mcp_servers=self.servers,
            )
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            return None

    async def run(self, input_text: str):
        try:
            agent = await self.create_agent()
            if agent is None:
                return "Sorry, there was an error initializing the agent."
            return await Runner.run(starting_agent=agent, input=input_text, context=self.context)
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            return "Sorry, there was an error processing your request."

