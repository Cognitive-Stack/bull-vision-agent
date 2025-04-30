import json
from typing import Any, List

from loguru import logger
from models.news import NewsArticle
from services.mongodb_service import insert_news_if_new
from motor.motor_asyncio import AsyncIOMotorDatabase

async def store_fetched_news(
    tool_call_output_item: Any,
    db: AsyncIOMotorDatabase
) -> List[NewsArticle]:
    """
    Extracts news articles from tool_call_output_item.output and stores new ones in MongoDB.
    Returns a list of newly inserted NewsArticle objects.
    """
    outer_json = json.loads(tool_call_output_item.output)
    # Parse the 'text' field inside
    news_result_items = json.loads(outer_json['text'])

    inserted_articles = []

    for item in news_result_items:
        for article_data in item.get("results", []):
            logger.info(f"article_data: \n{json.dumps(article_data, indent=2, ensure_ascii=False)}")
            try:
                article = NewsArticle(**article_data)
                inserted = await insert_news_if_new(db, article)
                if inserted:
                    inserted_articles.append(article)
            except Exception as e:
                # Optionally log or handle bad data
                logger.error(f"Error inserting news article: {str(e)}")
                continue

    return inserted_articles 