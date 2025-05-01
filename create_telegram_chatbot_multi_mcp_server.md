# Building a Trading Bot with MCPHub and OpenAI Agents SDK

This guide demonstrates how to create a trading bot using MCPHub for multiple AI agents with OpenAI Agents SDK, focusing on stock analysis and market news. We'll use Telegram as the interface and MongoDB for data persistence.

## Understanding MCPHub with OpenAI Agents SDK

MCPHub works with OpenAI Agents SDK to provide:
- Multiple MCP servers for different AI agent capabilities
- Shared server connections across your application
- Efficient tool management and caching
- Seamless integration with OpenAI models

## Project Overview

We'll build a trading bot with these features:
1. Stock analysis using one MCP server
2. Market news retrieval using another MCP server
3. News storage and deduplication in MongoDB
4. User context management for conversation history

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app with MCPHub initialization
│   ├── api/
│   │   ├── __init__.py
│   │   └── telegram_webhook.py  # Telegram webhook endpoint
│   ├── core/
│   │   ├── __init__.py
│   │   └── settings.py   # Application settings
│   └── startup.py        # Startup events
├── bot/
│   ├── __init__.py
│   ├── bot.py            # Bot instance and context management
│   ├── agent.py          # AI agent implementation with MCP servers
│   ├── context.py        # Conversation context and history
│   └── telegram_handler.py  # Process incoming messages
├── models/
│   ├── __init__.py
│   └── news.py           # News data models
└── services/
    ├── __init__.py
    └── mongodb_service.py # MongoDB operations
```

## Step 1: Initialize MCPHub and FastAPI Application

First, let's set up MCPHub and FastAPI with proper lifespan management:

```python:app/main.py
from contextlib import asynccontextmanager
import contextlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from mcphub import MCPHub
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.telegram_webhook import router as telegram_router
from app.core.settings import get_settings
from app.startup import startup_event

# Initialize MCPHub
hub = MCPHub()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        settings = get_settings()
        # Initialize MongoDB client
        mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
        app.state.mongo_client = mongo_client
        app.state.mongo_db = mongo_client[settings.MONGO_DB]
        logger.info(f"MongoDB client initialized: {settings.MONGO_URI}")

        # Create and maintain MCP servers connection
        servers = [
            hub.fetch_openai_mcp_server(mcp_name="search-stock-news", cache_tools_list=True),
            hub.fetch_openai_mcp_server(mcp_name="volume-wall-detector", cache_tools_list=True)
        ]
        async with contextlib.AsyncExitStack() as stack:
            app.state.mcp_servers = [await stack.enter_async_context(server) for server in servers]
            logger.info("MCP servers initialized")

            # Initialize other components
            await startup_event()
            yield

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down MCP server")
        # Close MongoDB connection
        mongo_client = getattr(app.state, "mongo_client", None)
        if mongo_client:
            mongo_client.close()

# Create FastAPI application with lifespan
app = FastAPI(title="Bull Vision Agent", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(telegram_router, prefix="/api", tags=["telegram"])
```

Key points about the MCPHub initialization:

1. **Server Management**:
   - Uses `AsyncExitStack` to manage multiple MCP server connections
   - Initializes servers concurrently for better performance
   - Stores servers in `app.state` for global access

2. **Resource Management**:
   - Properly initializes MongoDB connection
   - Ensures cleanup of both MCP servers and MongoDB
   - Uses context managers for resource handling

3. **Error Handling**:
   - Comprehensive error handling during startup
   - Proper logging of initialization steps
   - Graceful cleanup in case of errors

4. **Configuration**:
   - Loads settings from environment variables
   - Configures CORS middleware
   - Sets up application routes

## Step 2: Accessing MCP Servers in Handlers

To use the MCP servers in your handlers, you can access them through the application state:

```python:app/api/telegram_webhook.py
from fastapi import APIRouter, Request, Depends
from typing import List

router = APIRouter()

async def get_mcp_servers(request: Request) -> List[Any]:
    """Dependency to get MCP servers from app state"""
    return request.app.state.mcp_servers

@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    servers: List[Any] = Depends(get_mcp_servers)
):
    # Use servers[0] for stock analysis
    # Use servers[1] for volume wall detection
    pass
```

## Step 3: Create Trading Agent with Multiple MCP Servers

Let's create our trading agent that uses multiple MCP servers with OpenAI Agents SDK:

```python:app/bot/agent.py
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

# Initialize tracing and environment
set_tracing_disabled(disabled=True)
load_dotenv()

# Initialize MCPHub
hub = MCPHub()

# Azure OpenAI configuration
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# Initialize OpenAI client
openai_client = AsyncAzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
)

# Set default OpenAI client
set_default_openai_client(openai_client)

async def create_bull_vision_agent(servers):
    """Create the Bull Vision agent with MCP server integration"""
    mcp_servers = [] if servers is None else servers
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
        2. For news search:
           - Use default 1 day time period
           - Use default score threshold of 0.1
        3. Once you have the stock symbol:
           - Use search-stock-news tool to gather latest news and developments
           - Use analyze-stock tool to analyze volume and value patterns
           - Analyze news and market data:
             * News sentiment (positive/negative/neutral)
             * Key company developments and announcements
             * Industry/sector news impact
             * Market reaction to news events
           - Provide T3 trading strategy recommendations based on:
             * News-driven catalysts and sentiment signals
             * T3 trading rules alignment
             * Volume confirmation of news impact
             * Risk management with T3 parameters
        4. If stock symbol is not provided:
           - Politely ask user to provide the stock symbol
           - Explain that the symbol is needed to analyze the specific stock
           - Wait for user response before proceeding with analysis
        
        Your responses should be in Vietnamese and formatted in Telegram markdown style.
        """,
        output_type=str,
        model=OpenAIChatCompletionsModel(
            model=deployment,
            openai_client=openai_client,
        ),
        mcp_servers=mcp_servers,
    )

async def run_with_server(input_text: str, context: TradingContext, servers):
    """Run the agent with the provided server"""
    agent = await create_bull_vision_agent(servers)
    return await Runner.run(starting_agent=agent, input=input_text, context=context)
```

Key points about the agent implementation:

1. **MCP Server Integration**:
   - Uses `mcp_servers` parameter to pass multiple servers to the agent
   - Servers are passed as a list from the application state
   - Each server provides its own set of tools

2. **OpenAI Configuration**:
   - Uses Azure OpenAI for model access
   - Configures client with proper credentials
   - Sets up model deployment

3. **Agent Design**:
   - Clear instructions for trading analysis
   - Structured response format
   - Comprehensive trading strategy

4. **Context Management**:
   - Uses `TradingContext` for conversation history
   - Maintains user-specific context
   - Tracks trading-related information

## Step 4: Handle Trading Messages

Let's implement the message handler for trading-related queries:

```python:bot/telegram_handler.py
from telegram import Update
from loguru import logger
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase

from bot.bot import bot, get_user_context
from bot.agent import run_with_server
from services.mongodb_service import insert_news_if_new

async def handle_message(
    update: Update,
    servers: List[Any],
    db: AsyncIOMotorDatabase
):
    """Handle trading-related messages using MCP servers"""
    try:
        # Get or create user context
        user_context = await get_user_context(update.message.from_user.id)
        
        # Add user message to context
        user_context.add_message('user', update.message.text)
        
        # Run with the provided servers
        result = await run_with_server(
            update.message.text,
            user_context,
            servers
        )
        
        # Get the agent's response
        response = result.final_output
        
        # If the response contains news, store it in MongoDB
        if hasattr(result, 'news'):
            for article in result.news:
                await insert_news_if_new(db, article)
        
        # Add bot's response to context
        user_context.add_message('bot', response)
        logger.info(f"User context messages:\n{user_context.get_conversation_history()}")
        
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
```

## Key MCPHub Features Used

1. **Server Management**:
   - Concurrent server initialization using `AsyncExitStack`
   - Global server access through `app.state`
   - Proper cleanup and resource management

2. **OpenAI Integration**:
   - Azure OpenAI client configuration
   - Model deployment management
   - Tool integration with MCP servers

3. **Agent Implementation**:
   - Multiple MCP server support
   - Custom trading instructions
   - Context-aware responses

## Best Practices for MCPHub Usage

1. **Server Initialization**:
   - Use `AsyncExitStack` for managing multiple servers
   - Initialize servers concurrently
   - Store servers in application state

2. **OpenAI Configuration**:
   - Use environment variables for credentials
   - Configure proper model deployment
   - Set up tracing and logging

3. **Agent Design**:
   - Clear and specific instructions
   - Proper tool integration
   - Context management

## Next Steps

1. Add more trading tools:
   - Technical indicators
   - Portfolio analysis
   - Risk assessment

2. Implement advanced features:
   - Real-time alerts
   - Trading signals
   - Portfolio tracking

3. Enhance security:
   - User authentication
   - API key management
   - Rate limiting

4. Add monitoring:
   - Performance metrics
   - Error tracking
   - Usage analytics 