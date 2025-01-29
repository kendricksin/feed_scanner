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
        
    def __del__(self):
        """Cleanup database connection"""
        if hasattr(self, 'db'):
            self.db.__exit__(None, None, None)

    def get_by_project_id(self, project_id: str) -> Optional[Announcement]:
        """Get announcement by project ID"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM announcements WHERE project_id = ?",
            (project_id,)
        )
        row = cursor.fetchone()
        return Announcement.from_dict(dict(row)) if row else None

    def get_pending_processing(self):
        """Get announcements that need document processing"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM announcements 
            WHERE (doc_path IS NULL OR doc_path = '')
            AND status = 'pending'
            ORDER BY created_at DESC
        """)
        return cursor.fetchall()

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

    def update(self, announcement):
        """Update announcement record"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE announcements 
            SET 
                doc_info = ?,
                zip_id = ?,
                doc_path = ?,
                doc_updated_at = ?,
                updated_at = ?
            WHERE project_id = ?
        """, (
            announcement.doc_info,
            announcement.zip_id,
            announcement.doc_path,
            announcement.doc_updated_at,
            datetime.now(),
            announcement.project_id
        ))
        self.conn.commit()