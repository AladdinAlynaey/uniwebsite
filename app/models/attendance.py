from app.models.base_model import BaseModel
from datetime import datetime

class Attendance(BaseModel):
    """Model for student attendance"""
    
    @classmethod
    def get_by_student(cls, student_id):
        """Get attendance records for a specific student"""
        attendance_records = cls.load_all()
        return [record for record in attendance_records if record.get('student_id') == student_id]
    
    @classmethod
    def get_by_subject(cls, subject_id):
        """Get attendance records for a specific subject"""
        attendance_records = cls.load_all()
        result = []
        
        for record in attendance_records:
            if record.get('subject_id') == subject_id:
                # Ensure lecture_number is consistently a string for comparison
                if 'lecture_number' in record and record['lecture_number'] is not None:
                    record['lecture_number'] = str(record['lecture_number'])
                result.append(record)
                
        return result
    
    @classmethod
    def get_by_student_and_subject(cls, student_id, subject_id):
        """Get attendance records for a specific student and subject"""
        attendance_records = cls.load_all()
        result = []
        
        for record in attendance_records:
            if record.get('student_id') == student_id and record.get('subject_id') == subject_id:
                # Ensure lecture_number is consistently a string for comparison
                if 'lecture_number' in record and record['lecture_number'] is not None:
                    record['lecture_number'] = str(record['lecture_number'])
                result.append(record)
                
        return result
    
    @classmethod
    def mark_attendance(cls, student_id, subject_id, lecture_number, is_present, is_excused=False):
        """Mark attendance for a student with improved error handling"""
        if not student_id or not subject_id or lecture_number is None:
            print("Error: Missing required parameters for marking attendance")
            return None
            
        try:
            # Validate student_id and subject_id
            if student_id == "null" or subject_id == "null":
                print("Error: Invalid student_id or subject_id")
                return None
                
            # Convert lecture_number to string for consistent comparison
            lecture_number = str(lecture_number)
                
            # First check if record exists
            attendance_records = cls.load_all()
            for i, record in enumerate(attendance_records):
                record_lecture_num = str(record.get('lecture_number')) if record.get('lecture_number') is not None else None
                if (record.get('student_id') == student_id and 
                    record.get('subject_id') == subject_id and
                    record_lecture_num == lecture_number):
                    # Update existing record
                    attendance_records[i]['is_present'] = is_present
                    attendance_records[i]['is_excused'] = is_excused
                    attendance_records[i]['updated_at'] = datetime.now().isoformat()
                    cls.save_all(attendance_records)
                    return attendance_records[i]
            
            # Create new record with timestamp
            now = datetime.now().isoformat()
            new_record = {
                'student_id': student_id,
                'subject_id': subject_id,
                'lecture_number': lecture_number,
                'is_present': is_present,
                'is_excused': is_excused,
                'created_at': now,
                'updated_at': now
            }
            return cls.create(new_record)
        except Exception as e:
            print(f"Error marking attendance: {str(e)}")
            return None