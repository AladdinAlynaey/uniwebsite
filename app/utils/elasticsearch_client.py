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


def migrate_hierarchy():
    """Create the university hierarchy (faculty, department, batch) and
    migrate existing students to the unified User model.
    
    This is idempotent — it only runs if the user index is empty or missing.
    """
    import uuid
    from werkzeug.security import generate_password_hash
    from datetime import datetime
    
    es = get_es_client()
    
    try:
        if not es.ping():
            print("⚠️  Elasticsearch not reachable. Skipping hierarchy migration.")
            return False
    except Exception:
        return False
    
    # Ensure all new indices exist
    new_indices = ['user', 'faculty', 'department', 'batch', 'teachersubject']
    for idx in new_indices:
        ensure_index(f"{ES_INDEX_PREFIX}{idx}")
    
    # Check if user index already has data → migration already ran
    user_index = f"{ES_INDEX_PREFIX}user"
    try:
        count = es.count(index=user_index)['count']
        if count > 0:
            print(f"  ⏭️  Hierarchy migration: already done ({count} users exist)")
            return True
    except Exception:
        pass
    
    print("\n  🏛️  Running hierarchy migration...")
    now = datetime.now().isoformat()
    
    # 1. Create default Super Admin
    admin_id = str(uuid.uuid4())
    es.index(index=user_index, id=admin_id, document={
        'id': admin_id,
        'email': 'admin@university.edu',
        'password_hash': generate_password_hash('alaadin123'),
        'name': 'University Admin',
        'role': 'super_admin',
        'is_active': True,
        'faculty_id': None,
        'department_id': None,
        'batch_id': None,
        'created_at': now,
        'updated_at': now
    })
    print("  ✅ Created Super Admin: admin@university.edu / alaadin123")
    
    # 2. Create default Faculty
    faculty_id = str(uuid.uuid4())
    faculty_index = f"{ES_INDEX_PREFIX}faculty"
    es.index(index=faculty_index, id=faculty_id, document={
        'id': faculty_id,
        'name': 'Faculty of AI & Information Technology',
        'code': 'AIIT',
        'description': 'Default faculty created during migration',
        'head_user_id': '',
        'created_at': now,
        'updated_at': now
    })
    print("  ✅ Created default Faculty: AIIT")
    
    # 3. Create default Department
    dept_id = str(uuid.uuid4())
    dept_index = f"{ES_INDEX_PREFIX}department"
    es.index(index=dept_index, id=dept_id, document={
        'id': dept_id,
        'name': 'Artificial Intelligence',
        'code': 'AI',
        'faculty_id': faculty_id,
        'faculty_name': 'Faculty of AI & Information Technology',
        'description': 'Default department created during migration',
        'created_at': now,
        'updated_at': now
    })
    print("  ✅ Created default Department: AI")
    
    # 4. Create default Batch
    batch_id = str(uuid.uuid4())
    batch_index = f"{ES_INDEX_PREFIX}batch"
    es.index(index=batch_index, id=batch_id, document={
        'id': batch_id,
        'name': 'AI Batch 2024',
        'code': 'AI-2024',
        'department_id': dept_id,
        'department_name': 'Artificial Intelligence',
        'faculty_id': faculty_id,
        'year': '2024',
        'rep_user_id': '',
        'created_at': now,
        'updated_at': now
    })
    print("  ✅ Created default Batch: AI-2024")
    
    # 5. Migrate existing students to User model
    student_index = f"{ES_INDEX_PREFIX}student"
    try:
        if es.indices.exists(index=student_index):
            result = es.search(
                index=student_index,
                body={"query": {"match_all": {}}, "size": 10000},
                request_timeout=30
            )
            
            student_count = 0
            for hit in result['hits']['hits']:
                student = hit['_source']
                student_name = student.get('name', 'Unknown Student')
                student_email = student.get('email', '')
                
                # Generate email if not present
                if not student_email:
                    safe_name = student_name.lower().replace(' ', '.').replace("'", '')
                    student_email = f"{safe_name}@student.university.edu"
                
                # Create user record
                user_id = str(uuid.uuid4())
                es.index(index=user_index, id=user_id, document={
                    'id': user_id,
                    'email': student_email,
                    'password_hash': generate_password_hash('student123'),
                    'name': student_name,
                    'role': 'student',
                    'is_active': True,
                    'faculty_id': faculty_id,
                    'department_id': dept_id,
                    'batch_id': batch_id,
                    'token': student.get('token', str(uuid.uuid4())[:8].upper()),
                    'major': student.get('major', ''),
                    'level': student.get('level', ''),
                    'phone': student.get('phone', ''),
                    'profile_image': student.get('profile_image', ''),
                    'original_student_id': student.get('id', hit['_id']),
                    'created_at': student.get('created_at', now),
                    'updated_at': now
                })
                student_count += 1
            
            print(f"  ✅ Migrated {student_count} students to User model")
    except Exception as e:
        print(f"  ⚠️  Student migration error: {e}")
    
    # 6. Add batch_id to existing subjects
    subject_index = f"{ES_INDEX_PREFIX}subject"
    try:
        if es.indices.exists(index=subject_index):
            result = es.search(
                index=subject_index,
                body={"query": {"match_all": {}}, "size": 10000},
                request_timeout=30
            )
            for hit in result['hits']['hits']:
                doc = hit['_source']
                if not doc.get('batch_id'):
                    es.update(index=subject_index, id=hit['_id'], body={
                        "doc": {
                            "batch_id": batch_id,
                            "faculty_id": faculty_id,
                            "department_id": dept_id
                        }
                    })
            print(f"  ✅ Added batch scoping to existing subjects")
    except Exception as e:
        print(f"  ⚠️  Subject scoping error: {e}")
    
    # 7. Add batch_id to existing attendance, grades, feedback
    for model_name in ['attendance', 'grade', 'feedback', 'news']:
        idx = f"{ES_INDEX_PREFIX}{model_name}"
        try:
            if es.indices.exists(index=idx):
                result = es.search(
                    index=idx,
                    body={"query": {"match_all": {}}, "size": 10000},
                    request_timeout=30
                )
                for hit in result['hits']['hits']:
                    doc = hit['_source']
                    if not doc.get('batch_id'):
                        es.update(index=idx, id=hit['_id'], body={
                            "doc": {"batch_id": batch_id, "faculty_id": faculty_id}
                        })
                print(f"  ✅ Added batch scoping to {model_name}")
        except Exception as e:
            print(f"  ⚠️  {model_name} scoping error: {e}")
    
    # Refresh all indices
    try:
        es.indices.refresh(index=f"{ES_INDEX_PREFIX}*")
    except Exception:
        pass
    
    print("  🎉 Hierarchy migration complete!")
    return True

