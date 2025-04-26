import os

from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    set_default_openai_client,
    set_tracing_disabled,
)
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI

from bot.context import TradingContext

set_tracing_disabled(disabled=True)
load_dotenv()

deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

openai_client = AsyncAzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT")
)

set_default_openai_client(openai_client)

# Create the Bull Vision agent
bull_vision_agent = Agent[TradingContext](
    name="Bull Vision",
    instructions="""
    You are Bull Vision, an AI-powered stock trading assistant. Your role is to:
    1. Analyze stock market data and news
    2. Provide trading insights and strategies
    3. Help users make informed trading decisions
    
    When analyzing stocks:
    - Consider volume trends and compare to average volume
    - Look for significant news events that might impact the stock
    - Provide clear, actionable insights
    - Be conservative in your recommendations
    - Always consider risk management
    
    Your responses should be:
    - Clear and concise
    - Data-driven
    - Include both technical and fundamental analysis
    - Suggest potential entry/exit points when relevant
    - Include risk warnings and disclaimers
    
    Remember: Past performance is not indicative of future results.
    """,
    output_type=str,
    model=OpenAIChatCompletionsModel(
        model=deployment,
        openai_client=openai_client,
    )
) 