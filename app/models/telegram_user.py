from app.models.base_model import BaseModel

class TelegramUser(BaseModel):
    """Model for mapping Telegram chat_ids to student tokens"""
    
    @classmethod
    def find_by_chat_id(cls, chat_id):
        """Find a mapping by Telegram chat_id"""
        mappings = cls.load_all()
        for mapping in mappings:
            if mapping.get('chat_id') == chat_id:
                return mapping
        return None
    
    @classmethod
    def find_by_token(cls, token):
        """Find a mapping by student token"""
        mappings = cls.load_all()
        for mapping in mappings:
            if mapping.get('token') == token:
                return mapping
        return None
    
    @classmethod
    def link_chat_to_token(cls, chat_id, token):
        """Link a Telegram chat_id to a student token"""
        # Check if mapping already exists
        existing = cls.find_by_chat_id(chat_id)
        if existing:
            existing['token'] = token
            return cls.update(existing['id'], existing)
            
        # Create new mapping
        new_mapping = {
            'chat_id': chat_id,
            'token': token
        }
        return cls.create(new_mapping)
    
    @classmethod
    def get_all_chat_ids(cls):
        """Get all registered Telegram chat_ids"""
        mappings = cls.load_all()
        return [mapping.get('chat_id') for mapping in mappings if mapping.get('chat_id')] 