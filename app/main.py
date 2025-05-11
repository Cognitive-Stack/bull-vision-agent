import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from mcphub import MCPHub
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.telegram_webhook import router as telegram_router
from app.bot.bot import bot  # Import the bot instance
from app.core.settings import get_settings

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

        # Initialize user agents dictionary
        app.state.user_agents = {}
        logger.info("User agents dictionary initialized")

        # Create and maintain MCP servers connection
        servers = [hub.fetch_openai_mcp_server(mcp_name="search-stock-news", cache_tools_list=True),
                   hub.fetch_openai_mcp_server(mcp_name="volume-wall-detector", cache_tools_list=True)]
        async with contextlib.AsyncExitStack() as stack:
            app.state.mcp_servers = [await stack.enter_async_context(server) for server in servers]
            logger.info("MCP servers initialized")

            # Set webhook using the Bot instance
            webhook_url = settings.TELEGRAM_WEBHOOK_URL
            if not webhook_url:
                logger.error("TELEGRAM_WEBHOOK_URL not set in environment variables")
            else:
                await bot.set_webhook(url=webhook_url)
                logger.info(f"Successfully registered webhook URL: {webhook_url}")

            app.state.telegram_bot = bot  # Store the bot instance in app.state if needed
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
