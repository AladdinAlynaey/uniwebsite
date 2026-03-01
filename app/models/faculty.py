"""
Faculty Model — Represents a faculty/college in the university.

Example: Faculty of Engineering, Faculty of Science, Faculty of Arts
"""

from app.models.base_model import BaseModel


class Faculty(BaseModel):
    """Faculty model for university hierarchy."""

    @classmethod
    def find_by_code(cls, code):
        """Find a faculty by its unique code.
        
        Args:
            code: Faculty code (e.g., 'ENG', 'SCI')
            
        Returns:
            dict or None
        """
        if not code:
            return None
        try:
            from app.utils.elasticsearch_client import get_es_client
            es = get_es_client()
            index = cls._get_index()

            if not es.indices.exists(index=index):
                return None

            result = es.search(
                index=index,
                body={
                    "query": {"term": {"code.keyword": code.upper().strip()}},
                    "size": 1
                },
                request_timeout=10
            )

            if result['hits']['total']['value'] > 0:
                record = result['hits']['hits'][0]['_source']
                if 'id' not in record:
                    record['id'] = result['hits']['hits'][0]['_id']
                return record
            return None
        except Exception:
            return None

    @classmethod
    def get_with_stats(cls):
        """Get all faculties with department/batch/student counts.
        
        Returns:
            list: Faculties with stats
        """
        from app.models.department import Department
        from app.models.batch import Batch
        from app.models.user import User

        faculties = cls.load_all()
        for faculty in faculties:
            fid = faculty.get('id')
            departments = Department.get_by_faculty(fid)
            faculty['department_count'] = len(departments)

            batch_count = 0
            student_count = 0
            for dept in departments:
                batches = Batch.get_by_department(dept['id'])
                batch_count += len(batches)
                for batch in batches:
                    students = User.get_by_batch(batch['id'])
                    student_count += len(students)

            faculty['batch_count'] = batch_count
            faculty['student_count'] = student_count

        return faculties
