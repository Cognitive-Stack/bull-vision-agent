from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.telegram_webhook import router as telegram_router
from app.startup import startup_event

app = FastAPI(title="Bull Vision Agent")

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

# Add startup event
app.add_event_handler("startup", startup_event) 