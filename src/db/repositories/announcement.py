# src/db/repositories/announcement.py

from typing import List, Optional, Dict
from datetime import datetime, timedelta
import sqlite3
from .base import BaseRepository
from ..models.announcement import Announcement
from src.core.constants import Status
from src.core.logging import get_logger

logger = get_logger(__name__)

class AnnouncementRepository(BaseRepository[Announcement]):
    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        super().__init__(Announcement)
        self.table_name = "announcements"
        self.conn = conn
        
    def get_by_project_id(self, project_id: str) -> Optional[Announcement]:
        """Get announcement by project ID"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM announcements WHERE project_id = ?",
            (project_id,)
        )
        row = cursor.fetchone()
        return Announcement.from_dict(dict(row)) if row else None
    
    def upsert(self, announcement: Announcement) -> Optional[Announcement]:
        """Insert or update announcement"""
        cursor = self.conn.cursor()
        try:
            # Check if announcement exists
            cursor.execute(
                "SELECT id FROM announcements WHERE project_id = ?",
                (announcement.project_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing announcement
                data = announcement.to_dict()
                if 'id' in data:
                    del data['id']
                if 'created_at' in data:
                    del data['created_at']
                
                set_clause = ', '.join(f"{k} = ?" for k in data.keys())
                values = list(data.values()) + [announcement.project_id]
                
                cursor.execute(
                    f"""
                    UPDATE announcements 
                    SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                    WHERE project_id = ?
                    """,
                    tuple(values)
                )
            else:
                # Insert new announcement
                data = announcement.to_dict()
                if 'id' in data:
                    del data['id']
                
                columns = ', '.join(data.keys())
                placeholders = ', '.join('?' * len(data))
                
                cursor.execute(
                    f"""
                    INSERT INTO announcements ({columns})
                    VALUES ({placeholders})
                    """,
                    tuple(data.values())
                )
            
            self.conn.commit()
            return self.get_by_project_id(announcement.project_id)
            
        except Exception as e:
            logger.error(f"Error in upsert: {e}")
            self.conn.rollback()
            raise