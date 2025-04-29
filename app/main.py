from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.telegram_webhook import router as telegram_router
from app.startup import startup_event
from mcphub import MCPHub
from contextlib import asynccontextmanager
from loguru import logger

# Initialize MCPHub
hub = MCPHub()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        # Create and maintain MCP server connection
        async with hub.fetch_openai_mcp_server(
            mcp_name="search-stock-news",
            cache_tools_list=True
        ) as server:
            # Store server in app state
            app.state.mcp_server = server
            logger.info("MCP server initialized")
            
            # Initialize other components
            await startup_event()
            yield
            
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down MCP server")

app = FastAPI(
    title="Bull Vision Agent",
    lifespan=lifespan
)

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