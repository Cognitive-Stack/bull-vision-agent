from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class Message:
    """Represents a single message in the conversation"""

    timestamp: datetime
    sender: str  # 'user' or 'bot'
    content: str


@dataclass
class InvestorProfile:
    """Represents an investor's profile and preferences"""
    risk_tolerance: str  # 'conservative', 'moderate', 'aggressive'
    investment_horizon: str  # 'short_term', 'medium_term', 'long_term'
    investment_goals: List[str]  # e.g., ['growth', 'dividend', 'value']
    preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Portfolio:
    """Represents a user's investment portfolio"""
    symbols: List[str]
    weights: Dict[str, float]
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class TradingContext:
    """Context for tracking trading-related data and conversation history"""

    user_id: int
    current_date: datetime = field(default_factory=datetime.now)
    messages: List[Message] = field(default_factory=list)
    portfolio: Optional[Portfolio] = None
    investor_profile: Optional[InvestorProfile] = None
    last_analysis: Optional[str] = None
    last_volume_data: Optional[dict] = None
    last_news_data: Optional[list] = None

    def add_message(self, sender: str, content: str) -> None:
        """Add a new message to the conversation history"""
        self.messages.append(
            Message(timestamp=datetime.now(), sender=sender, content=content)
        )

    def get_conversation_history(self) -> str:
        """Get formatted conversation history"""
        return "\n".join([f"{msg.sender}: {msg.content}" for msg in self.messages])

    def update_portfolio(self, symbols: List[str], weights: Dict[str, float]) -> None:
        """Update the user's portfolio"""
        self.portfolio = Portfolio(
            symbols=symbols,
            weights=weights,
            last_updated=datetime.now()
        )

    def update_investor_profile(self, risk_tolerance: str, investment_horizon: str, 
                              investment_goals: List[str], preferences: Dict[str, Any] = None) -> None:
        """Update the user's investor profile"""
        self.investor_profile = InvestorProfile(
            risk_tolerance=risk_tolerance,
            investment_horizon=investment_horizon,
            investment_goals=investment_goals,
            preferences=preferences or {}
        )

# Dictionary to store user contexts
user_contexts: Dict[int, TradingContext] = {}

def get_user_context(user_id: int) -> Optional[TradingContext]:
    """Get a user's trading context"""
    return user_contexts.get(user_id)

def update_user_context(user_id: int, context_data: Dict[str, Any]) -> None:
    """Update a user's trading context"""
    if user_id not in user_contexts:
        user_contexts[user_id] = TradingContext(user_id=user_id)
    
    context = user_contexts[user_id]
    
    if 'portfolio' in context_data:
        portfolio = context_data['portfolio']
        symbols = list(portfolio.keys())
        weights = portfolio
        context.update_portfolio(symbols, weights)
    
    if 'investor_profile' in context_data:
        profile = context_data['investor_profile']
        context.update_investor_profile(
            risk_tolerance=profile.get('risk_tolerance', 'moderate'),
            investment_horizon=profile.get('investment_horizon', 'medium_term'),
            investment_goals=profile.get('investment_goals', ['growth']),
            preferences=profile.get('preferences', {})
        )
