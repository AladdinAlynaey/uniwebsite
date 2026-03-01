"""
Assignment Management Utility
Handles assignment CRUD operations and student submissions.

Uses Elasticsearch for persistence via the uniwebsite_assignments index.
"""

import os
from datetime import datetime
from app.models.student import Student
from app.utils.elasticsearch_client import get_es_client, ensure_index, ES_INDEX_PREFIX

ASSIGNMENTS_INDEX = f'{ES_INDEX_PREFIX}assignments'

# Default empty structure
DEFAULT_ASSIGNMENTS = {'final_projects': [], 'weekly_homework': [], 'presentations': []}


def _ensure_assignments_index():
    """Ensure the assignments index exists."""
    ensure_index(ASSIGNMENTS_INDEX)


def load_assignments():
    """Load all assignments from Elasticsearch."""
    try:
        es = get_es_client()
        _ensure_assignments_index()
        
        # Assignments are stored as a single document with ID 'assignments_data'
        if es.exists(index=ASSIGNMENTS_INDEX, id='assignments_data'):
            result = es.get(index=ASSIGNMENTS_INDEX, id='assignments_data')
            data = result['_source']
            # Ensure all categories exist
            if 'presentations' not in data:
                data['presentations'] = []
            if 'final_projects' not in data:
                data['final_projects'] = []
            if 'weekly_homework' not in data:
                data['weekly_homework'] = []
            return data
        
        return DEFAULT_ASSIGNMENTS.copy()
        
    except Exception as e:
        print(f"Error loading assignments from ES: {e}")
        return DEFAULT_ASSIGNMENTS.copy()


def save_assignments(assignments_data):
    """Save assignments to Elasticsearch."""
    try:
        es = get_es_client()
        _ensure_assignments_index()
        
        es.index(
            index=ASSIGNMENTS_INDEX,
            id='assignments_data',
            document=assignments_data,
            refresh='true'
        )
        return True
    except Exception as e:
        print(f"Error saving assignments to ES: {e}")
        return False


def get_all_assignments():
    """Get all assignments (final projects and weekly homework)"""
    return load_assignments()


def get_final_projects():
    """Get all final projects"""
    assignments = load_assignments()
    return assignments.get('final_projects', [])


def get_weekly_homework():
    """Get all weekly homework"""
    assignments = load_assignments()
    return assignments.get('weekly_homework', [])


def get_presentations():
    """Get all presentations"""
    assignments = load_assignments()
    return assignments.get('presentations', [])


def get_assignment_by_id(assignment_id, assignment_type='weekly_homework'):
    """Get specific assignment by ID"""
    assignments = load_assignments()
    items = assignments.get(assignment_type, [])
    
    for item in items:
        if item.get('id') == assignment_id:
            return item
    return None


def get_assignments_by_subject(subject_id):
    """Get all assignments for a specific subject"""
    assignments = load_assignments()
    
    final_projects = [p for p in assignments.get('final_projects', []) 
                     if p.get('subject_id') == subject_id]
    
    weekly_homework = [hw for hw in assignments.get('weekly_homework', []) 
                      if hw.get('subject_id') == subject_id]
    
    return {
        'final_projects': final_projects,
        'weekly_homework': weekly_homework
    }


def get_homework_by_week(subject_id, week):
    """Get homework for specific subject and week"""
    assignments = load_assignments()
    homework_list = assignments.get('weekly_homework', [])
    
    for hw in homework_list:
        if hw.get('subject_id') == subject_id and hw.get('week') == week:
            return hw
    return None


def create_assignment(assignment_type, data):
    """
    Create new assignment
    
    Args:
        assignment_type: 'final_projects', 'weekly_homework', or 'presentations'
        data: Assignment data dictionary
        
    Returns:
        dict: Created assignment or None if failed
    """
    assignments = load_assignments()
    
    if assignment_type not in ['final_projects', 'weekly_homework', 'presentations']:
        return None
    
    # Add metadata
    data['created_at'] = datetime.now().isoformat()
    
    # Add to list
    assignments[assignment_type].append(data)
    
    # Save
    if save_assignments(assignments):
        return data
    return None


def update_assignment(assignment_id, assignment_type, updated_data):
    """Update existing assignment"""
    assignments = load_assignments()
    items = assignments.get(assignment_type, [])
    
    for i, item in enumerate(items):
        if item.get('id') == assignment_id:
            items[i].update(updated_data)
            if save_assignments(assignments):
                return items[i]
            return None
    return None


def delete_assignment(assignment_id, assignment_type):
    """Delete assignment"""
    assignments = load_assignments()
    items = assignments.get(assignment_type, [])
    
    assignments[assignment_type] = [item for item in items 
                                    if item.get('id') != assignment_id]
    
    return save_assignments(assignments)


# Student Submission Functions

def get_student_submissions(student_id):
    """Get all submissions for a student"""
    student = Student.find_by_id(student_id)
    if not student:
        return None
    
    return student.get('assignments', {
        'final_projects': [],
        'weekly_homework': [],
        'presentations': []
    })


def get_student_submission(student_id, assignment_id, assignment_type='weekly_homework'):
    """Get specific submission for a student"""
    submissions = get_student_submissions(student_id)
    if not submissions:
        return None
    
    items = submissions.get(assignment_type, [])
    for item in items:
        if item.get('id') == assignment_id:
            return item
    return None


def update_submission_status(student_id, assignment_id, status, assignment_type='weekly_homework'):
    """
    Update submission status for a student
    
    Args:
        student_id: Student ID
        assignment_id: Assignment ID
        status: 'not_started', 'in_progress', 'done', 'graded'
        assignment_type: 'final_projects' or 'weekly_homework'
        
    Returns:
        bool: True if successful
    """
    student = Student.find_by_id(student_id)
    if not student:
        return False
    
    # Initialize assignments structure if not exists
    if 'assignments' not in student:
        student['assignments'] = {'final_projects': [], 'weekly_homework': [], 'presentations': []}
    
    # Find or create submission
    submissions = student['assignments'].get(assignment_type, [])
    submission = None
    
    for sub in submissions:
        if sub.get('id') == assignment_id:
            submission = sub
            break
    
    # If submission doesn't exist, create it
    if not submission:
        assignment = get_assignment_by_id(assignment_id, assignment_type)
        if not assignment:
            return False
        
        submission = {
            'id': assignment_id,
            'subject_id': assignment.get('subject_id'),
            'subject_name': assignment.get('subject_name'),
            'week': assignment.get('week'),
            'title': assignment.get('title'),
            'description': assignment.get('description'),
            'due_date': assignment.get('due_date'),
            'status': status,
            'submitted_at': None,
            'files': [],
            'grade': None,
            'feedback': None
        }
        submissions.append(submission)
    else:
        submission['status'] = status
    
    # Update student data
    student['assignments'][assignment_type] = submissions
    return Student.update(student_id, student)


def submit_assignment(student_id, assignment_id, files_data, assignment_type='weekly_homework'):
    """
    Submit assignment with files
    
    Args:
        student_id: Student ID
        assignment_id: Assignment ID
        files_data: List of file information dictionaries
        assignment_type: 'final_projects' or 'weekly_homework'
        
    Returns:
        bool: True if successful
    """
    student = Student.find_by_id(student_id)
    if not student:
        return False
    
    # Initialize assignments structure if not exists
    if 'assignments' not in student:
        student['assignments'] = {'final_projects': [], 'weekly_homework': [], 'presentations': []}
    
    # Find or create submission
    submissions = student['assignments'].get(assignment_type, [])
    submission = None
    
    for sub in submissions:
        if sub.get('id') == assignment_id:
            submission = sub
            break
    
    # If submission doesn't exist, create it
    if not submission:
        assignment = get_assignment_by_id(assignment_id, assignment_type)
        if not assignment:
            return False
        
        submission = {
            'id': assignment_id,
            'subject_id': assignment.get('subject_id'),
            'subject_name': assignment.get('subject_name'),
            'week': assignment.get('week'),
            'title': assignment.get('title'),
            'description': assignment.get('description'),
            'due_date': assignment.get('due_date'),
            'status': 'done',
            'submitted_at': datetime.now().isoformat(),
            'files': files_data,
            'grade': None,
            'feedback': None
        }
        submissions.append(submission)
    else:
        # Update existing submission
        submission['status'] = 'done'
        submission['submitted_at'] = datetime.now().isoformat()
        submission['files'].extend(files_data)
    
    # Update student data
    student['assignments'][assignment_type] = submissions
    return Student.update(student_id, student)


def grade_assignment(student_id, assignment_id, grade, feedback, assignment_type='weekly_homework'):
    """
    Grade a student's assignment
    
    Args:
        student_id: Student ID
        assignment_id: Assignment ID
        grade: Numeric grade
        feedback: Text feedback
        assignment_type: 'final_projects' or 'weekly_homework'
        
    Returns:
        bool: True if successful
    """
    student = Student.find_by_id(student_id)
    if not student or 'assignments' not in student:
        return False
    
    submissions = student['assignments'].get(assignment_type, [])
    
    for submission in submissions:
        if submission.get('id') == assignment_id:
            submission['grade'] = grade
            submission['feedback'] = feedback
            submission['status'] = 'graded'
            submission['graded_at'] = datetime.now().isoformat()
            
            student['assignments'][assignment_type] = submissions
            return Student.update(student_id, student)
    
    return False


def get_all_submissions_for_assignment(assignment_id, assignment_type='weekly_homework'):
    """Get all student submissions for a specific assignment"""
    all_students = Student.load_all()
    submissions = []
    
    for student in all_students:
        student_assignments = student.get('assignments', {})
        student_submissions = student_assignments.get(assignment_type, [])
        
        for sub in student_submissions:
            if sub.get('id') == assignment_id:
                submissions.append({
                    'student_id': student.get('id'),
                    'student_name': student.get('name'),
                    'submission': sub
                })
                break
    
    return submissions


def get_assignment_statistics(assignment_id, assignment_type='weekly_homework'):
    """Get statistics for an assignment"""
    submissions = get_all_submissions_for_assignment(assignment_id, assignment_type)
    
    total_students = len(Student.load_all())
    submitted = len([s for s in submissions if s['submission'].get('status') in ['done', 'graded']])
    in_progress = len([s for s in submissions if s['submission'].get('status') == 'in_progress'])
    graded = len([s for s in submissions if s['submission'].get('status') == 'graded'])
    
    return {
        'total_students': total_students,
        'submitted': submitted,
        'in_progress': in_progress,
        'not_started': total_students - submitted - in_progress,
        'graded': graded,
        'submission_rate': (submitted / total_students * 100) if total_students > 0 else 0
    }
