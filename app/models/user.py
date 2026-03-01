"""
User Model — Unified authentication for all roles.

Roles: super_admin, faculty_head, batch_rep, teacher, student
All users authenticate with email + password_hash.
Students can also use legacy tokens for backward compatibility.
"""

from app.models.base_model import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash
import uuid


class User(BaseModel):
    """Unified user model for all roles in the university system."""

    # Role constants
    ROLE_SUPER_ADMIN = 'super_admin'
    ROLE_FACULTY_HEAD = 'faculty_head'
    ROLE_BATCH_REP = 'batch_rep'
    ROLE_TEACHER = 'teacher'
    ROLE_STUDENT = 'student'

    ALL_ROLES = [ROLE_SUPER_ADMIN, ROLE_FACULTY_HEAD, ROLE_BATCH_REP, ROLE_TEACHER, ROLE_STUDENT]

    @classmethod
    def create_user(cls, email, password, name, role, **kwargs):
        """Create a new user with hashed password.
        
        Args:
            email: User email (unique)
            password: Plain text password (will be hashed)
            name: Display name
            role: One of the ROLE_* constants
            **kwargs: Additional fields (faculty_id, department_id, batch_id, etc.)
        
        Returns:
            dict: Created user record
        """
        # Check if email already exists
        existing = cls.find_by_email(email)
        if existing:
            return None

        data = {
            'email': email.lower().strip(),
            'password_hash': generate_password_hash(password),
            'name': name,
            'role': role,
            'is_active': True,
            'faculty_id': kwargs.get('faculty_id'),
            'department_id': kwargs.get('department_id'),
            'batch_id': kwargs.get('batch_id'),
            'phone': kwargs.get('phone', ''),
            'profile_image': kwargs.get('profile_image', ''),
        }

        # For students, generate a legacy token for backward compat
        if role == cls.ROLE_STUDENT:
            data['token'] = kwargs.get('token') or str(uuid.uuid4())[:8].upper()
            data['major'] = kwargs.get('major', '')
            data['level'] = kwargs.get('level', '')

        return cls.create(data)

    @classmethod
    def find_by_email(cls, email):
        """Find a user by email address.
        
        Args:
            email: Email to search for
            
        Returns:
            dict or None
        """
        if not email:
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
                    "query": {"term": {"email.keyword": email.lower().strip()}},
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
        except Exception as e:
            print(f"Error finding user by email: {e}")
            return None

    @classmethod
    def find_by_token(cls, token):
        """Find a student user by legacy token (backward compat).
        
        Args:
            token: Student access token
            
        Returns:
            dict or None
        """
        if not token:
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
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"token.keyword": token}},
                                {"term": {"role.keyword": cls.ROLE_STUDENT}}
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
        except Exception as e:
            print(f"Error finding user by token: {e}")
            return None

    @classmethod
    def check_password(cls, user, password):
        """Verify a password against the stored hash.
        
        Args:
            user: User dict with 'password_hash'
            password: Plain text password to check
            
        Returns:
            bool
        """
        if not user or not password:
            return False
        return check_password_hash(user.get('password_hash', ''), password)

    @classmethod
    def set_password(cls, user_id, new_password):
        """Set a new password for a user.
        
        Args:
            user_id: User ID
            new_password: New plain text password
            
        Returns:
            dict or None: Updated user
        """
        return cls.update(user_id, {
            'password_hash': generate_password_hash(new_password)
        })

    @classmethod
    def get_by_role(cls, role):
        """Get all users with a specific role.
        
        Args:
            role: Role string
            
        Returns:
            list: List of user dicts
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
                    "query": {"term": {"role.keyword": role}},
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
        """Get all users in a faculty."""
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
    def get_by_batch(cls, batch_id):
        """Get all users in a batch."""
        try:
            from app.utils.elasticsearch_client import get_es_client
            es = get_es_client()
            index = cls._get_index()

            if not es.indices.exists(index=index):
                return []

            result = es.search(
                index=index,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"batch_id.keyword": batch_id}},
                                {"term": {"role.keyword": cls.ROLE_STUDENT}}
                            ]
                        }
                    },
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
    def get_teachers_by_faculty(cls, faculty_id):
        """Get all teachers in a faculty."""
        try:
            from app.utils.elasticsearch_client import get_es_client
            es = get_es_client()
            index = cls._get_index()

            if not es.indices.exists(index=index):
                return []

            result = es.search(
                index=index,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"faculty_id.keyword": faculty_id}},
                                {"term": {"role.keyword": cls.ROLE_TEACHER}}
                            ]
                        }
                    },
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
