from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


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
