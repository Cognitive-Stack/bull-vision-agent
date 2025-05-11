from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger
from telegram import Update

from app.schemas.telegram import TelegramWebhookRequest, TelegramWebhookResponse
from app.services.telegram import telegram_handler

router = APIRouter()

async def get_mcp_server(request: Request):
    return request.app.state.mcp_servers

async def get_mongo_db(request: Request):
    return request.app.state.mongo_db

async def get_telegram_bot(request: Request):
    return request.app.state.telegram_bot

async def get_user_agents(request: Request):
    return request.app.state.user_agents

@router.post("/telegram/webhook", response_model=TelegramWebhookResponse)
async def telegram_webhook(
    request: Request,
    servers=Depends(get_mcp_server),
    db=Depends(get_mongo_db),
    telegram_bot=Depends(get_telegram_bot),
    user_agents=Depends(get_user_agents),
):
    try:
        # Set MCP servers in the handler
        telegram_handler.set_mcp_servers(servers)
        
        update = await request.json()
        # Validate request data
        webhook_request = TelegramWebhookRequest(**update)
        
        # Pass db and user_agents to handle_update
        await telegram_handler.handle_update(Update.de_json(update, telegram_bot), None, db, user_agents)
        
        return TelegramWebhookResponse(
            message="Webhook processed successfully",
            data={"update_id": webhook_request.update_id},
        )
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
