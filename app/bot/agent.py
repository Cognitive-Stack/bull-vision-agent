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

set_tracing_disabled(disabled=True)
load_dotenv()

# Initialize MCPHub
hub = MCPHub()

# Azure OpenAI configuration
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

openai_client = AsyncAzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
)

set_default_openai_client(openai_client)


class BullVisionAgent:
    def __init__(self, context: TradingContext, servers=None, portfolio_context: dict = None):
        self.context = context
        self.servers = servers or []
        self.portfolio_context = portfolio_context or {}

    def get_prompt(self):
        # You can expand this to inject more fields as needed
        prompt = BULL_VISION_PROMPT.format(
            portfolio_context=self.portfolio_context,
            current_date=datetime.now().strftime("%Y-%m-%d")
        )
        logger.info(f"Prompt: {prompt}")
        return prompt

    async def create_agent(self):
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

    async def run(self, input_text: str):
        agent = await self.create_agent()
        return await Runner.run(starting_agent=agent, input=input_text, context=self.context)

