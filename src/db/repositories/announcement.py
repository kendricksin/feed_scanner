# src/db/repositories/announcement.py

import sqlite3
import asyncio
from typing import Optional, List, Dict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from src.core.logging import get_logger
from src.core.config import config
from src.core.constants import Status
from src.db.models.announcement import Announcement

logger = get_logger(__name__)

class AnnouncementRepository:
    """Repository for working with announcements"""
    
    def __init__(self):
        self.conn = None
        self.logger = get_logger(self.__class__.__name__)
        self._lock = asyncio.Lock()

    async def connect(self):
        """Establish database connection"""
        if not self.conn:
            self.conn = sqlite3.connect(config.db_path)
            self.conn.row_factory = sqlite3.Row

    async def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self._lock.acquire()
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        try:
            if exc_type is None:
                if self.conn:
                    self.conn.commit()
            else:
                if self.conn:
                    self.conn.rollback()
        finally:
            await self.disconnect()
            self._lock.release()

    async def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL query"""
        if not self.conn:
            await self.connect()

        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor
        except Exception as e:
            self.logger.error(f"Query execution error: {e}")
            self.logger.error(f"Query: {query}")
            self.logger.error(f"Params: {params}")
            raise

    async def get_by_project_id(self, project_id: str) -> Optional[Announcement]:
        """Get announcement by project ID"""
        cursor = await self.execute_query(
            "SELECT * FROM announcements WHERE project_id = ?", 
            (project_id,)
        )
        row = cursor.fetchone()
        return Announcement.from_dict(dict(row)) if row else None

    async def get_pending_processing(self) -> List[Announcement]:
        """Get announcements pending processing"""
        cursor = await self.execute_query("""
            SELECT * FROM announcements 
            WHERE status = ? 
            ORDER BY created_at DESC
        """, (Status.PENDING,))
        
        return [
            Announcement.from_dict(dict(row))
            for row in cursor.fetchall()
        ]

    async def upsert(self, announcement: Announcement) -> Optional[Announcement]:
        """Insert or update announcement"""
        data = announcement.to_dict()
        now = datetime.now()
        
        if 'id' in data:
            del data['id']
        
        cursor = await self.execute_query("""
            INSERT INTO announcements (
                project_id, dept_id, title, link, description,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET
                title = excluded.title,
                link = excluded.link,
                description = excluded.description,
                status = excluded.status,
                updated_at = ?
        """, (
            data['project_id'],
            data.get('dept_id'),
            data.get('title'),
            data.get('link'),
            data.get('description'),
            data.get('status', Status.PENDING),
            now,
            now,
            now
        ))
        self.conn.commit()  # Commit after upsert
        return await self.get_by_project_id(announcement.project_id)

    async def update(self, announcement: Announcement) -> Optional[Announcement]:
        """Update announcement"""
        data = announcement.to_dict()
        if 'id' not in data:
            raise ValueError("Cannot update announcement without ID")
            
        id_value = data.pop('id')
        if 'created_at' in data:
            del data['created_at']
            
        data['updated_at'] = datetime.now()
        
        set_clause = ', '.join(f"{k} = ?" for k in data.keys())
        query = f"UPDATE announcements SET {set_clause} WHERE id = ?"
        
        values = list(data.values()) + [id_value]
        await self.execute_query(query, tuple(values))
        self.conn.commit()  # Commit after update
        return await self.get_by_project_id(data['project_id'])

    async def update_status(self, announcement_id: int, status: Status):
        """Update announcement status"""
        await self.execute_query("""
            UPDATE announcements
            SET status = ?,
                updated_at = ?
            WHERE id = ?
        """, (status, datetime.now(), announcement_id))
        self.conn.commit()  # Commit after status update

    async def get_statistics(self, days: int = 7) -> Dict:
        """Get announcement statistics"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cursor = await self.execute_query("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = ? THEN 1 END) as pending,
                COUNT(CASE WHEN status = ? THEN 1 END) as completed,
                COUNT(CASE WHEN status = ? THEN 1 END) as failed
            FROM announcements
            WHERE created_at >= ?
        """, (Status.PENDING, Status.COMPLETED, Status.FAILED, cutoff_date))
        
        return dict(cursor.fetchone())