from typing import Any, Dict, Optional

from app.schemas.base import BaseRequest, BaseResponse


class TelegramWebhookRequest(BaseRequest):
    """Schema for Telegram webhook request"""

    update_id: int
    message: Optional[Dict[str, Any]] = None
    edited_message: Optional[Dict[str, Any]] = None
    channel_post: Optional[Dict[str, Any]] = None
    edited_channel_post: Optional[Dict[str, Any]] = None
    inline_query: Optional[Dict[str, Any]] = None
    chosen_inline_result: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None
    shipping_query: Optional[Dict[str, Any]] = None
    pre_checkout_query: Optional[Dict[str, Any]] = None
    poll: Optional[Dict[str, Any]] = None
    poll_answer: Optional[Dict[str, Any]] = None


class TelegramWebhookResponse(BaseResponse):
    """Schema for Telegram webhook response"""

    data: Optional[Dict[str, Any]] = None
