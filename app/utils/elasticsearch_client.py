"""
Elasticsearch Client for UniWebsite
Handles connection, index management, and data migration from JSON files.
"""

import os
import json
import time
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# Elasticsearch connection
ES_HOST = os.environ.get('ES_HOST', 'http://localhost:9200')
ES_INDEX_PREFIX = 'uniwebsite_'

# Singleton client
_es_client = None


def get_es_client():
    """Get or create the Elasticsearch client singleton."""
    global _es_client
    if _es_client is None:
        _es_client = Elasticsearch(
            ES_HOST,
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
    return _es_client


def get_index_name(model_name):
    """Get the Elasticsearch index name for a model.
    
    Args:
        model_name: The model class name (e.g., 'Student', 'Lecture')
    
    Returns:
        str: Index name like 'uniwebsite_student'
    """
    return f"{ES_INDEX_PREFIX}{model_name.lower()}"


def ensure_index(index_name):
    """Create an index if it doesn't exist.
    
    Args:
        index_name: The Elasticsearch index name
    """
    es = get_es_client()
    if not es.indices.exists(index=index_name):
        es.indices.create(
            index=index_name,
            body={
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "index.max_result_window": 50000
                },
                "mappings": {
                    "dynamic": True,
                    "properties": {
                        "id": {"type": "keyword"},
                        "created_at": {"type": "keyword"},
                        "updated_at": {"type": "keyword"}
                    }
                }
            }
        )
        print(f"  ✅ Created index: {index_name}")


def migrate_json_to_es():
    """Migrate all JSON data files to Elasticsearch.
    
    This is idempotent — it skips indices that already have data.
    Called once during app initialization.
    """
    es = get_es_client()
    
    # Check if ES is reachable
    try:
        if not es.ping():
            print("⚠️  Elasticsearch is not reachable. Skipping migration.")
            return False
    except Exception as e:
        print(f"⚠️  Elasticsearch connection error: {e}. Skipping migration.")
        return False
    
    print("=" * 60)
    print("  📦 UniWebsite — Elasticsearch Data Migration")
    print("=" * 60)
    
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    
    # Models that use BaseModel (lowercase filename = classname)
    model_files = {
        'student': 'student.json',
        'lecture': 'lecture.json',
        'subject': 'subject.json',
        'attendance': 'attendance.json',
        'grade': 'grade.json',
        'feedback': 'feedback.json',
        'news': 'news.json',
        'telegramuser': 'telegramuser.json',
    }
    
    migrated_count = 0
    
    for model_name, json_file in model_files.items():
        index_name = f"{ES_INDEX_PREFIX}{model_name}"
        ensure_index(index_name)
        
        # Check if index already has data
        try:
            count = es.count(index=index_name)['count']
            if count > 0:
                print(f"  ⏭️  {index_name}: already has {count} documents, skipping")
                continue
        except Exception:
            pass
        
        # Load JSON data
        json_path = os.path.join(data_dir, json_file)
        if not os.path.exists(json_path):
            print(f"  ⏭️  {json_file}: file not found, skipping")
            continue
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            if not isinstance(records, list) or len(records) == 0:
                print(f"  ⏭️  {json_file}: empty or invalid, skipping")
                continue
            
            # Prepare bulk actions
            actions = []
            for record in records:
                doc_id = record.get('id')
                if not doc_id:
                    # Generate an ID for records without one
                    import uuid
                    doc_id = str(uuid.uuid4())
                    record['id'] = doc_id
                
                actions.append({
                    "_index": index_name,
                    "_id": doc_id,
                    "_source": record
                })
            
            # Bulk index
            success, errors = bulk(es, actions, raise_on_error=False)
            print(f"  ✅ {index_name}: migrated {success} documents")
            if errors:
                print(f"     ⚠️  {len(errors)} errors during migration")
            migrated_count += success
            
        except Exception as e:
            print(f"  ❌ {json_file}: migration failed: {e}")
    
    # Migrate assignments (separate structure)
    _migrate_assignments(es, data_dir)
    
    # Refresh all indices
    try:
        es.indices.refresh(index=f"{ES_INDEX_PREFIX}*")
    except Exception:
        pass
    
    print(f"\n  📊 Total documents migrated: {migrated_count}")
    print("=" * 60)
    return True


def _migrate_assignments(es, data_dir):
    """Migrate assignments data (separate JSON structure) to ES."""
    index_name = f"{ES_INDEX_PREFIX}assignments"
    ensure_index(index_name)
    
    # Check if already migrated
    try:
        count = es.count(index=index_name)['count']
        if count > 0:
            print(f"  ⏭️  {index_name}: already has {count} documents, skipping")
            return
    except Exception:
        pass
    
    # Assignments file is in app/data/ not data/
    assignments_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'data', 'assignments.json'
    )
    
    if not os.path.exists(assignments_path):
        print(f"  ⏭️  assignments.json: file not found, skipping")
        return
    
    try:
        with open(assignments_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Store as a single document with a known ID
        es.index(
            index=index_name,
            id='assignments_data',
            document=data
        )
        print(f"  ✅ {index_name}: migrated assignments data")
    except Exception as e:
        print(f"  ❌ assignments.json: migration failed: {e}")
