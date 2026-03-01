from app.models.base_model import BaseModel
import uuid

class Student(BaseModel):
    """Model for students"""
    
    @classmethod
    def find_by_token(cls, token):
        """Find a student by their unique token"""
        students = cls.load_all()
        for student in students:
            if student.get('token') == token:
                return student
        return None
    
    @classmethod
    def generate_token(cls):
        """Generate a unique token for a student"""
        return str(uuid.uuid4())
    
    @classmethod
    def get_attendance(cls, student_id):
        """Get attendance records for a student"""
        from app.models.attendance import Attendance
        return Attendance.get_by_student(student_id)
    
    @classmethod
    def get_grades(cls, student_id):
        """Get grade records for a student"""
        from app.models.grade import Grade
        return Grade.get_by_student(student_id) 