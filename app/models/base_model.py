import json
import os
import shutil
import uuid
from datetime import datetime
import time
import random

class BaseModel:
    """Base model for JSON data handling"""
    
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    
    @classmethod
    def get_data_file_path(cls):
        """Get the path to the JSON data file for this model"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        return os.path.join(cls.DATA_DIR, f"{cls.__name__.lower()}.json")
    
    @classmethod
    def load_all(cls):
        """Load all records from the JSON file with improved error handling"""
        try:
            with open(cls.get_data_file_path(), 'r') as f:
                data = json.load(f)
                # Validate that we have a list of records
                if not isinstance(data, list):
                    print(f"Warning: {cls.__name__} data file contains invalid format. Resetting to empty list.")
                    return []
                return data
        except FileNotFoundError:
            # File doesn't exist yet, return empty list
            return []
        except json.JSONDecodeError as e:
            # JSON is malformed, log error and return empty list
            print(f"Error: {cls.__name__} data file is corrupted. {str(e)}. Resetting to empty list.")
            # Create a backup of the corrupted file
            try:
                backup_path = f"{cls.get_data_file_path()}.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                shutil.copy2(cls.get_data_file_path(), backup_path)
                print(f"Created backup of corrupted file at {backup_path}")
            except Exception as backup_error:
                print(f"Failed to create backup: {str(backup_error)}")
            return []
    
    @classmethod
    def save_all(cls, data):
        """Save all records to the JSON file using atomic write pattern"""
        # Validate data is a list
        if not isinstance(data, list):
            print(f"Warning: Attempting to save non-list data to {cls.__name__} file. Converting to list.")
            if data is None:
                data = []
            else:
                data = [data]
        
        # Create a temporary file
        temp_file = f"{cls.get_data_file_path()}.{time.time()}.{random.randint(1000, 9999)}.tmp"
        try:
            # Write to temp file first
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                # Ensure the write is flushed to disk
                f.flush()
                os.fsync(f.fileno())
            
            # Rename temp file to target file (atomic operation on most filesystems)
            os.replace(temp_file, cls.get_data_file_path())
        except Exception as e:
            print(f"Error saving {cls.__name__} data: {str(e)}")
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            raise
    
    @classmethod
    def find_by_id(cls, id):
        """Find a record by ID"""
        records = cls.load_all()
        for record in records:
            if record.get('id') == id:
                return record
        return None
    
    @classmethod
    def create(cls, data):
        """Create a new record"""
        records = cls.load_all()
        
        # Generate ID if not provided
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        
        # Add timestamps
        data['created_at'] = datetime.now().isoformat()
        data['updated_at'] = data['created_at']
        
        records.append(data)
        cls.save_all(records)
        return data
    
    @classmethod
    def update(cls, id, data):
        """Update an existing record"""
        records = cls.load_all()
        for i, record in enumerate(records):
            if record.get('id') == id:
                # Update the record
                records[i].update(data)
                records[i]['updated_at'] = datetime.now().isoformat()
                cls.save_all(records)
                return records[i]
        return None
    
    @classmethod
    def delete(cls, id):
        """Delete a record"""
        records = cls.load_all()
        for i, record in enumerate(records):
            if record.get('id') == id:
                deleted = records.pop(i)
                cls.save_all(records)
                return deleted
        return None 