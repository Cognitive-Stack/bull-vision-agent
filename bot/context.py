from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Message:
    """Represents a single message in the conversation"""
    timestamp: datetime
    sender: str  # 'user' or 'bot'
    content: str

@dataclass
class TradingContext:
    """Context for tracking trading-related data and conversation history"""
    user_id: int
    current_date: datetime = field(default_factory=datetime.now)
    messages: List[Message] = field(default_factory=list)
    last_analysis: Optional[str] = None
    last_volume_data: Optional[dict] = None
    last_news_data: Optional[list] = None

    def add_message(self, sender: str, content: str) -> None:
        """Add a new message to the conversation history"""
        self.messages.append(Message(
            timestamp=datetime.now(),
            sender=sender,
            content=content
        ))

    def get_conversation_history(self) -> str:
        """Get formatted conversation history"""
        return "\n".join([
            f"{msg.sender}: {msg.content}"
            for msg in self.messages
        ]) 