from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict
from src.core.constants import Status

@dataclass
class Announcement:
    """Announcement model"""
    project_id: str
    title: str
    link: str
    description: str
    dept_id: Optional[str] = None
    status: Status = Status.PENDING
    pdf_path: Optional[str] = None
    budget_amount: Optional[float] = None
    quantity: Optional[int] = None
    duration_years: Optional[int] = None
    duration_months: Optional[int] = None
    submission_date: Optional[datetime] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    id: Optional[int] = None

    def __post_init__(self):
        """Set default values after initialization"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        
        # Ensure status is always a Status enum
        if isinstance(self.status, str):
            self.status = Status(self.status)
        
    def update(self, **kwargs):
        """Update announcement attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                # Handle special cases
                if key == 'status' and isinstance(value, str):
                    value = Status(value)
                elif key in ['submission_date', 'created_at', 'updated_at'] and isinstance(value, str):
                    value = datetime.fromisoformat(value)
                
                setattr(self, key, value)
        self.updated_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'Announcement':
        """Create announcement from dictionary"""
        # Convert string dates to datetime objects
        date_fields = ['submission_date', 'created_at', 'updated_at']
        for field in date_fields:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                except ValueError:
                    data[field] = None

        # Convert status string to enum
        if 'status' in data and isinstance(data['status'], str):
            try:
                data['status'] = Status(data['status'])
            except ValueError:
                data['status'] = Status.PENDING

        # Filter only valid fields and create instance
        valid_data = {
            k: v for k, v in data.items() 
            if k in cls.__annotations__
        }
        
        return cls(**valid_data)

    def to_dict(self) -> dict:
        """Convert announcement to dictionary"""
        data = {
            'id': self.id,
            'project_id': self.project_id,
            'title': self.title,
            'link': self.link,
            'description': self.description,
            'dept_id': self.dept_id,
            'status': self.status.value,  # Convert enum to string
            'pdf_path': self.pdf_path,
            'budget_amount': self.budget_amount,
            'quantity': self.quantity,
            'duration_years': self.duration_years,
            'duration_months': self.duration_months,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Remove None values for cleaner output
        return {k: v for k, v in data.items() if v is not None}