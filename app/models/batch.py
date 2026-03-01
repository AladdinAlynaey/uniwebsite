"""
Batch Model — Represents a student batch/cohort within a department.

Example: CS-2024, CS-2025 (under Computer Science department)
Each batch has a representative who manages it (like the current admin role).
"""

from app.models.base_model import BaseModel


class Batch(BaseModel):
    """Batch model for university hierarchy."""

    @classmethod
    def get_by_department(cls, department_id):
        """Get all batches in a department.
        
        Args:
            department_id: Department ID
            
        Returns:
            list: Batch dicts
        """
        if not department_id:
            return []
        try:
            from app.utils.elasticsearch_client import get_es_client
            es = get_es_client()
            index = cls._get_index()

            if not es.indices.exists(index=index):
                return []

            result = es.search(
                index=index,
                body={
                    "query": {"term": {"department_id.keyword": department_id}},
                    "size": 10000
                },
                request_timeout=10
            )

            records = []
            for hit in result['hits']['hits']:
                record = hit['_source']
                if 'id' not in record:
                    record['id'] = hit['_id']
                records.append(record)
            return records
        except Exception:
            return []

    @classmethod
    def get_by_faculty(cls, faculty_id):
        """Get all batches in a faculty.
        
        Args:
            faculty_id: Faculty ID
            
        Returns:
            list: Batch dicts
        """
        if not faculty_id:
            return []
        try:
            from app.utils.elasticsearch_client import get_es_client
            es = get_es_client()
            index = cls._get_index()

            if not es.indices.exists(index=index):
                return []

            result = es.search(
                index=index,
                body={
                    "query": {"term": {"faculty_id.keyword": faculty_id}},
                    "size": 10000
                },
                request_timeout=10
            )

            records = []
            for hit in result['hits']['hits']:
                record = hit['_source']
                if 'id' not in record:
                    record['id'] = hit['_id']
                records.append(record)
            return records
        except Exception:
            return []

    @classmethod
    def find_by_code(cls, code, department_id=None):
        """Find a batch by code.
        
        Args:
            code: Batch code (e.g., 'CS-2024')
            department_id: Optional department to scope search
            
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

            query = {"bool": {"must": [{"term": {"code.keyword": code.strip()}}]}}
            if department_id:
                query["bool"]["must"].append({"term": {"department_id.keyword": department_id}})

            result = es.search(
                index=index,
                body={"query": query, "size": 1},
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
    def get_with_stats(cls, department_id=None, faculty_id=None):
        """Get batches with student/subject counts.
        
        Args:
            department_id: Optional, filter by department
            faculty_id: Optional, filter by faculty
            
        Returns:
            list: Batches with stats
        """
        from app.models.user import User
        from app.models.subject import Subject

        if department_id:
            batches = cls.get_by_department(department_id)
        elif faculty_id:
            batches = cls.get_by_faculty(faculty_id)
        else:
            batches = cls.load_all()

        for batch in batches:
            students = User.get_by_batch(batch['id'])
            batch['student_count'] = len(students)

            subjects = Subject.get_by_batch(batch['id'])
            batch['subject_count'] = len(subjects)

        return batches
