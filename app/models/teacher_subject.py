"""
TeacherSubject Model — Links teachers to subjects in specific batches.

A teacher can be assigned to multiple subjects across multiple batches.
This determines what a teacher can see and manage.
"""

from app.models.base_model import BaseModel


class TeacherSubject(BaseModel):
    """Teacher-Subject assignment linking model."""

    @classmethod
    def assign(cls, teacher_id, subject_id, batch_id):
        """Assign a teacher to a subject in a batch.
        
        Returns:
            dict: The created assignment, or None if duplicate
        """
        # Check for existing assignment
        existing = cls.find_assignment(teacher_id, subject_id, batch_id)
        if existing:
            return existing

        return cls.create({
            'teacher_id': teacher_id,
            'subject_id': subject_id,
            'batch_id': batch_id
        })

    @classmethod
    def unassign(cls, teacher_id, subject_id, batch_id):
        """Remove a teacher-subject assignment.
        
        Returns:
            bool: True if deleted
        """
        assignment = cls.find_assignment(teacher_id, subject_id, batch_id)
        if assignment:
            cls.delete(assignment['id'])
            return True
        return False

    @classmethod
    def find_assignment(cls, teacher_id, subject_id, batch_id):
        """Find a specific assignment."""
        try:
            from app.utils.elasticsearch_client import get_es_client
            es = get_es_client()
            index = cls._get_index()

            if not es.indices.exists(index=index):
                return None

            result = es.search(
                index=index,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"teacher_id.keyword": teacher_id}},
                                {"term": {"subject_id.keyword": subject_id}},
                                {"term": {"batch_id.keyword": batch_id}}
                            ]
                        }
                    },
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
    def get_by_teacher(cls, teacher_id):
        """Get all subject assignments for a teacher.
        
        Returns:
            list: Assignment dicts with subject_id and batch_id
        """
        try:
            from app.utils.elasticsearch_client import get_es_client
            es = get_es_client()
            index = cls._get_index()

            if not es.indices.exists(index=index):
                return []

            result = es.search(
                index=index,
                body={
                    "query": {"term": {"teacher_id.keyword": teacher_id}},
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
    def get_by_subject(cls, subject_id):
        """Get all teacher assignments for a subject."""
        try:
            from app.utils.elasticsearch_client import get_es_client
            es = get_es_client()
            index = cls._get_index()

            if not es.indices.exists(index=index):
                return []

            result = es.search(
                index=index,
                body={
                    "query": {"term": {"subject_id.keyword": subject_id}},
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
    def get_by_batch(cls, batch_id):
        """Get all teacher-subject assignments in a batch."""
        try:
            from app.utils.elasticsearch_client import get_es_client
            es = get_es_client()
            index = cls._get_index()

            if not es.indices.exists(index=index):
                return []

            result = es.search(
                index=index,
                body={
                    "query": {"term": {"batch_id.keyword": batch_id}},
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
    def get_teacher_subjects_with_details(cls, teacher_id):
        """Get all subjects for a teacher with full subject and batch details.
        
        Returns:
            list: Dicts with teacher_subject, subject, and batch info
        """
        from app.models.subject import Subject
        from app.models.batch import Batch

        assignments = cls.get_by_teacher(teacher_id)
        detailed = []

        for assignment in assignments:
            subject = Subject.find_by_id(assignment.get('subject_id'))
            batch = Batch.find_by_id(assignment.get('batch_id'))
            
            if subject and batch:
                detailed.append({
                    'assignment_id': assignment['id'],
                    'subject': subject,
                    'batch': batch,
                    'subject_id': assignment['subject_id'],
                    'batch_id': assignment['batch_id']
                })

        return detailed
