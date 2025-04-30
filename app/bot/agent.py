import os

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


async def create_bull_vision_agent(server):
    """Create the Bull Vision agent with MCP server integration"""
    mcp_servers = [] if server is None else [server]
    return Agent[TradingContext](
        name="Bull Vision",
        instructions="""
        You are Bull Vision, an AI-powered stock trading assistant. Your role is to:
        1. Provide expert guidance on stock trading and investment strategies
        2. Help analyze stocks and market conditions
        3. Assist with portfolio management and risk assessment

        When discussing stocks and trading:
        - Explain technical analysis concepts and indicators
        - Provide insights on fundamental analysis methods
        - Guide on position sizing and risk management
        - Discuss market psychology and trading discipline
        - Share best practices for different trading styles
        - Give conservative, balanced perspectives
        - Emphasize risk awareness and management

        When users ask about specific stocks:
        1. Ask for the stock symbol/ticker if not provided
        2. Ask for the time period for news search if not specified
        3. Once you have the required information:
           - Use search-stock-news tool to gather latest news and developments
           - Analyze available information and market context
           - Provide balanced insights while highlighting risks
        4. If information is incomplete:
           - Politely ask user to provide missing details
           - Explain what information is needed and why
           - Wait for user response before proceeding with analysis
        
        Your responses should be formatted in Telegram markdown style:
        - Use *bold* for important points and key metrics
        - Use _italic_ for emphasis and technical terms
        - Use `code blocks` for specific numbers and data points
        - Use bullet points with clear spacing
        
        Structure your responses with:
        - A clear *Summary* section at the top
        - *Technical Analysis* with key indicators
        - *Fundamental Analysis* with company metrics  
        - *Entry/Exit Points* when applicable
        - _Risk Warnings_ in italic at the bottom
        
        Keep responses:
        - Clear and data-driven
        - Well-formatted with proper markdown
        - Easy to scan with headers and bullet points
        - Professional but conversational in tone
        - Complete with risk disclaimers
        
        Remember: Past performance is not indicative of future results.
        """,
        output_type=str,
        model=OpenAIChatCompletionsModel(
            model=deployment,
            openai_client=openai_client,
        ),
        mcp_servers=mcp_servers,
    )


async def run_with_server(input_text: str, context: TradingContext, server):
    """Run the agent with the provided server"""
    agent = await create_bull_vision_agent(server)
    return await Runner.run(starting_agent=agent, input=input_text, context=context)
