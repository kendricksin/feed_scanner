# src/core/constants.py

from enum import Enum
from typing import Dict, List

# Department configurations
DEPARTMENTS = {
    "0307": {
        "name": "Revenue Department",
        "sub_departments": ["0307"]  # Add sub-department codes if needed
    },
    # Add more departments as needed
}

class Status(str, Enum):
    """Pipeline status values"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    
class ProcurementMethod(str, Enum):
    """Procurement method codes"""
    E_BIDDING = "16"
    E_MARKET = "15"
    SPECIAL = "17"
    
class AnnouncementType(str, Enum):
    """Announcement type codes"""
    PROCUREMENT_PLAN = "P0"
    INVITATION = "D1"
    WINNER = "D3"
    CONTRACT = "D4"

# Feed configuration
FEED_PARAMS = {
    "dept_id": "deptId",
    "dept_sub_id": "deptsubId",
    "method_id": "methodId",
    "announce_type": "anounceType",
    "announce_date": "announceDate",
    "count_by_day": "countbyday"
}

# Time windows when the feed is typically available
FEED_TIME_WINDOWS = [
    {"start": "00:00", "end": "08:59"},
    {"start": "12:01", "end": "12:59"},
    {"start": "17:01", "end": "23:59"}
]

# Database table names
class Tables(str, Enum):
    """Database table names"""
    ANNOUNCEMENTS = "announcements"
    DOWNLOADS = "downloads"
    
# PDF processing timeouts
PDF_DOWNLOAD_TIMEOUT = 30  # seconds
PDF_PROCESSING_TIMEOUT = 60  # seconds

# Error messages
ERROR_MESSAGES = {
    "feed_unavailable": "Feed is currently unavailable. Please try during available time windows.",
    "invalid_department": "Invalid department ID provided.",
    "pdf_download_failed": "Failed to download PDF file.",
    "pdf_processing_failed": "Failed to process PDF file.",
    "database_error": "Database operation failed."
}

# Success messages
SUCCESS_MESSAGES = {
    "feed_processed": "Successfully processed feed data.",
    "pdf_downloaded": "Successfully downloaded PDF file.",
    "pdf_processed": "Successfully processed PDF file.",
    "pipeline_completed": "Pipeline execution completed successfully."
}