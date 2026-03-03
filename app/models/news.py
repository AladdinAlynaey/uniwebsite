from app.models.base_model import BaseModel
from datetime import datetime

class News(BaseModel):
    """Model for news items — supports faculty/batch scoping."""
    
    @classmethod
    def get_latest_news(cls, limit=10, faculty_id=None, batch_id=None):
        """Get the latest news items, optionally filtered by faculty or batch."""
        news_items = cls.load_all()
        
        if faculty_id:
            news_items = [n for n in news_items 
                         if n.get('faculty_id') == faculty_id or not n.get('faculty_id')]
        
        if batch_id:
            news_items = [n for n in news_items 
                         if n.get('batch_id') == batch_id or not n.get('batch_id')]
        
        # Sort by created_at in descending order
        sorted_news = sorted(
            news_items, 
            key=lambda x: datetime.fromisoformat(x.get('created_at', '2000-01-01T00:00:00')), 
            reverse=True
        )
        return sorted_news[:limit]
    
    @classmethod
    def get_by_faculty(cls, faculty_id):
        """Get all news for a specific faculty."""
        all_news = cls.load_all()
        return [n for n in all_news if n.get('faculty_id') == faculty_id]
    
    @classmethod
    def get_by_batch(cls, batch_id):
        """Get all news for a specific batch."""
        all_news = cls.load_all()
        return [n for n in all_news if n.get('batch_id') == batch_id]
    
    @classmethod
    def search_news(cls, query):
        """Search news items by title or content"""
        news_items = cls.load_all()
        query = query.lower()
        return [
            item for item in news_items 
            if query in item.get('title', '').lower() or query in item.get('content', '').lower()
        ]