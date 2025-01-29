from datetime import datetime
from typing import Optional
from dataclasses import dataclass
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
    doc_info: Optional[str] = None
    zip_id: Optional[str] = None
    doc_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    doc_updated_at: Optional[datetime] = None
    id: Optional[int] = None

    def __post_init__(self):
        """Set default values after initialization"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        
    def update(self, **kwargs):
        """Update announcement attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'Announcement':
        """Create announcement from dictionary"""
        return cls(**{
            k: v for k, v in data.items() 
            if k in cls.__annotations__
        })

    def to_dict(self) -> dict:
        """Convert announcement to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'title': self.title,
            'link': self.link,
            'description': self.description,
            'dept_id': self.dept_id,
            'status': self.status,
            'doc_info': self.doc_info,
            'zip_id': self.zip_id,
            'doc_path': self.doc_path,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'doc_updated_at': self.doc_updated_at
        }