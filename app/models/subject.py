"""
Subject Model — Represents an academic subject/course.

Now includes batch scoping: subjects belong to a batch within a department and faculty.
"""

from app.models.base_model import BaseModel


class Subject(BaseModel):
    """Model for subjects"""
    
    @classmethod
    def get_subjects_by_semester(cls, semester, batch_id=None):
        """Get subjects for a specific semester, optionally scoped to a batch.
        
        Args:
            semester: Semester identifier
            batch_id: Optional batch ID to scope
            
        Returns:
            list: Matching subjects
        """
        if batch_id:
            subjects = cls.load_by_batch(batch_id)
        else:
            subjects = cls.load_all()
        return [subject for subject in subjects if subject.get('semester') == semester]
    
    @classmethod
    def get_subject_details(cls, subject_id):
        """Get detailed information about a subject"""
        subject = cls.find_by_id(subject_id)
        if not subject:
            return None
        return subject

    @classmethod
    def get_by_batch(cls, batch_id):
        """Get all subjects in a batch.
        
        Args:
            batch_id: Batch ID
            
        Returns:
            list: Subject dicts
        """
        return cls.load_by_batch(batch_id)
    
    @classmethod
    def get_by_faculty(cls, faculty_id):
        """Get all subjects in a faculty."""
        return cls.load_by_faculty(faculty_id)