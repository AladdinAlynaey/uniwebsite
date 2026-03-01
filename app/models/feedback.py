from app.models.base_model import BaseModel
from datetime import datetime

class Feedback(BaseModel):
    """Model for student feedback and inquiries"""
    
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_RESOLVED = 'resolved'
    STATUS_ARCHIVED = 'archived'
    
    @classmethod
    def get_by_student(cls, student_id):
        """Get feedback records for a specific student"""
        feedback_records = cls.load_all()
        return [record for record in feedback_records if record.get('student_id') == student_id]
    
    @classmethod
    def get_by_status(cls, status):
        """Get feedback records by status"""
        feedback_records = cls.load_all()
        return [record for record in feedback_records if record.get('status') == status]
    
    @classmethod
    def add_reply(cls, feedback_id, reply_text, is_admin=True):
        """Add a reply to a feedback"""
        feedback = cls.find_by_id(feedback_id)
        if not feedback:
            return None
            
        if 'replies' not in feedback:
            feedback['replies'] = []
            
        reply = {
            'text': reply_text,
            'is_admin': is_admin,
            'timestamp': datetime.now().isoformat()
        }
        
        feedback['replies'].append(reply)
        return cls.update(feedback_id, feedback)
    
    @classmethod
    def update_status(cls, feedback_id, status):
        """Update the status of a feedback"""
        feedback = cls.find_by_id(feedback_id)
        if not feedback:
            return None
            
        feedback['status'] = status
        return cls.update(feedback_id, feedback) 