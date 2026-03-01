from app.models.base_model import BaseModel

class Subject(BaseModel):
    """Model for subjects"""
    
    @classmethod
    def get_subjects_by_semester(cls, semester):
        """Get subjects for a specific semester"""
        subjects = cls.load_all()
        return [subject for subject in subjects if subject.get('semester') == semester]
    
    @classmethod
    def get_subject_details(cls, subject_id):
        """Get detailed information about a subject"""
        subject = cls.find_by_id(subject_id)
        if not subject:
            return None
            
        # You could enrich the subject with additional data here
        return subject 