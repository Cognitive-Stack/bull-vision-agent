from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.news import NewsArticle


async def insert_news_if_new(db: AsyncIOMotorDatabase, article: NewsArticle) -> bool:
    """Insert news article if not already present (by URL). Returns True if inserted."""
    existing = await db.news.find_one({"url": article.url})
    if not existing:
        await db.news.insert_one(article.model_dump())
        return True
    return False
