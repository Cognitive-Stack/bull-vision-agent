from fastapi import APIRouter, Request, HTTPException
from bot.telegram_handler import handle_telegram_update
from app.schemas.telegram import TelegramWebhookRequest, TelegramWebhookResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/telegram/webhook", response_model=TelegramWebhookResponse)
async def telegram_webhook(request: Request):
    try:
        update = await request.json()
        # Validate request data
        webhook_request = TelegramWebhookRequest(**update)
        await handle_telegram_update(update)
        return TelegramWebhookResponse(
            message="Webhook processed successfully",
            data={"update_id": webhook_request.update_id}
        )
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 