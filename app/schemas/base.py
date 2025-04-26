from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response schema"""
    status: str = Field(default="success", description="Response status")
    message: Optional[str] = Field(default=None, description="Response message")
    data: Optional[Any] = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class ErrorResponse(BaseResponse):
    """Error response schema"""
    status: str = Field(default="error", description="Error status")
    error_code: Optional[str] = Field(default=None, description="Error code")
    error_details: Optional[Any] = Field(default=None, description="Error details")

class BaseRequest(BaseModel):
    """Base request schema"""
    class Config:
        json_schema_extra = {
            "example": {
                "example_field": "example_value"
            }
        } 