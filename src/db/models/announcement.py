from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from .base import BaseModel

@dataclass
class Announcement(BaseModel):
    id: Optional[int] = None
    project_id: str = None
    title: str = None
    link: str = None
    description: str = None
    dept_id: str = None
    status: str = "pending"
    
    # Procurement details
    budget_amount: Optional[float] = None
    quantity: Optional[int] = None
    duration_years: Optional[int] = None
    duration_months: Optional[int] = None
    submission_date: Optional[datetime] = None
    submission_time: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    
    # File details
    pdf_path: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Set default dates if not provided"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()