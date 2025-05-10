from motor.motor_asyncio import AsyncIOMotorDatabase

async def user_has_portfolio(user_id: int, db: AsyncIOMotorDatabase) -> bool:
    """
    Check if the user has a portfolio in the database.
    Returns True if portfolio exists, False otherwise.
    """
    portfolio = await db.portfolios.find_one({"user_id": user_id})
    return portfolio

async def setup_portfolio(
    user_id: int,
    db: AsyncIOMotorDatabase,
    symbols: list,
    weights: list,
):
    """
    Set up a portfolio for the user with provided symbols and weights.
    """
    portfolio_data = {
        "user_id": user_id,
        "symbols": symbols,
        "weights": weights,
    }
    await db.portfolios.update_one(
        {"user_id": user_id},
        {"$set": portfolio_data},
        upsert=True
    )

async def user_has_profile(user_id: int, db: AsyncIOMotorDatabase) -> bool:
    """
    Check if the user has a profile in the database.
    Returns True if profile exists, False otherwise.
    """
    profile = await db.profiles.find_one({"user_id": user_id})
    return profile

async def setup_profile(
    user_id: int,
    db: AsyncIOMotorDatabase,
    risk_tolerance: str,
    investment_horizon: str,
    investment_goals: str,
):
    """
    Set up a profile for the user with provided data.
    """
    profile_data = {
        "user_id": user_id,
        "risk_tolerance": risk_tolerance,
        "investment_horizon": investment_horizon,
        "investment_goals": investment_goals,
    }
    await db.profiles.update_one(
        {"user_id": user_id},
        {"$set": profile_data},
        upsert=True
    ) 