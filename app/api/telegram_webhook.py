from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger

from app.bot.telegram_handler import handle_telegram_update
from app.schemas.telegram import TelegramWebhookRequest, TelegramWebhookResponse

router = APIRouter()


async def get_mcp_server(request: Request):
    return request.app.state.mcp_server


async def get_mongo_db(request: Request):
    return request.app.state.mongo_db


@router.post("/telegram/webhook", response_model=TelegramWebhookResponse)
async def telegram_webhook(
    request: Request, server=Depends(get_mcp_server), db=Depends(get_mongo_db)
):
    try:
        update = await request.json()
        # Validate request data
        webhook_request = TelegramWebhookRequest(**update)
        await handle_telegram_update(update, server, db)
        return TelegramWebhookResponse(
            message="Webhook processed successfully",
            data={"update_id": webhook_request.update_id},
        )
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
