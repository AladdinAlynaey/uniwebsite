import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# n8n webhook URL
N8N_WEBHOOK_URL = "https://alaadin8n.duckdns.org/webhook/39ae4139-484e-4219-be17-28e4e5cc4270"

# n8n webhook URL for assignments
N8N_ASSIGNMENT_WEBHOOK_URL = "https://alaadin8n.duckdns.org/webhook/923b2156-4dee-44a6-ba27-7c9ccc154a57"

def send_news_webhook(news_item, action="created", original_data=None):
    """
    Send news data to n8n webhook
    
    Args:
        news_item (dict): The news item data (current/new data)
        action (str): The action performed ("created", "updated", "deleted")
        original_data (dict): The original data before update (only for "updated" action)
    
    Returns:
        bool: True if webhook was sent successfully, False otherwise
    """
    try:
        # Prepare webhook payload
        payload = {
            "event_type": "news_update",
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "id": news_item.get("id"),
                "title": news_item.get("title"),
                "content": news_item.get("content"),
                "created_at": news_item.get("created_at"),
                "updated_at": news_item.get("updated_at", news_item.get("created_at"))
            }
        }
        
        # Add original data for updates to show what changed
        if action == "updated" and original_data:
            payload["original_data"] = {
                "id": original_data.get("id"),
                "title": original_data.get("title"),
                "content": original_data.get("content"),
                "created_at": original_data.get("created_at"),
                "updated_at": original_data.get("updated_at", original_data.get("created_at"))
            }
            
            # Add changes summary
            changes = []
            if original_data.get("title") != news_item.get("title"):
                changes.append("title")
            if original_data.get("content") != news_item.get("content"):
                changes.append("content")
            
            payload["changes"] = changes
        
        # Send POST request to n8n webhook
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "UniWeb-Platform/1.0"
            },
            timeout=10  # 10 second timeout
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        logger.info(f"Successfully sent news webhook for {action} action. News ID: {news_item.get('id')}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send news webhook: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending news webhook: {e}")
        return False

def send_lecture_webhook(lecture_item, action="created"):
    """
    Send lecture data to n8n webhook (optional - for future use)
    
    Args:
        lecture_item (dict): The lecture item data
        action (str): The action performed ("created", "updated", "deleted")
    
    Returns:
        bool: True if webhook was sent successfully, False otherwise
    """
    try:
        # Prepare webhook payload
        payload = {
            "event_type": "lecture_update",
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "id": lecture_item.get("id"),
                "subject_id": lecture_item.get("subject_id"),
                "subject_name": lecture_item.get("subject_name"),
                "week": lecture_item.get("week"),
                "lecture_type": lecture_item.get("lecture_type"),
                "description": lecture_item.get("description"),
                "file_name": lecture_item.get("file_name"),
                "created_at": lecture_item.get("created_at"),
                "updated_at": lecture_item.get("updated_at", lecture_item.get("created_at"))
            }
        }
        
        # Send POST request to n8n webhook
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "UniWeb-Platform/1.0"
            },
            timeout=10  # 10 second timeout
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        logger.info(f"Successfully sent lecture webhook for {action} action. Lecture ID: {lecture_item.get('id')}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send lecture webhook: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending lecture webhook: {e}")
        return False

def test_webhook_connection():
    """
    Test the webhook connection by sending a test payload
    
    Returns:
        bool: True if connection test was successful, False otherwise
    """
    try:
        test_payload = {
            "event_type": "connection_test",
            "action": "test",
            "timestamp": datetime.now().isoformat(),
            "message": "Testing webhook connection from UniWeb Platform"
        }
        
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=test_payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "UniWeb-Platform/1.0"
            },
            timeout=10
        )
        
        response.raise_for_status()
        logger.info("Webhook connection test successful")
        return True
        
    except Exception as e:
        logger.error(f"Webhook connection test failed: {e}")
        return False


def send_assignment_webhook(assignment_data, assignment_type, action="created"):
    """
    Send assignment/project/presentation data to n8n webhook
    
    Args:
        assignment_data (dict): The assignment data
        assignment_type (str): 'weekly_homework', 'final_projects', or 'presentations'
        action (str): The action performed ("created", "updated", "deleted")
    
    Returns:
        bool: True if webhook was sent successfully, False otherwise
    """
    try:
        # Determine type category and labels
        type_categories = {
            "weekly_homework": {
                "category": "homework",
                "label": "📚 Weekly Homework",
                "icon": "📝"
            },
            "final_projects": {
                "category": "project", 
                "label": "🎯 Final Project",
                "icon": "📊"
            },
            "presentations": {
                "category": "presentation",
                "label": "🎤 Presentation",
                "icon": "📽️"
            }
        }
        
        type_info = type_categories.get(assignment_type, {
            "category": "unknown",
            "label": "Unknown Type",
            "icon": "❓"
        })
        
        # Get degree/points value
        degree = assignment_data.get("degree") or assignment_data.get("points") or assignment_data.get("max_points") or 10
        
        # Prepare professional webhook payload - TYPE FIRST
        payload = {
            # === TYPE INFORMATION (FIRST) ===
            "type": {
                "category": type_info["category"],
                "label": type_info["label"],
                "icon": type_info["icon"],
                "raw_type": assignment_type,
                "is_homework": assignment_type == "weekly_homework",
                "is_project": assignment_type == "final_projects",
                "is_presentation": assignment_type == "presentations"
            },
            
            # === EVENT METADATA ===
            "event": {
                "type": "assignment_update",
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "platform": "University AI Batch Platform"
            },
            
            # === ASSIGNMENT DETAILS ===
            "assignment": {
                "id": assignment_data.get("id"),
                "title": assignment_data.get("title"),
                "description": assignment_data.get("description"),
                "degree": degree,
                "max_file_size_mb": assignment_data.get("max_file_size_mb", 5)
            },
            
            # === SUBJECT INFORMATION ===
            "subject": {
                "id": assignment_data.get("subject_id"),
                "name": assignment_data.get("subject_name")
            },
            
            # === SCHEDULE ===
            "schedule": {
                "due_date": assignment_data.get("due_date"),
                "week": assignment_data.get("week"),
                "created_at": assignment_data.get("created_at"),
                "created_by": assignment_data.get("created_by", "admin")
            },
            
            # === SUMMARY (Human-readable) ===
            "summary": f"{type_info['icon']} New {type_info['label'].split(' ', 1)[1]}: {assignment_data.get('title')} | Subject: {assignment_data.get('subject_name')} | Degree: {degree} points | Due: {assignment_data.get('due_date')}"
        }
        
        # Send POST request to n8n assignment webhook
        response = requests.post(
            N8N_ASSIGNMENT_WEBHOOK_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "UniWeb-Platform/1.0"
            },
            timeout=10  # 10 second timeout
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        logger.info(f"Successfully sent assignment webhook for {action} action. Type: {type_info['label']}, ID: {assignment_data.get('id')}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send assignment webhook: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending assignment webhook: {e}")
        return False
