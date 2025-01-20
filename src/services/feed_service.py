# src/services/feed_service.py

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.db.repositories.announcement import AnnouncementRepository
from src.core.logging import get_logger
from src.core.constants import Status, DEPARTMENTS

logger = get_logger(__name__)

class FeedService:
    def __init__(self):
        self.repository = AnnouncementRepository()
    
    async def get_announcements(
        self,
        dept_id: Optional[str] = None,
        status: Optional[Status] = None,
        days: int = 7,
        limit: int = 50
    ) -> List[Dict]:
        """Get recent announcements with filters"""
        try:
            announcements = self.repository.find_by(dept_id=dept_id) if dept_id \
                else self.repository.get_all()
            
            # Filter by status if provided
            if status:
                announcements = [a for a in announcements if a.status == status]
            
            # Filter by date
            cutoff_date = datetime.now() - timedelta(days=days)
            announcements = [
                a for a in announcements 
                if a.created_at and a.created_at >= cutoff_date
            ]
            
            # Sort by created_at descending and limit
            announcements.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
            announcements = announcements[:limit]
            
            return [ann.to_dict() for ann in announcements]
            
        except Exception as e:
            logger.error(f"Error getting announcements: {e}")
            raise
    
    async def get_statistics(self, days: int = 7) -> Dict:
        """Get announcement statistics"""
        try:
            stats = self.repository.get_statistics(days)
            
            # Add department breakdown
            dept_stats = {}
            for dept_id in DEPARTMENTS:
                dept_announcements = self.repository.find_by(dept_id=dept_id)
                dept_stats[dept_id] = {
                    "total": len(dept_announcements),
                    "pending": len([a for a in dept_announcements if a.status == Status.PENDING]),
                    "completed": len([a for a in dept_announcements if a.status == Status.COMPLETED]),
                    "failed": len([a for a in dept_announcements if a.status == Status.FAILED])
                }
            
            stats["departments"] = dept_stats
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise
    
    async def get_announcement_details(self, project_id: str) -> Optional[Dict]:
        """Get detailed announcement information"""
        try:
            announcement = self.repository.get_by_project_id(project_id)
            return announcement.to_dict() if announcement else None
            
        except Exception as e:
            logger.error(f"Error getting announcement details: {e}")
            raise