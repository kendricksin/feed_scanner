from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any

@dataclass
class BaseModel:
    """Base model class with common functionality"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create model instance from dictionary"""
        # Filter out keys that aren't in the dataclass
        valid_fields = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    def update(self, **kwargs):
        """Update model attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                
    @property
    def created_at_formatted(self) -> str:
        """Return formatted created_at date"""
        if hasattr(self, 'created_at') and self.created_at:
            return self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return ''

    @property
    def updated_at_formatted(self) -> str:
        """Return formatted updated_at date"""
        if hasattr(self, 'updated_at') and self.updated_at:
            return self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        return ''