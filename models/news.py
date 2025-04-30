from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional

class NewsArticle(BaseModel):
    title: str
    url: str
    content: str
    score: float
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    source: Optional[str] = None
    notified: bool = False
    created_at: datetime = Field(default_factory=datetime.now) 