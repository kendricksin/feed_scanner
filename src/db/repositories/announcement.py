# src/db/repositories/announcement.py

from typing import List, Optional
from datetime import datetime, timedelta
from .base import BaseRepository
from ..models.announcement import Announcement
from src.core.constants import Status

class AnnouncementRepository(BaseRepository[Announcement]):
    def __init__(self):
        super().__init__(Announcement)
        self.table_name = "announcements"
    
    def get_by_project_id(self, project_id: str) -> Optional[Announcement]:
        """Get announcement by project ID"""
        results = self.find_by(project_id=project_id)
        return results[0] if results else None
    
    def get_recent_by_dept(self, dept_id: str, limit: int = 10) -> List[Announcement]:
        """Get recent announcements for department"""
        query = """
            SELECT * FROM announcements 
            WHERE dept_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """
        cursor = self._execute_query(query, (dept_id, limit))
        return [Announcement.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def get_pending_processing(self) -> List[Announcement]:
        """Get announcements pending PDF processing"""
        query = """
            SELECT * FROM announcements 
            WHERE status = ? 
            ORDER BY created_at ASC
        """
        cursor = self._execute_query(query, (Status.PENDING,))
        return [Announcement.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def upsert(self, announcement: Announcement) -> Optional[Announcement]:
        """Insert or update announcement"""
        existing = self.get_by_project_id(announcement.project_id)
        
        if existing:
            # Update existing announcement
            announcement.id = existing.id
            announcement.created_at = existing.created_at  # Preserve original creation date
            return self.update(announcement)
        else:
            # Create new announcement
            return self.create(announcement)
    
    def update_status(self, id: int, status: Status) -> bool:
        """Update announcement status"""
        query = """
            UPDATE announcements 
            SET status = ?, updated_at = ? 
            WHERE id = ?
        """
        cursor = self._execute_query(query, (status, datetime.now(), id))
        return cursor.rowcount > 0
    
    def get_statistics(self, days: int = 7) -> dict:
        """Get announcement statistics"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as processing,
                SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as failed,
                COUNT(DISTINCT dept_id) as departments
            FROM announcements
            WHERE created_at >= ?
        """
        
        cursor = self._execute_query(query, (
            Status.PENDING,
            Status.PROCESSING,
            Status.COMPLETED,
            Status.FAILED,
            cutoff_date
        ))
        
        return dict(cursor.fetchone())