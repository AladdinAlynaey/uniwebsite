from app.models.base_model import BaseModel
from datetime import datetime

class News(BaseModel):
    """Model for news items"""
    
    @classmethod
    def get_latest_news(cls, limit=10):
        """Get the latest news items"""
        news_items = cls.load_all()
        # Sort by created_at in descending order
        sorted_news = sorted(
            news_items, 
            key=lambda x: datetime.fromisoformat(x.get('created_at')), 
            reverse=True
        )
        return sorted_news[:limit]
    
    @classmethod
    def search_news(cls, query):
        """Search news items by title or content"""
        news_items = cls.load_all()
        query = query.lower()
        return [
            item for item in news_items 
            if query in item.get('title', '').lower() or query in item.get('content', '').lower()
        ] 