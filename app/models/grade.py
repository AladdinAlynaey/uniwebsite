from app.models.base_model import BaseModel
from datetime import datetime

class Grade(BaseModel):
    """Model for student grades"""
    
    @classmethod
    def get_by_student(cls, student_id):
        """Get grade records for a specific student"""
        grade_records = cls.load_all()
        return [record for record in grade_records if record.get('student_id') == student_id]
    
    @classmethod
    def get_by_subject(cls, subject_id):
        """Get grade records for a specific subject"""
        grade_records = cls.load_all()
        return [record for record in grade_records if record.get('subject_id') == subject_id]
    
    @classmethod
    def get_by_student_and_subject(cls, student_id, subject_id):
        """Get grade records for a specific student and subject"""
        grade_records = cls.load_all()
        return [
            record for record in grade_records 
            if record.get('student_id') == student_id and record.get('subject_id') == subject_id
        ]
    
    @classmethod
    def set_grade(cls, student_id, subject_id, grade_type, grade_value):
        """Set a grade for a student with improved error handling"""
        if not student_id or not subject_id or not grade_type:
            print("Error: Missing required parameters for setting grade")
            return None
            
        try:
            # Validate student_id and subject_id
            if student_id == "null" or subject_id == "null":
                print("Error: Invalid student_id or subject_id")
                return None
                
            # Validate grade_value
            if grade_value is not None:
                # Convert to string for consistent storage
                grade_value = str(grade_value)
            else:
                grade_value = ""
            
            # First check if record exists
            grade_records = cls.load_all()
            for i, record in enumerate(grade_records):
                if (record.get('student_id') == student_id and 
                    record.get('subject_id') == subject_id and
                    record.get('grade_type') == grade_type):
                    # Update existing record
                    grade_records[i]['grade_value'] = grade_value
                    grade_records[i]['updated_at'] = datetime.now().isoformat()
                    cls.save_all(grade_records)
                    return grade_records[i]
            
            # Create new record with timestamp
            now = datetime.now().isoformat()
            new_record = {
                'student_id': student_id,
                'subject_id': subject_id,
                'grade_type': grade_type,
                'grade_value': grade_value,
                'created_at': now,
                'updated_at': now
            }
            return cls.create(new_record)
        except Exception as e:
            print(f"Error setting grade: {str(e)}")
            return None
    
    @classmethod
    def update_homework_grade(cls, grade_id, homework_grade):
        """Update homework grade and recalculate total"""
        grade_record = cls.find_by_id(grade_id)
        if not grade_record:
            return False
        
        # Update homework grade
        grade_record['homework'] = homework_grade
        
        # Recalculate total (homework: 10, midterm: 30, final: 60)
        homework = float(grade_record.get('homework', 0))
        midterm = float(grade_record.get('midterm', 0))
        final = float(grade_record.get('final', 0))
        
        # Homework is out of 10, midterm and final are out of 100
        # Total = homework + (midterm * 0.3) + (final * 0.6)
        total = homework + (midterm * 0.3) + (final * 0.6)
        grade_record['total'] = round(total, 2)
        
        return cls.update(grade_id, grade_record)