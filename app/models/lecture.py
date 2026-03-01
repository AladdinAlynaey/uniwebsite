import json
import os
import uuid
from datetime import datetime
from app.models.base_model import BaseModel

class Lecture(BaseModel):
    """Lecture model for storing lecture information"""
    
    def __init__(self, id=None, subject_id=None, title=None, description=None, date=None, 
                 materials=None, assignments=None, created_at=None, updated_at=None, week=None):
        """Initialize a lecture object"""
        self.id = id or str(uuid.uuid4())
        self.subject_id = subject_id
        self.title = title
        self.description = description
        self.date = date
        self.materials = materials or []
        self.assignments = assignments or []
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or self.created_at
        self.week = week
    
    @classmethod
    def get_all(cls):
        """Get all lectures as objects"""
        lectures_data = cls.load_all()
        return [cls.from_dict(lecture_data) for lecture_data in lectures_data]
    
    @classmethod
    def get_lectures_by_subject(cls, subject_id):
        """Get all lectures for a specific subject"""
        lectures = cls.get_all()
        return [lecture for lecture in lectures if lecture.subject_id == subject_id]
    
    @classmethod
    def get_lectures_by_week(cls, week_number):
        """Get lectures for a specific week"""
        lectures = cls.get_all()
        return [lecture for lecture in lectures if getattr(lecture, 'week', None) == week_number]
    
    @classmethod
    def get_latest_lectures(cls, limit=5):
        """Get the latest lectures"""
        lectures = cls.get_all()
        # Sort by created_at in descending order
        sorted_lectures = sorted(
            lectures, 
            key=lambda x: x.created_at, 
            reverse=True
        )
        return sorted_lectures[:limit]
    
    def add_material(self, material):
        """Add a material to the lecture"""
        if not isinstance(material, LectureMaterial):
            raise TypeError("Material must be a LectureMaterial object")
        
        self.materials.append(material.__dict__)
        self.updated_at = datetime.now().isoformat()
        self.save()
        return True
    
    def add_assignment(self, assignment):
        """Add an assignment to the lecture"""
        if not hasattr(assignment, '__dict__'):
            raise TypeError("Assignment must be an object with __dict__ attribute")
        
        self.assignments.append(assignment.__dict__)
        self.updated_at = datetime.now().isoformat()
        self.save()
        return True
    
    def save(self):
        """Save the lecture to the data file"""
        data = self.to_dict()
        
        # Check if lecture already exists
        lectures_data = self.load_all()
        for i, lecture_data in enumerate(lectures_data):
            if lecture_data.get('id') == self.id:
                lectures_data[i] = data
                self.save_all(lectures_data)
                return True
        
        # If not, add it
        lectures_data.append(data)
        self.save_all(lectures_data)
        return True
    
    def to_dict(self):
        """Convert the lecture object to a dictionary"""
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'title': self.title,
            'description': self.description,
            'date': self.date,
            'materials': self.materials,
            'assignments': self.assignments,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'week': getattr(self, 'week', None),
            'file_name': getattr(self, 'file_name', None),
            'file_path': getattr(self, 'file_path', None)
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a lecture object from a dictionary"""
        lecture = cls(
            id=data.get('id'),
            subject_id=data.get('subject_id'),
            title=data.get('title'),
            description=data.get('description'),
            date=data.get('date'),
            materials=data.get('materials', []),
            assignments=data.get('assignments', []),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            week=data.get('week')
        )
        # Add file attributes if they exist
        if 'file_name' in data:
            lecture.file_name = data.get('file_name')
        if 'file_path' in data:
            lecture.file_path = data.get('file_path')
        return lecture
    
    @classmethod
    def find_by_id(cls, id):
        """Find a lecture by its ID"""
        lecture_data = super().find_by_id(id)
        if lecture_data:
            return cls.from_dict(lecture_data)
        return None
        
    @classmethod
    def delete(cls, id):
        """Delete a lecture by its ID"""
        lectures_data = cls.load_all()
        for i, lecture_data in enumerate(lectures_data):
            if lecture_data.get('id') == id:
                deleted_lecture = lectures_data.pop(i)
                cls.save_all(lectures_data)
                return deleted_lecture
        return None


class LectureMaterial:
    """Class for lecture materials"""
    
    def __init__(self, id=None, lecture_id=None, title=None, description=None, 
                 filename=None, file_type=None, created_at=None):
        """Initialize a lecture material object"""
        self.id = id or str(uuid.uuid4())
        self.lecture_id = lecture_id
        self.title = title
        self.description = description
        self.filename = filename
        self.file_type = file_type
        self.created_at = created_at or datetime.now().isoformat()
    
    @classmethod
    def find_by_id(cls, material_id):
        """Find a material by its ID"""
        lectures = Lecture.get_all()
        
        for lecture in lectures:
            for material in lecture.materials:
                if material.get('id') == material_id:
                    material_obj = cls(
                        id=material.get('id'),
                        lecture_id=lecture.id,
                        title=material.get('title'),
                        description=material.get('description'),
                        filename=material.get('filename'),
                        file_type=material.get('file_type'),
                        created_at=material.get('created_at')
                    )
                    return material_obj
        
        return None
    
    def save(self):
        """Save the material to its lecture"""
        lecture = Lecture.find_by_id(self.lecture_id)
        if not lecture:
            return False
        
        # Check if material already exists
        for i, material in enumerate(lecture.materials):
            if material.get('id') == self.id:
                lecture.materials[i] = self.__dict__
                lecture.save()
                return True
        
        # If not, add it
        lecture.add_material(self)
        return True
    
    def delete(self):
        """Delete the material"""
        lecture = Lecture.find_by_id(self.lecture_id)
        if not lecture:
            return False
        
        # Remove material from lecture
        lecture.materials = [m for m in lecture.materials if m.get('id') != self.id]
        lecture.save()
        
        # Delete the file if it exists
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                  'app', 'static', 'uploads')
        if self.filename:
            file_path = os.path.join(uploads_dir, self.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return True


class Assignment:
    """Class for assignments"""
    
    def __init__(self, id=None, lecture_id=None, title=None, description=None, 
                 due_date=None, points=None, created_at=None):
        """Initialize an assignment object"""
        self.id = id or str(uuid.uuid4())
        self.lecture_id = lecture_id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.points = points
        self.created_at = created_at or datetime.now().isoformat()
    
    @classmethod
    def find_by_id(cls, assignment_id):
        """Find an assignment by its ID"""
        lectures = Lecture.get_all()
        
        for lecture in lectures:
            for assignment in lecture.assignments:
                if assignment.get('id') == assignment_id:
                    assignment_obj = cls(
                        id=assignment.get('id'),
                        lecture_id=lecture.id,
                        title=assignment.get('title'),
                        description=assignment.get('description'),
                        due_date=assignment.get('due_date'),
                        points=assignment.get('points'),
                        created_at=assignment.get('created_at')
                    )
                    return assignment_obj
        
        return None
    
    def save(self):
        """Save the assignment to its lecture"""
        lecture = Lecture.find_by_id(self.lecture_id)
        if not lecture:
            return False
        
        # Check if assignment already exists
        for i, assignment in enumerate(lecture.assignments):
            if assignment.get('id') == self.id:
                lecture.assignments[i] = self.__dict__
                lecture.save()
                return True
        
        # If not, add it
        lecture.add_assignment(self)
        return True
    
    def delete(self):
        """Delete the assignment"""
        lecture = Lecture.find_by_id(self.lecture_id)
        if not lecture:
            return False
        
        # Remove assignment from lecture
        lecture.assignments = [a for a in lecture.assignments if a.get('id') != self.id]
        lecture.save()
        
        return True 