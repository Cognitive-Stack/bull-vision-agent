from motor.motor_asyncio import AsyncIOMotorDatabase

async def user_has_portfolio(user_id: int, db: AsyncIOMotorDatabase) -> bool:
    """
    Check if the user has a portfolio in the database.
    Returns True if portfolio exists, False otherwise.
    """
    portfolio = await db.portfolios.find_one({"user_id": user_id})
    return portfolio if portfolio is not None else None

async def setup_portfolio(
    user_id: int,
    db: AsyncIOMotorDatabase,
    portfolio_size: int,
    current_exposure: str,
    strategy_preference: str,
    goal: str,
    max_hold_per_swing: str
):
    """
    Set up a portfolio for the user with provided data.
    """
    portfolio_data = {
        "user_id": user_id,
        "portfolio_size": portfolio_size,
        "current_exposure": current_exposure,
        "strategy_preference": strategy_preference,
        "goal": goal,
        "max_hold_per_swing": max_hold_per_swing
    }
    await db.portfolios.update_one(
        {"user_id": user_id},
        {"$set": portfolio_data},
        upsert=True
    ) 