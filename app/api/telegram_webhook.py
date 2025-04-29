from fastapi import APIRouter, HTTPException, Request, Depends
from loguru import logger

from app.schemas.telegram import TelegramWebhookRequest, TelegramWebhookResponse
from bot.telegram_handler import handle_telegram_update
from bot.agent import run_with_server
from telegram import Update

router = APIRouter()

async def get_mcp_server(request: Request):
    return request.app.state.mcp_server

@router.post("/telegram/webhook", response_model=TelegramWebhookResponse)
async def telegram_webhook(
    request: Request,
    server = Depends(get_mcp_server)
):
    try:
        update = await request.json()
        # Validate request data
        webhook_request = TelegramWebhookRequest(**update)
        await handle_telegram_update(update, server)
        return TelegramWebhookResponse(
            message="Webhook processed successfully",
            data={"update_id": webhook_request.update_id}
        )
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 