"""
Department Model — Represents a department/major within a faculty.

Example: Computer Science, Electrical Engineering (under Faculty of Engineering)
"""

from app.models.base_model import BaseModel


class Department(BaseModel):
    """Department model for university hierarchy."""

    @classmethod
    def get_by_faculty(cls, faculty_id):
        """Get all departments in a faculty.
        
        Args:
            faculty_id: Faculty ID
            
        Returns:
            list: Department dicts
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
    def find_by_code(cls, code, faculty_id=None):
        """Find a department by code, optionally within a faculty.
        
        Args:
            code: Department code (e.g., 'CS', 'EE')
            faculty_id: Optional faculty ID to scope the search
            
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

            query = {"bool": {"must": [{"term": {"code.keyword": code.upper().strip()}}]}}
            if faculty_id:
                query["bool"]["must"].append({"term": {"faculty_id.keyword": faculty_id}})

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
    def get_with_stats(cls, faculty_id=None):
        """Get departments with batch/student counts.
        
        Args:
            faculty_id: Optional, filter by faculty
            
        Returns:
            list: Departments with stats
        """
        from app.models.batch import Batch
        from app.models.user import User

        if faculty_id:
            departments = cls.get_by_faculty(faculty_id)
        else:
            departments = cls.load_all()

        for dept in departments:
            batches = Batch.get_by_department(dept['id'])
            dept['batch_count'] = len(batches)
            student_count = 0
            for batch in batches:
                students = User.get_by_batch(batch['id'])
                student_count += len(students)
            dept['student_count'] = student_count

        return departments
