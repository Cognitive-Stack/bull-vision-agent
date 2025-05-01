from contextlib import asynccontextmanager
import contextlib

from fastapi import Depends, FastAPI
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
        servers = [hub.fetch_openai_mcp_server(mcp_name="search-stock-news", cache_tools_list=True),
                   hub.fetch_openai_mcp_server(mcp_name="volume-wall-detector", cache_tools_list=True)]
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
