"""
BaseModel — Elasticsearch-backed data layer for UniWebsite.

Provides CRUD operations via Elasticsearch while maintaining the exact same
API as the original JSON-based implementation. All subclasses (Student, Subject,
Lecture, Attendance, Grade, Feedback, News, TelegramUser) work without changes.
"""

import uuid
import time
from datetime import datetime
from app.utils.elasticsearch_client import get_es_client, get_index_name, ensure_index


class BaseModel:
    """Base model for Elasticsearch data handling"""
    
    @classmethod
    def _get_index(cls):
        """Get the Elasticsearch index name for this model."""
        return get_index_name(cls.__name__)
    
    @classmethod
    def _ensure_index(cls):
        """Ensure the index exists for this model."""
        ensure_index(cls._get_index())
    
    @classmethod
    def load_all(cls):
        """Load all records from Elasticsearch.
        
        Returns:
            list: List of record dictionaries
        """
        try:
            es = get_es_client()
            index = cls._get_index()
            
            # Ensure index exists
            if not es.indices.exists(index=index):
                return []
            
            # Search for all documents, up to 10000
            result = es.search(
                index=index,
                body={"query": {"match_all": {}}, "size": 10000},
                request_timeout=30
            )
            
            records = []
            for hit in result['hits']['hits']:
                record = hit['_source']
                # Ensure 'id' field is present
                if 'id' not in record:
                    record['id'] = hit['_id']
                records.append(record)
            
            return records
            
        except Exception as e:
            print(f"Error loading {cls.__name__} from Elasticsearch: {e}")
            return []
    
    @classmethod
    def load_by_batch(cls, batch_id):
        """Load all records scoped to a specific batch.
        
        Args:
            batch_id: Batch ID to filter by
            
        Returns:
            list: Filtered records
        """
        if not batch_id:
            return []
        try:
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
                request_timeout=30
            )
            
            records = []
            for hit in result['hits']['hits']:
                record = hit['_source']
                if 'id' not in record:
                    record['id'] = hit['_id']
                records.append(record)
            return records
            
        except Exception as e:
            print(f"Error loading {cls.__name__} by batch: {e}")
            return []
    
    @classmethod
    def load_by_faculty(cls, faculty_id):
        """Load all records scoped to a specific faculty.
        
        Args:
            faculty_id: Faculty ID to filter by
            
        Returns:
            list: Filtered records
        """
        if not faculty_id:
            return []
        try:
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
                request_timeout=30
            )
            
            records = []
            for hit in result['hits']['hits']:
                record = hit['_source']
                if 'id' not in record:
                    record['id'] = hit['_id']
                records.append(record)
            return records
            
        except Exception as e:
            print(f"Error loading {cls.__name__} by faculty: {e}")
            return []
    
    @classmethod
    def load_by_department(cls, department_id):
        """Load all records scoped to a specific department.
        
        Args:
            department_id: Department ID to filter by
            
        Returns:
            list: Filtered records
        """
        if not department_id:
            return []
        try:
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
                request_timeout=30
            )
            
            records = []
            for hit in result['hits']['hits']:
                record = hit['_source']
                if 'id' not in record:
                    record['id'] = hit['_id']
                records.append(record)
            return records
            
        except Exception as e:
            print(f"Error loading {cls.__name__} by department: {e}")
            return []
    
    @classmethod
    def save_all(cls, data):
        """Save all records to Elasticsearch (full replace).
        
        This replaces all documents in the index with the provided data.
        Used by models that do bulk updates (Attendance, Grade).
        
        Args:
            data: List of record dictionaries
        """
        if not isinstance(data, list):
            if data is None:
                data = []
            else:
                data = [data]
        
        try:
            es = get_es_client()
            index = cls._get_index()
            cls._ensure_index()
            
            # Build a set of IDs in the new data
            new_ids = set()
            for record in data:
                if 'id' not in record:
                    record['id'] = str(uuid.uuid4())
                new_ids.add(record['id'])
            
            # Get existing document IDs
            existing_ids = set()
            try:
                if es.indices.exists(index=index):
                    result = es.search(
                        index=index,
                        body={"query": {"match_all": {}}, "_source": False, "size": 10000},
                        request_timeout=30
                    )
                    existing_ids = {hit['_id'] for hit in result['hits']['hits']}
            except Exception:
                pass
            
            # Delete documents that are no longer in the data
            ids_to_delete = existing_ids - new_ids
            for doc_id in ids_to_delete:
                try:
                    es.delete(index=index, id=doc_id, refresh=False)
                except Exception:
                    pass
            
            # Index all current documents
            from elasticsearch.helpers import bulk as es_bulk
            
            actions = []
            for record in data:
                actions.append({
                    "_index": index,
                    "_id": record['id'],
                    "_source": record
                })
            
            if actions:
                es_bulk(es, actions, raise_on_error=False, refresh='true')
            else:
                # If empty data, just refresh
                try:
                    es.indices.refresh(index=index)
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"Error saving {cls.__name__} to Elasticsearch: {e}")
            raise
    
    @classmethod
    def find_by_id(cls, id):
        """Find a record by ID.
        
        Args:
            id: The document ID
            
        Returns:
            dict or None: The record dictionary, or None if not found
        """
        try:
            es = get_es_client()
            index = cls._get_index()
            
            if not es.indices.exists(index=index):
                return None
            
            result = es.get(index=index, id=id)
            record = result['_source']
            if 'id' not in record:
                record['id'] = result['_id']
            return record
            
        except Exception:
            # Document not found or index doesn't exist
            return None
    
    @classmethod
    def create(cls, data):
        """Create a new record.
        
        Args:
            data: Record dictionary
            
        Returns:
            dict: The created record with generated ID and timestamps
        """
        try:
            es = get_es_client()
            index = cls._get_index()
            cls._ensure_index()
            
            # Generate ID if not provided
            if 'id' not in data:
                data['id'] = str(uuid.uuid4())
            
            # Add timestamps
            data['created_at'] = datetime.now().isoformat()
            data['updated_at'] = data['created_at']
            
            es.index(index=index, id=data['id'], document=data, refresh='true')
            return data
            
        except Exception as e:
            print(f"Error creating {cls.__name__} in Elasticsearch: {e}")
            raise
    
    @classmethod
    def update(cls, id, data):
        """Update an existing record.
        
        Args:
            id: The document ID
            data: Updated fields dictionary
            
        Returns:
            dict or None: The updated record, or None if not found
        """
        try:
            es = get_es_client()
            index = cls._get_index()
            
            # Check if document exists
            if not es.exists(index=index, id=id):
                return None
            
            # Get existing document
            existing = es.get(index=index, id=id)['_source']
            
            # Merge updates
            existing.update(data)
            existing['updated_at'] = datetime.now().isoformat()
            
            # Re-index the full document
            es.index(index=index, id=id, document=existing, refresh='true')
            return existing
            
        except Exception as e:
            print(f"Error updating {cls.__name__} in Elasticsearch: {e}")
            return None
    
    @classmethod
    def delete(cls, id):
        """Delete a record.
        
        Args:
            id: The document ID
            
        Returns:
            dict or None: The deleted record, or None if not found
        """
        try:
            es = get_es_client()
            index = cls._get_index()
            
            # Get the document first
            try:
                result = es.get(index=index, id=id)
                deleted = result['_source']
            except Exception:
                return None
            
            # Delete the document
            es.delete(index=index, id=id, refresh='true')
            return deleted
            
        except Exception as e:
            print(f"Error deleting {cls.__name__} from Elasticsearch: {e}")
            return None